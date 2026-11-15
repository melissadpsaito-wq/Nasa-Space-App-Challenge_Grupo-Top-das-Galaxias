"""2.2 Grade comum + H3 (Guia 48h v2 §2.2). Dono: Murilo.

Passo 1 — "peneira": 1 linha por célula de 0,02° por passagem (passagem = sensor + ts + daynight, conferido
pelo check_method: Brasil 2025 → 3,45). FRP da célula = máximo (D26) e soma (frp_sum, D29 ajustada).
Passo 2 — "bairro": cada célula de 0,02° recebe a célula H3 res 4 do seu centro (D04); agregado mensal.

Saídas (em --out):
  grid2km_pass.parquet  sensor, ts, daynight, gy, gx, cell, ym, frp_max, frp_sum, n_pix, pix_area   (DATA_DICTIONARY §5)
  agg_monthly.parquet   sensor, cell, ym, n, frp_mean, frp_p90, night_frac, pix_area, frp_sum         (DATA_DICTIONARY §2)

Uso (raiz do repo):
  python -m pipeline.grid --area pantanal      # data/clean_pantanal → data/interim/pantanal/
  python -m pipeline.grid --area brasil        # data/clean → data/interim/ (caminhos do sensors.yaml)
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import duckdb
import h3
import pandas as pd

AREAS = {"pantanal": ("data/clean_pantanal", "data/interim/pantanal"), "brasil": ("data/clean", "data/interim")}
GRID_DEG = 0.02     # D13 · config/sensors.yaml grid.pass_cell_deg
H3_RES = 4          # D04 · config/sensors.yaml grid.h3_res


def _p(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def build(clean: Path, out: Path, years: list[int] | None = None, g: float = GRID_DEG, res: int = H3_RES,
          con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    """Gera grid2km_pass e agg_monthly. Devolve o resumo por sensor × ano (linhas em cada etapa)."""
    con = con or duckdb.connect()
    out.mkdir(parents=True, exist_ok=True)
    where = f"WHERE year(ts) IN ({', '.join(map(str, years))})" if years else ""
    con.sql(f"CREATE OR REPLACE TEMP VIEW clean AS SELECT * FROM read_parquet('{_p(clean)}/*/*.parquet') {where}")

    # Passo 1: peneira de 0,02° por passagem
    con.sql(f"""CREATE OR REPLACE TEMP TABLE gp AS
        SELECT sensor, ts, daynight,
               CAST(floor(latitude / {g}) AS INTEGER) AS gy, CAST(floor(longitude / {g}) AS INTEGER) AS gx,
               max(frp) AS frp_max, sum(frp) AS frp_sum, count(*) AS n_pix, avg(pixel_area) AS pix_area
        FROM clean GROUP BY ALL""")

    # Passo 2: célula H3 do centro de cada célula de 0,02° (só as distintas: rápido mesmo no Brasil)
    u = con.sql("SELECT DISTINCT gy, gx FROM gp").df()
    u["cell"] = [h3.latlng_to_cell((y + 0.5) * g, (x + 0.5) * g, res) for y, x in zip(u.gy, u.gx)]
    con.register("u_df", u)
    con.sql("""CREATE OR REPLACE TEMP TABLE pass AS
        SELECT gp.sensor, gp.ts, gp.daynight, gp.gy, gp.gx, u_df.cell,
               CAST(year(gp.ts) * 100 + month(gp.ts) AS INTEGER) AS ym,
               gp.frp_max, gp.frp_sum, gp.n_pix, gp.pix_area
        FROM gp JOIN u_df USING (gy, gx)""")
    con.sql(f"""COPY (SELECT * FROM pass ORDER BY sensor, ym, ts)
                TO '{_p(out / "grid2km_pass.parquet")}' (FORMAT parquet, COMPRESSION zstd)""")

    con.sql(f"""COPY (
        SELECT sensor, cell, ym,
               count(*)                                   AS n,
               avg(frp_max)                               AS frp_mean,
               quantile_cont(frp_max, 0.9)                AS frp_p90,
               avg(CASE WHEN daynight = 'N' THEN 1.0 ELSE 0.0 END) AS night_frac,
               avg(pix_area)                              AS pix_area,
               sum(frp_sum)                               AS frp_sum
        FROM pass GROUP BY ALL ORDER BY sensor, cell, ym)
        TO '{_p(out / "agg_monthly.parquet")}' (FORMAT parquet, COMPRESSION zstd)""")

    # Conservação: pixels = focos limpos; Σn do agregado = linhas da grade
    s = con.sql(f"""
        WITH c AS (SELECT sensor, year(ts) AS year, count(*) AS clean_rows FROM clean GROUP BY ALL),
             p AS (SELECT sensor, ym // 100 AS year, count(*) AS pass_cells, sum(n_pix) AS pixels FROM pass GROUP BY ALL),
             a AS (SELECT sensor, ym // 100 AS year, sum(n) AS agg_n, count(DISTINCT cell) AS h3_cells
                   FROM read_parquet('{_p(out / "agg_monthly.parquet")}') GROUP BY ALL)
        SELECT c.sensor, c.year, clean_rows, pass_cells, pixels, agg_n, h3_cells
        FROM c JOIN p USING (sensor, year) JOIN a USING (sensor, year) ORDER BY c.sensor, c.year""").df()
    assert (s.pixels == s.clean_rows).all(), "pixels da grade ≠ focos limpos"
    assert (s.agg_n == s.pass_cells).all(), "Σn do agg_monthly ≠ linhas da grade"
    s["pixels_per_cell"] = s.clean_rows / s.pass_cells
    return s


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Grade 0,02° por passagem + H3 res 4 → grid2km_pass e agg_monthly.")
    ap.add_argument("--area", choices=AREAS, default="brasil")
    ap.add_argument("--clean", help="pasta de focos limpos (padrão pela área)")
    ap.add_argument("--out", help="pasta de saída (padrão pela área)")
    ap.add_argument("--years", help="ex.: 2025 ou 2012-2019")
    a = ap.parse_args(argv)
    clean, out = (Path(x) for x in AREAS[a.area])
    clean, out = Path(a.clean or clean), Path(a.out or out)
    years = None
    if a.years:
        lo, _, hi = a.years.partition("-")
        years = list(range(int(lo), int(hi or lo) + 1))

    t0 = time.time()
    s = build(clean, out, years)
    pd.set_option("display.width", 160)
    print(f"{clean} → {out} · {time.time() - t0:.0f} s · conservação OK\n")
    print(s.to_string(index=False))
    tot = s.groupby("sensor")[["clean_rows", "pass_cells"]].sum()
    tot["pixels_per_cell"] = tot.clean_rows / tot.pass_cells
    print("\nTotal por sensor:\n" + tot.round(2).to_string())
    w = s.pivot(index="year", columns="sensor", values="pass_cells")
    if {"AQUA", "SNPP"} <= set(w.columns):
        r = (w.SNPP / w.AQUA).dropna()
        print("\nS-NPP/Aqua na grade 0,02° por ano:\n" + r.round(2).to_string())
    s.to_csv(out / "grid_log.csv", index=False)


if __name__ == "__main__":
    main()

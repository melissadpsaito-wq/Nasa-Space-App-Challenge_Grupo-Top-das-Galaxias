"""D40 — Harmonização do ΣFRP mensal com a mesma ponte M1 da contagem (sem alterar o M1).

Ideia: o M1 só lê `n` do agg_monthly (CONTRATO-CIENCIA §2). Gravamos um agg em que
    n = frp_sum / s      (s = MW por "unidade", fixo)
rodamos o pipeline existente (m1 --eval para validar, harmonize para a série) e multiplicamos de volta por s.
Escala s = ΣFRP do S-NPP ÷ Σn do S-NPP (MW por detecção na grade, Brasil, 2012–2025), para que
λ = 20 continue valendo "≈ 20 detecções" de encolhimento. Resultado em ΣFRP na escala S-NPP.

Passos (raiz do repo):
  1) python -m pipeline.frp_harmonize prep
  2) python -m pipeline.bridges.m1 --eval --fast --agg data/interim/res5_frp/agg_monthly.parquet
  3) python -m pipeline.bridges.harmonize --lam 20 --agg data/interim/res5_frp/agg_monthly.parquet --out data/processed/res5_frp/harm_series.parquet
  4) python -m pipeline.frp_harmonize csv
Saída final: data/processed/res5_frp/frp_harm_nonzero.csv  →  cell, lat, lon, year, month, frp
Variantes do passo 4:
  csv --with-zeros --gzip                          todo hexágono COM FOGO × todo mês (zeros incluídos)
  csv --brazil data/raw/br_pais.geojson --gzip     TODOS os hexágonos res 5 do Brasil × todo mês (D42, treino)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

AGG_IN = "data/interim/res5/agg_monthly.parquet"
AGG_OUT = "data/interim/res5_frp/agg_monthly.parquet"
HARM = "data/processed/res5_frp/harm_series.parquet"
CSV = "data/processed/res5_frp/frp_harm_nonzero.csv"
META = "data/interim/res5_frp/scale.json"
REF = "SNPP"


def scale_of(agg: pd.DataFrame, ref: str = REF) -> float:
    r = agg[agg.sensor == ref]
    return float(r.frp_sum.sum() / r.n.sum())


def prep(agg: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    s = scale_of(agg)
    out = agg.copy()
    out["n_count"] = out["n"]                  # contagem original preservada (não usada pelo M1)
    out["n"] = (out["frp_sum"].fillna(0) / s).astype(float)
    return out, s


def month_range(start: int = 200011, end: int = 202512) -> list[int]:
    y, m, out = start // 100, start % 100, []
    while y * 100 + m <= end:
        out.append(y * 100 + m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def brazil_cells(geojson_path: str, res: int = 5) -> set[str]:
    """Todos os hexágonos H3 cujo centro está dentro do contorno (GeoJSON do IBGE, Polygon/MultiPolygon)."""
    import h3
    geo = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    feats = geo["features"] if geo.get("type") == "FeatureCollection" else [geo]
    cells: set[str] = set()
    for f in feats:
        g = f.get("geometry", f)
        cells |= set(h3.geo_to_cells(g, res))      # GeoJSON [lon, lat]; MultiPolygon aceito
    return cells


def full_grid(harm: pd.DataFrame, extra_cells: set[str] | None = None) -> pd.DataFrame:
    """Todo hexágono × todo mês (nov/2000–dez/2025); hexágono-mês ausente entra com n_harm = 0.
    extra_cells: hexágonos do Brasil sem nenhum foco (entram com zero em todos os meses)."""
    fire = set(harm.cell.unique())
    cells = sorted(fire | (extra_cells or set()))
    if extra_cells:
        print(f"  hexágonos: {len(fire):,} com fogo + {len(set(extra_cells) - fire):,} do contorno sem fogo "
              f"= {len(cells):,} ({len(fire - set(extra_cells)):,} com fogo têm centro fora do contorno e foram mantidos)")
    idx = pd.MultiIndex.from_product([cells, month_range()], names=["cell", "ym"])
    h = harm.set_index(["cell", "ym"])[["n_harm"]]
    h = h[~h.index.duplicated()].reindex(idx)
    added = int(h.n_harm.isna().sum())
    h["n_harm"] = h.n_harm.fillna(0.0)
    print(f"  grade completa: {len(h):,} linhas ({len(cells):,} hexágonos × 302 meses); "
          f"{added:,} hexágono-mês ausentes preenchidos com 0")
    return h.reset_index()


def to_csv_frame(harm: pd.DataFrame, s: float, min_mw: float = 0.0, with_zeros: bool = False,
                 extra_cells: set[str] | None = None) -> pd.DataFrame:
    h = full_grid(harm, extra_cells) if with_zeros else harm.copy()
    h["frp"] = (h.n_harm.astype(float) * s).round(2)
    if with_zeros:
        h.loc[h.frp <= min_mw, "frp"] = 0.0      # abaixo do limiar vira zero, mas a linha fica
    else:
        h = h[h.frp > min_mw]
    h["year"], h["month"] = h.ym // 100, h.ym % 100
    cells = h.cell.unique()
    try:
        import h3
        ll = {c: h3.cell_to_latlng(c) for c in cells}
        h["lat"] = h.cell.map(lambda c: round(ll[c][0], 4))
        h["lon"] = h.cell.map(lambda c: round(ll[c][1], 4))
    except ImportError:
        h["lat"] = h["lon"] = np.nan
    return h[["cell", "lat", "lon", "year", "month", "frp"]].sort_values(
        ["cell", "year", "month"], kind="stable").reset_index(drop=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="D40 — ΣFRP harmonizado via M1")
    ap.add_argument("step", choices=["prep", "csv"])
    ap.add_argument("--agg", default=AGG_IN)
    ap.add_argument("--harm", default=HARM)
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-mw", type=float, default=0.0,
                    help="descarta meses com FRP harmonizado ≤ este valor (padrão 0 = só remove zeros)")
    ap.add_argument("--with-zeros", action="store_true",
                    help="tabela completa: todo hexágono × todo mês, FRP = 0 onde não houve fogo")
    ap.add_argument("--gzip", action="store_true", help="grava .csv.gz")
    ap.add_argument("--brazil", default=None,
                    help="GeoJSON do contorno do Brasil (IBGE): inclui TODOS os hexágonos res 5 do país (D42)")
    args = ap.parse_args(argv)
    if args.brazil:
        args.with_zeros = True

    if args.step == "prep":
        agg = pd.read_parquet(args.agg)
        out, s = prep(agg)
        p = Path(args.out or AGG_OUT)
        p.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(p, index=False)
        Path(META).write_text(json.dumps({"scale_mw": s, "ref": REF, "source": args.agg}, indent=1))
        tot = out.groupby("sensor").frp_sum.sum()
        print(f"escala s = {s:.3f} MW por unidade ({REF}) · gravado {p} ({len(out):,} linhas)")
        print("  ΣFRP por sensor (MW): " + " · ".join(f"{k} {v:,.0f}" for k, v in tot.items()))
        return

    s = json.loads(Path(META).read_text())["scale_mw"]
    harm = pd.read_parquet(args.harm)
    extra = brazil_cells(args.brazil) if args.brazil else None
    d = to_csv_frame(harm, s, args.min_mw, args.with_zeros, extra)
    raw_mw = float((harm.n_raw.astype(float) * s).sum())
    default = (CSV.replace("_nonzero", "_brasil") if args.brazil
               else CSV.replace("_nonzero", "_full") if args.with_zeros else CSV)
    p = Path(args.out or default + (".gz" if args.gzip else ""))
    p.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(p, index=False, compression="gzip" if args.gzip else None)
    if args.with_zeros:
        print(f"  linhas com frp = 0: {(d.frp == 0).sum():,}")
    only_add = int(((harm.n_harm > 0) & (harm.n_raw.fillna(0) == 0)).sum())
    print(f"gravado {p} · {len(d):,} linhas · {d.cell.nunique():,} hexágonos · "
          f"Σ FRP harmonizado {d.frp.sum():,.0f} MW (bruto da linha do tempo {raw_mw:,.0f} MW)")
    print(f"  {only_add:,} hexágono-mês só com termo aditivo (fogo fraco estimado onde o MODIS não viu; "
          f"use --min-mw para cortar)")
    if len(d) > 1_048_576:
        print("  aviso: mais de 1.048.576 linhas — o Excel não abre inteiro")


if __name__ == "__main__":
    main()

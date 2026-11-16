"""Auditoria: valores DIÁRIOS por hexágono res 5 e conferência com o mensal (frp_monthly).

Diário (sensor × cell × date, UTC) a partir de data/interim/grid2km_pass.parquet, pelo mesmo caminho do grid.py:
  quadrado 0,02° (gy, gx) → centro ((g + 0,5) · 0,02) → h3.latlng_to_cell(lat, lon, 5)
  n       = nº de quadrados 0,02° × passagem com fogo no dia      (soma do mês = n_<SENSOR>)
  n_pix   = nº de pixels (focos limpos) no dia
  frp_sum = Σ FRP de todos os pixels no dia (MW)                   (soma do mês = frp_sum_<SENSOR>)

Conferência: Σ diário por mês × frp_monthly.parquet (n_<S>, frp_sum_<S>), célula a célula.

Uso (raiz do repo):
  python -m pipeline.audit_daily                                     # diário completo + conferência
  python -m pipeline.audit_daily --csv --cell 85a8... --year 2020    # CSV de um hexágono/ano para olhar no Excel
  python -m pipeline.audit_daily --csv --lat -17.8 --lon -56.4       # hexágono que contém o ponto
Saídas (data/processed/res5/, fora do Git): audit_daily.parquet · audit_report.csv · audit_mismatch.csv · [audit_daily_<filtro>.csv]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

GRID = "data/interim/grid2km_pass.parquet"
MONTHLY = "data/processed/res5/frp_monthly.parquet"
OUTDIR = "data/processed/res5"
SENSORS = ["TERRA", "AQUA", "SNPP", "N20"]
STEP = 0.02
RES = 5
YM_START, YM_END = 200011, 202512


def h3_cell_fn(res: int = RES):
    import h3
    return lambda lat, lon: h3.latlng_to_cell(lat, lon, res)


def daily(grid: pd.DataFrame, cell_fn) -> pd.DataFrame:
    """grid2km_pass → sensor × cell × date."""
    g = grid
    sq = g[["gy", "gx"]].drop_duplicates()
    sq["cell5"] = [cell_fn((y + 0.5) * STEP, (x + 0.5) * STEP) for y, x in zip(sq.gy, sq.gx)]
    g = g.merge(sq, on=["gy", "gx"], how="left")
    ts = pd.to_datetime(g.ts, utc=True)
    g["date"] = ts.dt.strftime("%Y-%m-%d")
    g["ym"] = ts.dt.year * 100 + ts.dt.month
    d = (g.groupby(["sensor", "cell5", "date", "ym"], as_index=False)
          .agg(n=("gy", "size"), n_pix=("n_pix", "sum"), frp_sum=("frp_sum", "sum"))
          .rename(columns={"cell5": "cell"}))
    d = d[(d.ym >= YM_START) & (d.ym <= YM_END)]
    d["frp_sum"] = d.frp_sum.astype(float).round(3)
    return d.sort_values(["cell", "date", "sensor"], kind="stable").reset_index(drop=True)


def compare(d: pd.DataFrame, monthly: pd.DataFrame, tol_frp: float = 0.05) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Σ diário por mês × mensal. Devolve (relatório por sensor, divergências célula-mês)."""
    m_d = d.groupby(["sensor", "cell", "ym"], as_index=False)[["n", "frp_sum"]].sum()
    rows, bad = [], []
    for s in SENSORS:
        mm = monthly[["cell", "ym", f"n_{s}", f"frp_sum_{s}"]].rename(
            columns={f"n_{s}": "n_m", f"frp_sum_{s}": "frp_m"})
        mm = mm[(mm.n_m != 0) | (mm.frp_m != 0)]
        x = m_d[m_d.sensor == s].merge(mm, on=["cell", "ym"], how="outer").fillna(
            {"n": 0, "frp_sum": 0, "n_m": 0, "frp_m": 0})
        x["sensor"] = s
        x["dn"] = x.n - x.n_m
        x["dfrp"] = (x.frp_sum - x.frp_m).round(3)
        err = x[(x.dn != 0) | (x.dfrp.abs() > tol_frp)]
        rows.append({"sensor": s, "cell_months": len(x),
                     "n_daily": int(x.n.sum()), "n_monthly": int(x.n_m.sum()),
                     "frp_daily_MW": round(float(x.frp_sum.sum()), 1),
                     "frp_monthly_MW": round(float(x.frp_m.sum()), 1),
                     "cell_months_diverging": len(err), "ok": len(err) == 0})
        bad.append(err[["sensor", "cell", "ym", "n", "n_m", "dn", "frp_sum", "frp_m", "dfrp"]])
    return pd.DataFrame(rows), pd.concat(bad, ignore_index=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Auditoria diária × mensal (res 5)")
    ap.add_argument("--grid", default=GRID)
    ap.add_argument("--monthly", default=MONTHLY)
    ap.add_argument("--outdir", default=OUTDIR)
    ap.add_argument("--csv", action="store_true", help="grava CSV diário filtrado")
    ap.add_argument("--cell", default=None)
    ap.add_argument("--lat", type=float, default=None)
    ap.add_argument("--lon", type=float, default=None)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--sensor", default=None, help="ex.: SNPP")
    args = ap.parse_args(argv)

    t = time.time()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    cell_fn = h3_cell_fn()

    grid = pd.read_parquet(args.grid, columns=["sensor", "ts", "gy", "gx", "n_pix", "frp_sum"])
    d = daily(grid, cell_fn)
    d.to_parquet(out / "audit_daily.parquet", index=False)
    print(f"diário: {len(d):,} linhas (sensor × hexágono × dia) · {d.cell.nunique():,} hexágonos")

    monthly = pd.read_parquet(args.monthly)
    rep, bad = compare(d, monthly)
    rep.to_csv(out / "audit_report.csv", index=False)
    bad.to_csv(out / "audit_mismatch.csv", index=False)
    print(rep.to_string(index=False))
    print("RESULTADO:", "✓ diário soma exatamente o mensal" if rep.ok.all()
          else f"✗ {len(bad):,} célula-mês divergentes → {out / 'audit_mismatch.csv'}")

    if args.csv:
        f = d
        cell = args.cell or (cell_fn(args.lat, args.lon) if args.lat is not None else None)
        if cell:
            f = f[f.cell == cell]
        if args.year:
            f = f[f.ym // 100 == args.year]
        if args.sensor:
            f = f[f.sensor == args.sensor.upper()]
        tag = "_".join(str(v) for v in (cell, args.year, args.sensor) if v) or "todos"
        p = out / f"audit_daily_{tag}.csv"
        f.to_csv(p, index=False)
        print(f"CSV: {p} · {len(f):,} linhas" + ("  (Excel abre até ~1 M)" if len(f) > 1_000_000 else ""))
    print(f"{time.time() - t:.0f} s")


if __name__ == "__main__":
    main()

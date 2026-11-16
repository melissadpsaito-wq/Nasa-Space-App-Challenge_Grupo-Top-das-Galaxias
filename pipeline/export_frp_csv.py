"""CSV enxuto: cell, lat, lon, year, month, frp — só meses com FRP > 0 (sem nulos/zeros).

Lê data/processed/res5/frp_monthly.parquet (gerar antes com `python -m pipeline.export_frp_monthly`).
frp = Σ FRP (MW) de todos os pixels do hexágono no mês, de UM satélite por mês:
  --frp src   (padrão) satélite da linha do tempo: TERRA até 2002-06 · AQUA até 2012-01 · SNPP depois
              ATENÇÃO: degrau em fev/2012 (S-NPP vê ~1,17× o Aqua em ΣFRP, D29) — FRP não é harmonizado
  --frp AQUA  só Aqua (2002–2025, sem troca de sensor) · --frp SNPP só S-NPP (2012–2025)
  --with-src  acrescenta a coluna src (satélite de cada linha)

Uso (raiz do repo):
  python -m pipeline.export_frp_csv
  python -m pipeline.export_frp_csv --frp AQUA
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

MONTHLY = "data/processed/res5/frp_monthly.parquet"
SENSORS = ["TERRA", "AQUA", "SNPP", "N20"]


def build(m: pd.DataFrame, frp: str = "src", with_src: bool = False) -> pd.DataFrame:
    if frp == "src":
        d = m[["cell", "lat", "lon", "year", "month", "src", "frp_sum_src"]].rename(columns={"frp_sum_src": "frp"})
    else:
        d = m[["cell", "lat", "lon", "year", "month", f"frp_sum_{frp}"]].rename(columns={f"frp_sum_{frp}": "frp"})
        d["src"] = frp
    d = d[d.frp.notna() & (d.frp > 0)]
    cols = ["cell", "lat", "lon", "year", "month", "frp"] + (["src"] if with_src else [])
    return d[cols].reset_index(drop=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="CSV cell, lat, lon, year, month, frp (sem zeros)")
    ap.add_argument("--monthly", default=MONTHLY)
    ap.add_argument("--frp", default="src", type=str.upper, choices=["SRC", *SENSORS])
    ap.add_argument("--with-src", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    frp = "src" if args.frp == "SRC" else args.frp

    m = pd.read_parquet(args.monthly)
    d = build(m, frp, args.with_src)
    out = Path(args.out or Path(args.monthly).with_name(f"frp_{frp}_nonzero.csv"))
    d.to_csv(out, index=False)
    print(f"gravado {out} · {len(d):,} linhas · {d.cell.nunique():,} hexágonos · "
          f"{d.year.min()}–{d.year.max()} · Σ FRP {d.frp.sum():,.0f} MW · {out.stat().st_size / 1e6:.0f} MB")
    if len(d) > 1_048_576:
        print("  aviso: mais de 1.048.576 linhas — o Excel não abre inteiro; use pandas ou filtre por ano")


if __name__ == "__main__":
    main()

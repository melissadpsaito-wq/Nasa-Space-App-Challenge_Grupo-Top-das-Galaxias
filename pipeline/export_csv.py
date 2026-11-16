"""CSV da série harmonizada (formato longo) para testar o modelo preditivo (D35).

Uma linha por célula H3 × mês: cell, lat, lon, ym, year, month, n_harm, n_raw, lo, hi, low_conf, src
- lat/lon = centro da célula (h3); valores em escala S-NPP, SEM o × 10 do app.
- Separador "," e ponto decimal. Fica em data/processed/ (fora do Git).
- ~8,7 M linhas (res 5): abre em pandas/DuckDB, NÃO no Excel (limite de 1.048.576 linhas).

Uso (raiz do repo):
  python -m pipeline.export_csv                      # res 5 completo (inclui meses sem fogo)
  python -m pipeline.export_csv --nonzero            # só célula-mês com fogo (menor)
  python -m pipeline.export_csv --gzip               # .csv.gz (~5× menor; pandas lê direto)
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

HARM_DEFAULT = "data/processed/res5/harm_series.parquet"
COLS = ["cell", "lat", "lon", "ym", "year", "month",
        "n_harm", "n_raw", "lo", "hi", "low_conf", "src"]


def cell_centers(cells) -> pd.DataFrame:
    try:
        import h3
    except ImportError:
        print("  aviso: h3 não instalado → lat/lon vazios")
        return pd.DataFrame({"cell": cells, "lat": pd.NA, "lon": pd.NA})
    ll = [h3.cell_to_latlng(c) for c in cells]
    return pd.DataFrame({"cell": cells,
                         "lat": [round(a, 4) for a, _ in ll],
                         "lon": [round(b, 4) for _, b in ll]})


def build(harm: pd.DataFrame, nonzero: bool = False) -> pd.DataFrame:
    h = harm.copy()
    if nonzero:
        h = h[(h.n_harm.fillna(0) > 0) | (h.n_raw.fillna(0) > 0)]
    h["year"], h["month"] = h.ym // 100, h.ym % 100
    for c in ["n_harm", "lo", "hi"]:
        h[c] = h[c].astype(float).round(3)
    h["low_conf"] = h.low_conf.fillna(0).astype(int)
    if "src" not in h.columns:
        h["src"] = ""
    h = h.merge(cell_centers(h.cell.unique()), on="cell", how="left")
    return h[COLS].sort_values(["cell", "ym"], kind="stable").reset_index(drop=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="CSV da série harmonizada (modelo preditivo)")
    ap.add_argument("--harm", default=HARM_DEFAULT)
    ap.add_argument("--out", default=None, help="padrão: ao lado do Parquet")
    ap.add_argument("--nonzero", action="store_true", help="só célula-mês com fogo")
    ap.add_argument("--gzip", action="store_true")
    args = ap.parse_args(argv)

    t = time.time()
    harm = pd.read_parquet(args.harm)
    df = build(harm, args.nonzero)
    out = Path(args.out) if args.out else Path(args.harm).with_suffix(
        (".nonzero" if args.nonzero else "") + ".csv" + (".gz" if args.gzip else ""))
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip" if args.gzip else None)

    print(f"gravado {out} · {len(df):,} linhas · {df.cell.nunique():,} células · "
          f"{df.ym.min()}–{df.ym.max()} · {out.stat().st_size / 1e6:.0f} MB · {time.time() - t:.0f} s")
    print(f"  conferência: Σ n_harm {df.n_harm.sum():,.1f} · Σ n_raw {df.n_raw.sum():,.1f}")


if __name__ == "__main__":
    main()

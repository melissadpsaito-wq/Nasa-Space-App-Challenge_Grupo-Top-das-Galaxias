"""Tabela mensal por hexágono com FRP somado, para TESTE do modelo preditivo.

Uma linha por célula H3 res 5 × mês (nov/2000–dez/2025, inclusive meses sem fogo = 0):
  cell, lat, lon, ym, year, month,
  n_harm, n_raw, low_conf, src                      (série harmonizada, harm_series)
  frp_sum_TERRA, frp_sum_AQUA, frp_sum_SNPP, frp_sum_N20   (Σ FRP de todos os pixels no mês, MW — D29)
  n_TERRA, n_AQUA, n_SNPP, n_N20                    (contagem na grade 2 km, por sensor)
  frp_sum_src                                       (Σ FRP do satélite da linha do tempo daquele mês)

ATENÇÃO: FRP NÃO é harmonizado. Em ΣFRP o S-NPP vê 1,17× o Aqua (D29, Brasil 2025);
`frp_sum_src` tem degrau em fev/2012. Para série sem degrau use uma coluna de 1 sensor
(ex. frp_sum_SNPP de 2012 em diante ou frp_sum_AQUA 2002–2025).

Uso (raiz do repo):
  python -m pipeline.export_frp_monthly                 # Parquet (recomendado)
  python -m pipeline.export_frp_monthly --csv --gzip    # + CSV
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

AGG = "data/interim/res5/agg_monthly.parquet"
HARM = "data/processed/res5/harm_series.parquet"
OUT = "data/processed/res5/frp_monthly.parquet"
SENSORS = ["TERRA", "AQUA", "SNPP", "N20"]
YM_START, YM_END = 200011, 202512


def build(agg: pd.DataFrame, harm: pd.DataFrame) -> pd.DataFrame:
    a = agg[(agg.ym >= YM_START) & (agg.ym <= YM_END)]
    wide = (a.pivot_table(index=["cell", "ym"], columns="sensor",
                          values=["frp_sum", "n"], aggfunc="sum", fill_value=0))
    wide.columns = [f"{v}_{s}" for v, s in wide.columns]
    for s in SENSORS:
        for v in ("frp_sum", "n"):
            if f"{v}_{s}" not in wide.columns:
                wide[f"{v}_{s}"] = 0
    wide = wide.reset_index()

    h = harm[(harm.ym >= YM_START) & (harm.ym <= YM_END)][
        ["cell", "ym", "n_harm", "n_raw", "low_conf", "src"]]
    df = h.merge(wide, on=["cell", "ym"], how="left")
    extra = set(zip(wide.cell, wide.ym)) - set(zip(h.cell, h.ym))
    if extra:
        print(f"  aviso: {len(extra)} célula-mês do agg_monthly fora da harm_series (ignoradas)")

    fr = [f"frp_sum_{s}" for s in SENSORS]
    nn = [f"n_{s}" for s in SENSORS]
    df[fr] = df[fr].fillna(0).astype(float).round(2)
    df[nn] = df[nn].fillna(0).astype(int)

    src = df["src"].astype(str).str.upper()
    df["frp_sum_src"] = np.select([src == s for s in SENSORS], [df[f"frp_sum_{s}"] for s in SENSORS], 0.0)

    df["year"], df["month"] = df.ym // 100, df.ym % 100
    df["n_harm"] = df.n_harm.astype(float).round(3)
    df["low_conf"] = df.low_conf.fillna(0).astype(int)
    df = df.merge(centers(df.cell.unique()), on="cell", how="left")
    cols = (["cell", "lat", "lon", "ym", "year", "month", "n_harm", "n_raw", "low_conf", "src"]
            + fr + nn + ["frp_sum_src"])
    return df[cols].sort_values(["cell", "ym"], kind="stable").reset_index(drop=True)


def centers(cells) -> pd.DataFrame:
    try:
        import h3
    except ImportError:
        return pd.DataFrame({"cell": cells, "lat": np.nan, "lon": np.nan})
    ll = [h3.cell_to_latlng(c) for c in cells]
    return pd.DataFrame({"cell": cells, "lat": [round(x, 4) for x, _ in ll],
                         "lon": [round(y, 4) for _, y in ll]})


def check(agg: pd.DataFrame, df: pd.DataFrame) -> None:
    a = agg[(agg.ym >= YM_START) & (agg.ym <= YM_END)]
    for s in SENSORS:
        src_sum = float(a.loc[a.sensor == s, "frp_sum"].sum())
        out_sum = float(df[f"frp_sum_{s}"].sum())
        ok = abs(src_sum - out_sum) <= 0.01 * len(df) ** 0.5 + 1
        print(f"  ΣFRP {s:5s}: agg {src_sum:,.0f} MW · tabela {out_sum:,.0f} MW {'✓' if ok else '✗'}")
        assert ok, f"conservação do FRP falhou em {s}"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="FRP mensal por hexágono (teste do modelo)")
    ap.add_argument("--agg", default=AGG)
    ap.add_argument("--harm", default=HARM)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--csv", action="store_true", help="grava também CSV")
    ap.add_argument("--gzip", action="store_true", help="CSV comprimido")
    args = ap.parse_args(argv)

    t = time.time()
    agg = pd.read_parquet(args.agg, columns=["sensor", "cell", "ym", "n", "frp_sum"])
    harm = pd.read_parquet(args.harm)
    df = build(agg, harm)
    check(agg, df)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"gravado {out} · {len(df):,} linhas · {df.cell.nunique():,} células · {time.time() - t:.0f} s")
    if args.csv:
        c = out.with_suffix(".csv" + (".gz" if args.gzip else ""))
        df.to_csv(c, index=False, compression="gzip" if args.gzip else None)
        print(f"gravado {c} · {c.stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()

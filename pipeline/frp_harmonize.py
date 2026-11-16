"""D40 — ΣFRP mensal harmonizado com a ponte M1 (sem alterar o M1). D42: --brazil = todos os hexágonos do país.
Passos: prep → m1 --eval → harmonize → csv [--with-zeros | --brazil data/raw/br_pais.geojson] [--gzip]
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


def scale_of(agg, ref=REF):
    r = agg[agg.sensor == ref]
    return float(r.frp_sum.sum() / r.n.sum())


def prep(agg):
    s = scale_of(agg)
    out = agg.copy()
    out["n_count"] = out["n"]
    out["n"] = (out["frp_sum"].fillna(0) / s).astype(float)
    return out, s


def month_range(start=200011, end=202512):
    y, m, out = start // 100, start % 100, []
    while y * 100 + m <= end:
        out.append(y * 100 + m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def brazil_cells(geojson_path, res=5):
    import h3
    geo = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    feats = geo["features"] if geo.get("type") == "FeatureCollection" else [geo]
    cells = set()
    for f in feats:
        g = f.get("geometry", f)
        cells |= set(h3.geo_to_cells(g, res))
    return cells


def full_grid(harm, extra_cells=None):
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


def to_csv_frame(harm, s, min_mw=0.0, with_zeros=False, extra_cells=None):
    h = full_grid(harm, extra_cells) if with_zeros else harm.copy()
    h["frp"] = (h.n_harm.astype(float) * s).round(2)
    if with_zeros:
        h.loc[h.frp <= min_mw, "frp"] = 0.0
    else:
        h = h[h.frp > min_mw]
    h["year"], h["month"] = h.ym // 100, h.ym % 100
    try:
        import h3
        ll = {c: h3.cell_to_latlng(c) for c in h.cell.unique()}
        h["lat"] = h.cell.map(lambda c: round(ll[c][0], 4))
        h["lon"] = h.cell.map(lambda c: round(ll[c][1], 4))
    except ImportError:
        h["lat"] = h["lon"] = np.nan
    return h[["cell", "lat", "lon", "year", "month", "frp"]].sort_values(
        ["cell", "year", "month"], kind="stable").reset_index(drop=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="D40 — ΣFRP harmonizado via M1")
    ap.add_argument("step", choices=["prep", "csv"])
    ap.add_argument("--agg", default=AGG_IN)
    ap.add_argument("--harm", default=HARM)
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-mw", type=float, default=0.0)
    ap.add_argument("--with-zeros", action="store_true")
    ap.add_argument("--gzip", action="store_true")
    ap.add_argument("--brazil", default=None)
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
        print(f"escala s = {s:.3f} MW por unidade ({REF}) · gravado {p} ({len(out):,} linhas)")
        return

    s = json.loads(Path(META).read_text())["scale_mw"]
    harm = pd.read_parquet(args.harm)
    extra = brazil_cells(args.brazil) if args.brazil else None
    d = to_csv_frame(harm, s, args.min_mw, args.with_zeros, extra)
    default = (CSV.replace("_nonzero", "_brasil") if args.brazil
               else CSV.replace("_nonzero", "_full") if args.with_zeros else CSV)
    p = Path(args.out or default + (".gz" if args.gzip else ""))
    p.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(p, index=False, compression="gzip" if args.gzip else None)
    if args.with_zeros:
        print(f"  linhas com frp = 0: {(d.frp == 0).sum():,}")
    print(f"gravado {p} · {len(d):,} linhas · {d.cell.nunique():,} hexágonos · Σ FRP {d.frp.sum():,.0f} MW")
    if len(d) > 1_048_576:
        print("  aviso: mais de 1.048.576 linhas — o Excel não abre inteiro")


if __name__ == "__main__":
    main()
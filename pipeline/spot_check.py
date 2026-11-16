"""Validação independente do CSV de FRP (camadas 5 e 6).

5) Recalcula UMA linha (hexágono × mês) direto de data/clean/<SENSOR>/<ano>.parquet, sem usar grid/agg:
   foco → quadrado 0,02° (floor) → centro → h3 res 5 → filtra mês → Σ FRP  ==  frp do CSV?
6) Sanidade do CSV inteiro: colunas, nulos, zeros, negativos, faixa de lat/lon, mês, ano, duplicatas.

Uso (raiz do repo):
  python -m pipeline.spot_check --csv data/processed/res5/frp_AQUA_nonzero.csv --sensor AQUA --lat -17.8 --lon -56.4 --ym 202009
  python -m pipeline.spot_check --csv data/processed/res5/frp_AQUA_nonzero.csv --sensor AQUA --random 5
"""
from __future__ import annotations

import argparse
import math

import pandas as pd

STEP, RES = 0.02, 5
BBOX = (-34.0, 5.5, -74.5, -28.5)   # lat_min, lat_max, lon_min, lon_max (Brasil + ilhas)


def sanity(d: pd.DataFrame) -> bool:
    checks = {
        "colunas = cell, lat, lon, year, month, frp": list(d.columns)[:6] == ["cell", "lat", "lon", "year", "month", "frp"],
        "sem nulos": not d[["cell", "lat", "lon", "year", "month", "frp"]].isna().any().any(),
        "frp > 0 em todas as linhas": bool((d.frp > 0).all()),
        "mês entre 1 e 12": bool(d.month.between(1, 12).all()),
        "ano entre 2000 e 2025": bool(d.year.between(2000, 2025).all()),
        "lat/lon dentro do Brasil (caixa)": bool(d.lat.between(BBOX[0], BBOX[1]).all() and d.lon.between(BBOX[2], BBOX[3]).all()),
        "sem duplicata hexágono × mês": not d.duplicated(["cell", "year", "month"]).any(),
    }
    for k, v in checks.items():
        print(f"  {'✓' if v else '✗'} {k}")
    return all(checks.values())


def recompute(clean: str, sensor: str, cell: str, ym: int, cell_fn) -> tuple[float, int]:
    y, m = divmod(ym, 100)
    f = pd.read_parquet(f"{clean}/{sensor}/{y}.parquet", columns=["ts", "latitude", "longitude", "frp"])
    ts = pd.to_datetime(f.ts, utc=True)
    f = f[ts.dt.month == m]
    gy = (f.latitude / STEP).apply(math.floor)
    gx = (f.longitude / STEP).apply(math.floor)
    sq = pd.DataFrame({"gy": gy, "gx": gx}).drop_duplicates()
    sq["c"] = [cell_fn((a + .5) * STEP, (b + .5) * STEP) for a, b in zip(sq.gy, sq.gx)]
    keep = set(map(tuple, sq.loc[sq.c == cell, ["gy", "gx"]].to_numpy()))
    sel = [(a, b) in keep for a, b in zip(gy, gx)]
    return float(f.loc[sel, "frp"].sum()), int(sum(sel))


def main(argv=None) -> None:
    import h3
    ap = argparse.ArgumentParser(description="Validação independente do CSV de FRP")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--sensor", required=True, help="satélite usado no CSV (ex. AQUA)")
    ap.add_argument("--clean", default="data/clean")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--ym", type=int, help="AAAAMM")
    ap.add_argument("--random", type=int, default=0, help="sorteia N linhas do CSV para conferir")
    args = ap.parse_args(argv)
    cell_fn = lambda a, b: h3.latlng_to_cell(a, b, RES)

    d = pd.read_csv(args.csv)
    print(f"CSV: {len(d):,} linhas · {d.cell.nunique():,} hexágonos · Σ FRP {d.frp.sum():,.0f} MW")
    print("Sanidade:")
    ok = sanity(d)

    alvos = []
    if args.lat is not None and args.ym:
        alvos.append((cell_fn(args.lat, args.lon), args.ym))
    if args.random:
        s = d.sample(args.random, random_state=42)
        alvos += [(c, int(y) * 100 + int(m)) for c, y, m in zip(s.cell, s.year, s.month)]

    print("Recálculo direto dos focos limpos:")
    for cell, ym in alvos:
        row = d[(d.cell == cell) & (d.year == ym // 100) & (d.month == ym % 100)]
        csv_frp = float(row.frp.iloc[0]) if len(row) else 0.0
        frp, n = recompute(args.clean, args.sensor.upper(), cell, ym, cell_fn)
        hit = abs(frp - csv_frp) <= 0.01 + 1e-6 * frp
        ok &= hit
        print(f"  {'✓' if hit else '✗'} {cell} {ym}: focos {n:,} · Σ FRP focos {frp:,.2f} MW · CSV {csv_frp:,.2f} MW")
    print("RESULTADO:", "✓ tudo confere" if ok else "✗ ver itens marcados")


if __name__ == "__main__":
    main()

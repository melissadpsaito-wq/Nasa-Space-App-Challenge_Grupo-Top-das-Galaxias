"""D43 — Valores DIÁRIOS harmonizados (focos e ΣFRP) por hexágono res 5, distribuindo o mensal harmonizado.

Para cada hexágono × mês, com o satélite da linha do tempo daquele mês (src: TERRA → AQUA → SNPP):
    focos_dia = focos_harm_mês × n_dia   / Σ n_dia      (n_dia   = detecções do src no dia, grade 2 km)
    frp_dia   = frp_harm_mês   × frp_dia_bruto / Σ frp_dia_bruto
Soma dos dias = valor mensal harmonizado (exato). Meses sem nenhuma detecção do src (termo aditivo do M1,
fogo fraco esperado onde o MODIS não viu) não têm dia: viram UMA linha com day vazio e o valor do mês.

Entradas (raiz do repo):
  data/processed/res5/audit_daily.parquet        diário bruto (gera com `python -m pipeline.audit_daily` se faltar)
  data/processed/res5/harm_series.parquet        focos harmonizados (cell, ym, n_harm, src)
  data/processed/res5_frp/harm_series.parquet    ΣFRP harmonizado em unidades s (D40) + data/interim/res5_frp/scale.json
Saída: data/processed/res5_frp/fogo_diario_harm.csv  →  cell, lat, lon, year, month, day, frp, focos
       (só dias com fogo; dias sem fogo não são listados — seriam ~290 M linhas)

Uso:  python -m pipeline.daily_harm
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

DAILY = "data/processed/res5/audit_daily.parquet"
HARM_N = "data/processed/res5/harm_series.parquet"
HARM_F = "data/processed/res5_frp/harm_series.parquet"
SCALE = "data/interim/res5_frp/scale.json"
OUT = "data/processed/res5_frp/fogo_diario_harm.csv"
KEY = ["cell", "ym"]


def timeline_src(ym: int) -> str:
    return "TERRA" if ym <= 200206 else "AQUA" if ym <= 201201 else "SNPP"


def monthly(hn: pd.DataFrame, hf: pd.DataFrame, s: float) -> pd.DataFrame:
    a = hn[["cell", "ym", "n_harm", "src"]].rename(columns={"n_harm": "focos_m"})
    b = hf[["cell", "ym", "n_harm"]].assign(frp_m=lambda x: x.n_harm.astype(float) * s)[["cell", "ym", "frp_m"]]
    m = a.merge(b, on=KEY, how="outer")
    m[["focos_m", "frp_m"]] = m[["focos_m", "frp_m"]].fillna(0.0)
    miss = m.src.isna()
    m.loc[miss, "src"] = m.loc[miss, "ym"].map(timeline_src)
    m["src"] = m.src.astype(str).str.upper()
    return m[(m.focos_m > 0) | (m.frp_m > 0)]


def distribute(daily: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    d = daily.merge(m, on=KEY, how="inner")
    d = d[d.sensor == d.src].copy()
    g = d.groupby(KEY)
    d["N"] = g["n"].transform("sum")
    d["F"] = g["frp_sum"].transform("sum")
    d["focos"] = np.where(d.N > 0, d.focos_m * d.n / d.N.where(d.N > 0, 1), 0.0)
    d["frp"] = np.where(d.F > 0, d.frp_m * d.frp_sum / d.F.where(d.F > 0, 1), 0.0)
    d["day"] = d.date.str[8:10].astype(int)
    rows = d[(d.focos > 0) | (d.frp > 0)][["cell", "ym", "day", "frp", "focos"]]

    # o que não pôde ser distribuído (mês sem detecção do src) vira linha mensal com day vazio
    got = d.groupby(KEY).agg(N=("N", "first"), F=("F", "first")).reset_index()
    r = m.merge(got, on=KEY, how="left").fillna({"N": 0, "F": 0})
    r["focos"] = np.where(r.N > 0, 0.0, r.focos_m)
    r["frp"] = np.where(r.F > 0, 0.0, r.frp_m)
    r = r[(r.focos > 0) | (r.frp > 0)][["cell", "ym", "frp", "focos"]].assign(day=pd.NA)
    out = pd.concat([rows, r[["cell", "ym", "day", "frp", "focos"]]], ignore_index=True)
    out["day"] = out["day"].astype("Int64")
    return out


def finish(out: pd.DataFrame) -> pd.DataFrame:
    out = out.copy()
    out["year"], out["month"] = out.ym // 100, out.ym % 100
    try:
        import h3
        ll = {c: h3.cell_to_latlng(c) for c in out.cell.unique()}
        out["lat"] = out.cell.map(lambda c: round(ll[c][0], 4))
        out["lon"] = out.cell.map(lambda c: round(ll[c][1], 4))
    except ImportError:
        out["lat"] = out["lon"] = np.nan
    out["frp"] = out.frp.round(3)
    out["focos"] = out.focos.round(4)
    return out[["cell", "lat", "lon", "year", "month", "day", "frp", "focos"]].sort_values(
        ["cell", "year", "month", "day"], kind="stable", na_position="last").reset_index(drop=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="D43 — diário harmonizado (focos e ΣFRP)")
    ap.add_argument("--daily", default=DAILY)
    ap.add_argument("--harm-n", default=HARM_N)
    ap.add_argument("--harm-f", default=HARM_F)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    t = time.time()
    s = json.loads(Path(SCALE).read_text())["scale_mw"]
    daily = pd.read_parquet(args.daily, columns=["sensor", "cell", "date", "ym", "n", "frp_sum"])
    m = monthly(pd.read_parquet(args.harm_n), pd.read_parquet(args.harm_f), s)
    out = distribute(daily, m)

    for col, ref in (("focos", "focos_m"), ("frp", "frp_m")):
        a, b = float(out[col].sum()), float(m[ref].sum())
        assert abs(a - b) <= 1e-6 * max(b, 1) + 1, f"conservação {col}: diário {a:,.1f} × mensal {b:,.1f}"
        print(f"  conservação {col:5s}: Σ diário {a:,.1f} = Σ mensal harmonizado {b:,.1f} ✓")

    out = finish(out)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    # D45 (opção A): diário só com dias detectados; estimativa sem dia vai para arquivo mensal separado
    dias = out[out.day.notna()]
    adit = out[out.day.isna()].drop(columns="day")
    dias.to_csv(p, index=False)
    pa = p.with_name(p.stem.replace("diario", "aditivo_mensal") + p.suffix)
    adit.to_csv(pa, index=False)
    print(f"gravado {p} · {len(dias):,} dias com fogo (day sempre preenchido) · {dias.cell.nunique():,} hexágonos · "
          f"{p.stat().st_size / 1e6:.0f} MB")
    print(f"gravado {pa} · {len(adit):,} hexágono-mês de fogo fraco estimado sem dia (nota mensal, D45) · "
          f"Σ focos {adit.focos.sum():,.0f} · Σ FRP {adit.frp.sum():,.0f} MW")
    print(f"  diário + aditivo = mensal harmonizado · {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()

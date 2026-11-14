"""Conferência do entendimento antes do M1 (Guia 48h v2 §3.2): reproduzir a decomposição do METHOD.md.

    Bruto 5,42 → grade 0,01° por passagem 3,58 → 0,02° 3,45 → + limiar de FRP (~9,5 MW) ≈ 1,0   (Brasil 2025)

Passagem = sensor + ts + daynight (mesma definição da análise de 13/11 e do pipeline/grid.py).
Célula = (floor(lat/g), floor(lon/g)). FRP da célula = máximo (D26).
τ = FRP tal que #S-NPP(frp_max ≥ τ) = #Aqua na mesma grade. Prévia do §3.3: τ por trimestre × dia/noite (D33).

Uso (raiz do repo):
    python -m pipeline.bridges.check_method --clean data/clean --year 2025
    python -m pipeline.bridges.check_method --clean data/clean_pantanal --year 2019
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.bridges import base

GRIDS = (0.01, 0.02)
EXPECTED_BR_2025 = {"raw": 5.42, 0.01: 3.58, 0.02: 3.45, "tau": 9.5}   # METHOD.md


def collapse(df: pd.DataFrame, g: float) -> pd.DataFrame:
    """Uma linha por célula g° × passagem: ts, daynight, gy, gx, frp_max."""
    d = df.assign(gy=np.floor(df.latitude / g).astype("int64"), gx=np.floor(df.longitude / g).astype("int64"))
    return d.groupby(["ts", "daynight", "gy", "gx"], as_index=False, sort=False).frp.max().rename(
        columns={"frp": "frp_max"})


def tau_equal_counts(frp_max: np.ndarray, n_target: int) -> float:
    """τ tal que #(frp_max ≥ τ) ≈ n_target (n_target ≥ total → 0)."""
    s = np.sort(np.asarray(frp_max, dtype=float))[::-1]
    if len(s) == 0 or n_target <= 0:
        return float("nan")
    return float(s[min(n_target, len(s)) - 1])


def decompose(aqua: pd.DataFrame, snpp: pd.DataFrame, cfg: dict | None = None) -> dict:
    """aqua, snpp = focos limpos (schema DATA_DICTIONARY §1). Devolve razões, τ e tabelas por mês e estrato."""
    res = {"n_aqua": len(aqua), "n_snpp": len(snpp), "raw": len(snpp) / max(len(aqua), 1), "grid": {}}
    month = lambda d: d.ts.dt.month                                                     # noqa: E731
    by_month = pd.DataFrame({"raw": snpp.groupby(month(snpp)).size() / aqua.groupby(month(aqua)).size()})
    for g in GRIDS:
        ca, cs = collapse(aqua, g), collapse(snpp, g)
        tau = tau_equal_counts(cs.frp_max, len(ca))
        strong = int((cs.frp_max >= tau).sum())
        res["grid"][g] = {"n_aqua": len(ca), "n_snpp": len(cs), "ratio": len(cs) / max(len(ca), 1),
                          "tau": tau, "ratio_after_tau": strong / max(len(ca), 1)}
        by_month[f"grid_{g}"] = cs.groupby(month(cs)).size() / ca.groupby(month(ca)).size()
        if g == 0.02 and cfg is not None:                                               # prévia §3.3 (8 estratos)
            rows = []
            for (s, dn), sub in cs.assign(season=base.season_of(cs.ts.dt.month, cfg)).groupby(["season", "daynight"]):
                na = int(((base.season_of(ca.ts.dt.month, cfg) == s) & (ca.daynight == dn)).sum())
                rows.append({"season": s, "daynight": dn, "n_aqua": na, "n_snpp": len(sub),
                             "ratio": len(sub) / max(na, 1), "tau": tau_equal_counts(sub.frp_max, na)})
            res["strata"] = pd.DataFrame(rows)
        if g == 0.02:                                                                   # D29: Σ frp_max das células 2 km
            res["frp_grid"] = cs.frp_max.sum() / max(ca.frp_max.sum(), 1e-9)
            by_month["frp_grid_0.02"] = cs.groupby(month(cs)).frp_max.sum() / ca.groupby(month(ca)).frp_max.sum()
            res["frp_daynight"] = (cs.groupby("daynight").frp_max.sum() / ca.groupby("daynight").frp_max.sum()).to_dict()
    # ΣFRP bruto (sem grade): a energia de um fogo dividida em vários pixels soma de volta
    res["frp_raw"] = snpp.frp.sum() / max(aqua.frp.sum(), 1e-9)
    by_month["frp_raw"] = snpp.groupby(month(snpp)).frp.sum() / aqua.groupby(month(aqua)).frp.sum()
    res["by_month"] = by_month
    return res


def load_clean(clean: Path, sensor: str, year: int) -> pd.DataFrame:
    p = clean / sensor / f"{year}.parquet"
    if not p.exists():
        raise SystemExit(f"Não achei {p}. Rode antes: python -m pipeline.ingest --area brasil --years {year}")
    df = pd.read_parquet(p, columns=["ts", "latitude", "longitude", "frp", "daynight"])
    return df.assign(ts=pd.to_datetime(df.ts))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Reproduz 5,42 → 3,45 → ≈1,0 (METHOD.md).")
    ap.add_argument("--clean", default="data/clean")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--config", default=str(base.CONFIG))
    a = ap.parse_args(argv)
    cfg = base.load_config(a.config)
    r = decompose(load_clean(Path(a.clean), "AQUA", a.year), load_clean(Path(a.clean), "SNPP", a.year), cfg)

    ref = EXPECTED_BR_2025 if (a.year == 2025 and Path(a.clean).name == "clean") else {}
    exp = lambda key: f"{ref[key]:.2f}" if key in ref else "–"                         # noqa: E731
    pd.set_option("display.width", 140)
    print(f"{a.clean} · {a.year} · Aqua {r['n_aqua']:,} · S-NPP {r['n_snpp']:,} focos limpos\n")
    print(f"{'Etapa':<34}{'Razão S-NPP/Aqua':>18}{'Esperado':>10}")
    print(f"{'Bruto':<34}{r['raw']:>18.2f}{exp('raw'):>10}")
    for g, v in r["grid"].items():
        print(f"{f'Grade {g}° por passagem':<34}{v['ratio']:>18.2f}{exp(g):>10}")
    g2 = r["grid"][0.02]
    label = f"+ limiar FRP τ = {g2['tau']:.1f} MW (0,02°)"
    print(f"{label:<34}{g2['ratio_after_tau']:>18.2f}{'≈1,0':>10}")
    print(f"(τ na grade 0,01° = {r['grid'][0.01]['tau']:.1f} MW · esperado ~{ref.get('tau', '–')} MW)\n")
    dn = " · ".join(f"{k} {v:.2f}" for k, v in r["frp_daynight"].items())
    print(f"ΣFRP S-NPP/Aqua: bruto {r['frp_raw']:.2f} · Σ frp_max grade 0,02° {r['frp_grid']:.2f} (D29) · por turno: {dn}\n")
    print("Razão por mês (contagens e ΣFRP):\n" + r["by_month"].round(2).to_string())
    if "strata" in r:
        print("\nPrévia §3.3 — τ por trimestre × dia/noite (grade 0,02°):\n" + r["strata"].round(2).to_string(index=False))
    if ref:
        ok = abs(r["raw"] - ref["raw"]) < 0.05 and abs(g2["ratio"] - ref[0.02]) < 0.15
        print("\n" + ("OK: bruto e 0,02° batem com o METHOD.md." if ok else
                      "ATENÇÃO: não bate com o METHOD.md — rever definição de passagem (ts + daynight) com o Murilo."))


if __name__ == "__main__":
    main()

"""Série harmonizada (escala S-NPP) célula × mês, nov/2000 → dez/2025, seguindo a linha do tempo do YAML.

PROVISÓRIA com M1: libera as features da previsão (D35, sáb 23:30) e o export do Pantanal (2.4) antes do
vencedor do CP3 e do bootstrap (3.4). Quando a 3.4 rodar, `lo`/`hi`/`low_conf` passam a vir do bootstrap.

Linha do tempo (sensors.yaml `timeline`, DATA_DICTIONARY §8):
  TERRA 200011–200206 → cadeia terra_aqua → aqua_snpp (low_conf)
  AQUA  200207–201201 → ponte aqua_snpp
  SNPP  201202–202512 → nativo (n_harm = n_raw)

Saída (DATA_DICTIONARY §5): cell, ym, n_harm, n_raw, lo, hi, low_conf, src
  provisório: lo = hi = n_harm · low_conf = 1 só no trecho Terra (a regra completa vem da 3.4)

Uso (raiz do repo):
  python -m pipeline.bridges.harmonize --lam 20                                   # Brasil res 4 → data/processed/harm_series.parquet
  python -m pipeline.bridges.harmonize --lam 20 --agg data/interim/pantanal/agg_monthly.parquet --out data/processed/pantanal/harm_series.parquet
  python -m pipeline.bridges.harmonize --lam 20 --hier --agg data/interim/res5/agg_monthly.parquet --out data/processed/res5/harm_series.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.bridges import base
from pipeline.bridges.m1 import M1

OUT_COLS = ["cell", "ym", "n_harm", "n_raw", "lo", "hi", "low_conf", "src"]


def analysis_months(cfg: dict) -> list[int]:
    lo, hi = cfg["analysis_period"]
    return [ym for ym in base.months_of(range(lo // 100, hi // 100 + 1)) if lo <= ym <= hi]


def harmonize(agg: pd.DataFrame, cfg: dict, lam: float, hier: bool = False, ctx: base.Context | None = None) -> pd.DataFrame:
    """agg = agg_monthly (sensor, cell, ym, n). Devolve a série harmonizada densa (todas as células × meses)."""
    ctx = ctx or base.Context(cfg=cfg)
    data = {s: agg.loc[agg.sensor == s, ["cell", "ym", "n"]].reset_index(drop=True) for s in agg.sensor.unique()}
    cells = sorted(set(agg.cell))
    months_all = analysis_months(cfg)
    parts = []
    for seg in cfg["timeline"]:
        s = seg["sensor"]
        months = [ym for ym in months_all if seg["from"] <= ym <= seg["to"]]
        A = base.densify(data.get(s, pd.DataFrame(columns=["cell", "ym", "n"])).query("ym in @months"), cells, months)
        if s == cfg["reference"]:
            harm = A.rename(columns={"n": "n_pred"}).astype({"n_pred": float})
        else:
            if hier:                                    # D37 (proposta): total do pai res 4, padrão do filho
                from pipeline.bridges.m1_hier import M1Hier
                run = base.build_chain(s, lambda bid: M1Hier(lam, ctx), data.get, cfg)
            else:
                run = base.build_chain(s, lambda bid: M1(lam, ctx), data.get, cfg)
            harm = run(A, months)                       # A densa → todas as células recebem previsão
        d = A.rename(columns={"n": "n_raw"}).merge(harm, on=["cell", "ym"], how="left")
        d["n_harm"] = d.pop("n_pred").fillna(0.0)
        d["src"] = s
        d["low_conf"] = np.int8(1 if seg.get("low_conf") else 0)
        parts.append(d)
    out = pd.concat(parts, ignore_index=True)
    out["lo"] = out.n_harm
    out["hi"] = out.n_harm
    out = out.astype({"ym": "int64", "n_raw": "int64", "n_harm": float})
    return out[OUT_COLS].sort_values(["cell", "ym"]).reset_index(drop=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Série harmonizada provisória (M1) → harm_series.parquet")
    ap.add_argument("--lam", type=float, help="λ do M1; sem isso usa o vencedor de validation.json (R8)")
    ap.add_argument("--agg", help="agg_monthly (padrão: inputs.agg_monthly do YAML)")
    ap.add_argument("--out", help="saída (padrão: outputs.harm_series do YAML)")
    ap.add_argument("--config", default=str(base.CONFIG))
    ap.add_argument("--hier", action="store_true", help="res 5/6: M1 hierárquico com total do pai res 4 (D37, proposta)")
    a = ap.parse_args(argv)
    cfg = base.load_config(a.config)
    lam = a.lam
    if lam is None:
        w = base.winner(cfg, "aqua_snpp")
        if not w or w.get("lam") is None or w["method"] != "M1":
            raise SystemExit("Sem λ do M1 em validation.json: use --lam 20 (provisório até o CP3).")
        lam = w["lam"]
    agg_path = Path(a.agg or cfg["inputs"]["agg_monthly"])
    out = Path(a.out or cfg["outputs"]["harm_series"])
    agg = pd.read_parquet(agg_path, columns=["sensor", "cell", "ym", "n"])
    h = harmonize(agg, cfg, lam, hier=a.hier)
    out.parent.mkdir(parents=True, exist_ok=True)
    h.to_parquet(out, index=False)

    y = h.assign(ano=h.ym // 100).groupby("ano").agg(bruto=("n_raw", "sum"), harmonizado=("n_harm", "sum"),
                                                      fonte=("src", lambda s: "/".join(dict.fromkeys(s))))
    pd.set_option("display.width", 160)
    print(f"harm_series PROVISÓRIA · {'M1 hierárquico (pai res 4)' if a.hier else 'M1'} λ={lam:g} · {agg_path} → {out}")
    print(f"{h.cell.nunique():,} células × {h.ym.nunique()} meses = {len(h):,} linhas\n")
    print(y.round(0).astype({"bruto": "int64", "harmonizado": "int64"}).to_string())
    j = y.harmonizado
    if 2011 in j and 2012 in j:
        print(f"\nEmenda 2011→2012 (Aqua harm → S-NPP): {j[2011]:,.0f} → {j[2012]:,.0f} "
              f"(bruto: {y.bruto[2011]:,} → {y.bruto[2012]:,})")


if __name__ == "__main__":
    main()

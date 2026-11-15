"""Prévia do M1 para abrir no Excel (não é a série oficial: harm_series sai na 3.4 com o vencedor do CP3).

Gera em --out (CSV padrão: vírgula separa colunas, ponto decimal):
  m1_taxa_por_mes.csv      M, k_global, a_global — taxa do Brasil por mês (Aqua → S-NPP)
  m1_taxa_por_celula.csv   cell, M, focos Aqua/S-NPP no ajuste, k, add_term — taxa de cada bairro × mês
  m1_serie_anual.csv       ano × sensor: bruto e harmonizado (escala S-NPP) — os 4 satélites numa curva

Uso (raiz do repo):
  python -m pipeline.bridges.m1_preview --lam 20
  python -m pipeline.bridges.m1_preview --lam 20 --agg data/interim/pantanal/agg_monthly.parquet --out data/interim/pantanal
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pipeline.bridges import base
from pipeline.bridges.m1 import M1

SENSORS = ["TERRA", "AQUA", "SNPP", "N20"]


def preview(agg: pd.DataFrame, cfg: dict, lam: float) -> dict[str, pd.DataFrame]:
    ctx = base.Context(cfg=cfg)
    data = {s: agg[agg.sensor == s][["cell", "ym", "n"]].reset_index(drop=True) for s in SENSORS}
    m = M1(lam, ctx).fit(data["AQUA"], data["SNPP"], base.fit_years(cfg, "aqua_snpp"))
    taxa_mes = m.global_table()
    taxa_cel = m.params().rename(columns={"sa_pos": "aqua_ajuste", "sb_pos": "snpp_ajuste",
                                          "n_zero": "meses_aqua_zero", "sb_zero": "snpp_quando_aqua_zero"})
    cnt = ["aqua_ajuste", "snpp_ajuste", "meses_aqua_zero", "snpp_quando_aqua_zero"]
    taxa_cel = taxa_cel.astype({c: "int64" for c in cnt}).round({"k": 4, "add_term": 4})
    taxa_mes = taxa_mes.round(4)

    rows = []
    for s in SENSORS:
        A = data[s]
        if A.empty:
            continue
        lo, hi = cfg["sensor_years"][s]
        months = [ym for ym in base.months_of(range(lo, hi + 1)) if cfg["analysis_period"][0] <= ym <= cfg["analysis_period"][1]]
        if s == cfg["reference"]:
            harm = A[A.ym.isin(months)].rename(columns={"n": "n_pred"})
        else:
            run = base.build_chain(s, lambda bid: M1(lam, ctx), data.get, cfg)
            harm = run(A, months)
        raw = A[A.ym.isin(months)]
        y = pd.DataFrame({"bruto": raw.groupby(raw.ym // 100).n.sum(),
                          "harmonizado": harm.groupby(harm.ym // 100).n_pred.sum()})
        rows.append(y.assign(sensor=s))
    serie = pd.concat(rows).reset_index(names="ano")
    serie = serie.pivot(index="ano", columns="sensor", values=["bruto", "harmonizado"])
    serie.columns = [f"{s}_{kind}" for kind, s in serie.columns]
    order = [f"{s}_{k}" for k in ("bruto", "harmonizado") for s in SENSORS if f"{s}_{k}" in serie.columns]
    serie = serie[order].round(0).astype("Int64")
    return {"m1_taxa_por_mes": taxa_mes, "m1_taxa_por_celula": taxa_cel, "m1_serie_anual": serie.reset_index()}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Prévia do M1 em CSV para o Excel.")
    ap.add_argument("--lam", type=float, default=20)
    ap.add_argument("--agg", help="agg_monthly (padrão: inputs.agg_monthly do YAML)")
    ap.add_argument("--out", default="data/interim")
    ap.add_argument("--config", default=str(base.CONFIG))
    a = ap.parse_args(argv)
    cfg = base.load_config(a.config)
    agg_path = Path(a.agg or cfg["inputs"]["agg_monthly"])
    agg = pd.read_parquet(agg_path, columns=["sensor", "cell", "ym", "n"])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tabs = preview(agg, cfg, a.lam)
    for name, df in tabs.items():
        df.to_csv(out / f"{name}.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"Prévia M1 · λ={a.lam:g} · {agg_path} → {out / 'm1_*.csv'} (abrir no Excel)\n")
    print("Série anual (focos em células de 2 km por passagem; harmonizado = escala S-NPP):")
    print(tabs["m1_serie_anual"].to_string(index=False))
    print("\nObs.: Aqua 2020 inclui ago–set (pane do Aqua); a série oficial (3.4) segue a linha do tempo Terra → Aqua → S-NPP.")


if __name__ == "__main__":
    main()

"""M1 — razão com encolhimento por célula × mês do calendário (Guia 48h v2 §3.2, D32, D33). Dona: Melissa.

    k(c,M) = (ΣB⁺ + λ·k_global(M)) / (ΣA⁺ + λ)     ⁺ = meses com A > 0 nos anos de ajuste (D32)
    a(c,M) = média de B nos meses com A = 0         (termo aditivo: fogo que só o sensor novo vê)
    pred(c,ym) = k(c,M)·A(c,ym)  se A > 0
               = a(c,M)          se A = 0

Prior (D33, sem bioma): k_global(M) = ΣB⁺/ΣA⁺ de todas as células no mês M; a_global(M) = média de B nos
meses com A = 0 de todas as células. Fallbacks: k_global(M) sem dados → k_global (todos os meses) → 1,0;
a_global(M) sem meses A = 0 → 0. Célula sem ΣA⁺ (ou nova) → k = k_global(M); sem meses A = 0 → a = a_global(M).

Contrato: pipeline/bridges/base.py (R1–R8). Tabela de ajuste sempre via base.paired().

Uso (raiz do repo):
    python -m pipeline.bridges.m1 --bridge aqua_snpp --lam 20
    python -m pipeline.bridges.m1 --bridge aqua_snpp --lam 20 --agg data/interim/agg_monthly_pantanal.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.bridges import base

PARAM_COLS = ["cell", "M", "sa_pos", "sb_pos", "n_zero", "sb_zero", "k", "add_term"]


class M1:
    name = "M1"

    def __init__(self, lam: float, ctx: base.Context):
        assert lam >= 0, "λ ≥ 0"
        self.lam = float(lam)
        self.ctx = ctx

    # ---------- ajuste ----------
    def fit(self, A: pd.DataFrame, B: pd.DataFrame, years: list[int]) -> "M1":
        t = base.paired(A, B, years, self.ctx.cfg)              # R1–R3: zero-fill, sem pane, 1 cópia por repetição
        t = t.assign(M=(t.ym % 100).astype("int64"), pos=t.a > 0)
        t["a_pos"] = np.where(t.pos, t.a, 0)
        t["b_pos"] = np.where(t.pos, t.b, 0)
        t["b_zero"] = np.where(t.pos, 0, t.b)
        t["zero"] = (~t.pos).astype("int64")

        # prior global (Brasil/área inteira, mês do calendário) — D33
        g = t.groupby("M")[["a_pos", "b_pos", "zero", "b_zero"]].sum().reindex(range(1, 13), fill_value=0)
        k_all = g.b_pos.sum() / g.a_pos.sum() if g.a_pos.sum() > 0 else 1.0
        self.k_global_ = pd.Series(np.where(g.a_pos > 0, g.b_pos / g.a_pos.where(g.a_pos > 0, 1), k_all),
                                   index=g.index, name="k_global").astype(float)
        self.a_global_ = pd.Series(np.where(g.zero > 0, g.b_zero / g.zero.where(g.zero > 0, 1), 0.0),
                                   index=g.index, name="a_global").astype(float)
        self.k_all_ = float(k_all)

        # por célula × M
        p = (t.groupby(["cell", "M"])[["a_pos", "b_pos", "zero", "b_zero"]].sum().reset_index()
               .rename(columns={"a_pos": "sa_pos", "b_pos": "sb_pos", "zero": "n_zero", "b_zero": "sb_zero"}))
        kg = self.k_global_.reindex(p.M).to_numpy()
        ag = self.a_global_.reindex(p.M).to_numpy()
        den = p.sa_pos + self.lam
        p["k"] = np.where(den > 0, (p.sb_pos + self.lam * kg) / den.where(den > 0, 1), kg).astype(float)
        p["add_term"] = np.where(p.n_zero > 0, p.sb_zero / p.n_zero.where(p.n_zero > 0, 1), ag).astype(float)
        self.params_ = p[PARAM_COLS].astype({"sa_pos": float, "sb_pos": float, "sb_zero": float})
        self.cells_ = set(p.cell)
        self.years_ = list(years)
        return self

    # ---------- previsão ----------
    def transform(self, A: pd.DataFrame, months: list[int] | None = None) -> pd.DataFrame:
        months = base.default_months(A, months)
        d = base.densify(A[["cell", "ym", "n"]], self.cells_ | set(A.cell), months)   # R5: só n
        M = (d.ym % 100).astype("int64")
        par = self.params_.set_index(["cell", "M"])[["k", "add_term"]]
        key = pd.MultiIndex.from_arrays([d.cell, M])
        k = par.k.reindex(key).to_numpy()
        a = par["add_term"].reindex(key).to_numpy()
        k = np.where(np.isnan(k), self.k_global_.reindex(M).to_numpy(), k)          # célula/mês sem ajuste
        a = np.where(np.isnan(a), self.a_global_.reindex(M).to_numpy(), a)
        n = d.n.to_numpy(dtype=float)
        pred = np.where(n > 0, k * n, a)
        return pd.DataFrame({"cell": d.cell.to_numpy(), "ym": d.ym.astype("int64").to_numpy(),
                             "n_pred": pred.astype(float)})

    # ---------- inspeção ----------
    def params(self) -> pd.DataFrame:
        """cell, M, somas, k, add — para o Method e para depuração."""
        return self.params_.copy()

    def global_table(self) -> pd.DataFrame:
        return pd.DataFrame({"M": range(1, 13), "k_global": self.k_global_.to_numpy(),
                             "a_global": self.a_global_.to_numpy()})


# ---------- CLI ----------
def _load_agg(path: Path, sensors: list[str]) -> dict[str, pd.DataFrame]:
    df = pd.read_parquet(path, columns=["sensor", "cell", "ym", "n"])
    df = df[df.sensor.isin(sensors)]
    return {s: df[df.sensor == s][["cell", "ym", "n"]].reset_index(drop=True) for s in sensors}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Ajusta o M1 de uma ponte e grava os parâmetros.")
    ap.add_argument("--bridge", default="aqua_snpp")
    ap.add_argument("--lam", type=float, help="λ; sem isso usa o vencedor de validation.json (R8)")
    ap.add_argument("--agg", help="agg_monthly (padrão: inputs.agg_monthly do YAML)")
    ap.add_argument("--out", default="data/interim")
    ap.add_argument("--config", default=str(base.CONFIG))
    a = ap.parse_args(argv)

    cfg = base.load_config(a.config)
    br = cfg["bridges_by_id"][a.bridge]
    lam = a.lam
    if lam is None:
        w = base.winner(cfg, a.bridge)
        if not w or w.get("lam") is None:
            raise SystemExit("Sem λ: validation.json ainda não tem vencedor (CP3). Use --lam 20 só para conferência.")
        lam = w["lam"]

    agg_path = Path(a.agg or cfg["inputs"]["agg_monthly"])
    data = _load_agg(agg_path, [br["from"], br["to"]])
    A, B = data[br["from"]], data[br["to"]]
    fy, ty = base.fit_years(cfg, a.bridge), base.test_years(cfg, a.bridge)
    m = M1(lam, base.Context(cfg=cfg)).fit(A, B, fy)

    out = Path(a.out) / f"m1_params_{a.bridge}_lam{lam:g}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    m.params().to_parquet(out, index=False)

    pd.set_option("display.width", 140)
    print(f"M1 {a.bridge} ({br['from']}→{br['to']}) · λ={lam:g} · fit {fy[0]}–{fy[-1]} · {len(m.cells_)} células · {agg_path}")
    print(m.global_table().round(3).to_string(index=False))
    print(f"k_global (todos os meses) = {m.k_all_:.3f} · parâmetros → {out}")

    for label, years in (("ajuste", fy), ("teste", ty)):
        if not years:
            continue
        months = base.scoring_months(cfg, years)
        Ay, By = A[A.ym.isin(months)], B[B.ym.isin(months)]
        pred = m.transform(Ay, months)
        s_pred, s_a, s_b = pred.n_pred.sum(), Ay.n.sum(), By.n.sum()
        print(f"{label} {years[0]}–{years[-1]}: ΣA={s_a:,.0f} · ΣB={s_b:,.0f} · Σpred={s_pred:,.0f} "
              f"· Σpred/ΣB={s_pred / max(s_b, 1):.3f}  (conferência; nota oficial = Samuel)")


if __name__ == "__main__":
    main()

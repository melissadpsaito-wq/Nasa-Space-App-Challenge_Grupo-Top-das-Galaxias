"""M2 — limiar físico de FRP + resíduo com encolhimento (Guia 48h v2 §3.3, D13, D26, D33). Dona: Melissa.

Etapa 1 — limiar τ por estrato s = trimestre × dia/noite (8 estratos, Brasil inteiro, D33), nos anos de ajuste:
    τ_s = FRP tal que #(passagens S-NPP em s com frp_max ≥ τ_s) ≈ N_Aqua,s     (= quantil 1 − N_Aqua,s/N_SNPP,s)
    forte = célula-passagem S-NPP com frp_max ≥ τ_s  (≈ o que o Aqua veria)   fraco = o resto

Etapa 2 — por célula × mês do calendário M, só meses com A > 0 (⁺, D32):
    k_f(c,M) = (ΣBforte⁺ + λ·kf_global(M)) / (ΣA⁺ + λ)            forte por detecção Aqua (≈ 1 se τ acerta)
    r(c,M)   = (ΣBfraco⁺ + λ·r_global(M))  / (ΣBforte⁺ + λ)        fogo fraco por fogo forte
    a(c,M)   = média de B nos meses com A = 0                       termo aditivo (igual ao M1)
    pred(c,ym) = k_f(c,M)·A·(1 + r(c,M))  se A > 0  ·  a(c,M)  se A = 0

Leitura: com λ = 0, k_f·(1+r) = ΣB⁺/ΣA⁺ = k do M1 (identidade). O M2 só difere do M1 no encolhimento, feito
em duas partes com significado físico (detecção dos fogos fortes × proporção de fogos fracos). Com λ → ∞,
k_f·(1+r) → kf_global·(1+r_global) = k_global do M1. O τ não entra no transform (R5: só usa A.n).

Contrato: base.py (R1–R8). Passagens via ctx.passes (base.passes_reader): o M2 é a única ponte que as lê.
Escala: as passagens trazem `cell` na resolução do grid2km_pass (res 4). Para rodar em outra resolução,
o grid2km_pass tem de ter a mesma `cell` do agg_monthly (fit falha com mensagem se não bater).

Uso (raiz do repo):
    python -m pipeline.bridges.m2 --bridge aqua_snpp --lam 20            # τ por estrato + parâmetros
    python -m pipeline.bridges.m2 --bridge aqua_snpp --eval              # bruto × taxa única × M1 × M2
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.bridges import base
from pipeline.bridges.m1 import M1, _Global, _load_agg, _Raw, score

PARAM_COLS = ["cell", "M", "sa_pos", "sbf_pos", "sbw_pos", "n_zero", "sb_zero", "k_f", "r", "k", "add_term"]
TAU_COLS = ["season", "daynight", "n_aqua", "n_snpp", "ratio", "tau", "n_strong", "ratio_after_tau"]


def tau_weighted(frp: np.ndarray, w: np.ndarray, n_target: float) -> float:
    """τ tal que Σw(frp ≥ τ) ≈ n_target. Mesma regra do check_method (sem pesos = tau_equal_counts).

    n_target ≤ 0 → +inf (nenhum forte) · n_target ≥ Σw → menor FRP (todos fortes).
    """
    frp, w = np.asarray(frp, float), np.asarray(w, float)
    if len(frp) == 0 or n_target <= 0:
        return float("inf")
    o = np.argsort(-frp, kind="stable")
    s, cw = frp[o], np.cumsum(w[o])
    if n_target >= cw[-1]:
        return float(s[-1])
    return float(s[int(np.searchsorted(cw, n_target))])


class M2:
    name = "M2"

    def __init__(self, lam: float, ctx: base.Context, bridge: str = "aqua_snpp"):
        assert lam >= 0, "λ ≥ 0"
        assert ctx.passes is not None, "M2 precisa de ctx.passes = base.passes_reader(cfg) (grid2km_pass)"
        self.lam, self.ctx, self.bridge = float(lam), ctx, bridge
        self.br = ctx.cfg["bridges_by_id"][bridge]
        assert "M2" in self.br["methods"], f"{bridge}: M2 não está em methods do YAML"

    # ---------- etapa 1: τ por estrato ----------
    def _tau(self, pa: pd.DataFrame, pb: pd.DataFrame, reps: Counter) -> pd.DataFrame:
        wa = (pa.ym // 100).map(reps).to_numpy(float)
        wb = (pb.ym // 100).map(reps).to_numpy(float)
        rows = []
        for s in self.ctx.cfg["seasons"]:
            for dn in ("D", "N"):
                ma = ((pa.season == s) & (pa.daynight == dn)).to_numpy()
                mb = ((pb.season == s) & (pb.daynight == dn)).to_numpy()
                na, nb = wa[ma].sum(), wb[mb].sum()
                tau = tau_weighted(pb.frp_max.to_numpy()[mb], wb[mb], na)
                ns = wb[mb][pb.frp_max.to_numpy()[mb] >= tau].sum()
                rows.append({"season": s, "daynight": dn, "n_aqua": na, "n_snpp": nb, "ratio": nb / max(na, 1),
                             "tau": tau, "n_strong": ns, "ratio_after_tau": ns / max(na, 1)})
        return pd.DataFrame(rows, columns=TAU_COLS)

    def _strong(self, pb: pd.DataFrame) -> pd.DataFrame:
        """cell, ym, bs = nº de células-passagem S-NPP fortes (frp_max ≥ τ do estrato)."""
        tau = self.tau_.set_index(["season", "daynight"]).tau
        t = tau.reindex(pd.MultiIndex.from_arrays([pb.season, pb.daynight])).to_numpy()
        strong = pb.frp_max.to_numpy() >= t
        return pb[strong].groupby(["cell", "ym"]).size().rename("bs").reset_index()

    # ---------- ajuste ----------
    def fit(self, A: pd.DataFrame, B: pd.DataFrame, years: list[int]) -> "M2":
        cfg, reps = self.ctx.cfg, Counter(years)
        uniq = sorted(reps)
        pa = self.ctx.passes(self.br["from"], uniq)                       # meses da pane já saem (R3)
        pb = self.ctx.passes(self.br["to"], uniq)
        self.tau_ = self._tau(pa, pb, reps)

        t = base.paired(A, B, years, cfg)                                 # R1–R3: zero-fill, pane fora, bootstrap
        bs = self._strong(pb)
        if len(t) and len(bs):
            hit = t.loc[t.b > 0, "cell"].isin(set(bs.cell)).mean()
            assert hit > 0.5, ("M2: células do grid2km_pass não batem com as do agg_monthly "
                               f"({hit:.0%}); use passagens na mesma resolução H3 (D36)")
        t = t.merge(bs, on=["cell", "ym"], how="left").fillna({"bs": 0})
        self.mismatch_ = float((t.bs - t.b).clip(lower=0).sum() / max(t.b.sum(), 1))   # conservação passagens × agg
        t["bs"] = np.minimum(t.bs, t.b)                                   # nunca mais fortes que o total
        t = t.assign(M=(t.ym % 100).astype("int64"), pos=t.a > 0)
        t["a_pos"] = np.where(t.pos, t.a, 0)
        t["bf_pos"] = np.where(t.pos, t.bs, 0)
        t["bw_pos"] = np.where(t.pos, t.b - t.bs, 0)
        t["b_zero"] = np.where(t.pos, 0, t.b)
        t["zero"] = (~t.pos).astype("int64")
        cols = ["a_pos", "bf_pos", "bw_pos", "zero", "b_zero"]

        # prior global (mês do calendário, D33), com os mesmos fallbacks do M1
        g = t.groupby("M")[cols].sum().reindex(range(1, 13), fill_value=0)
        kf_all = g.bf_pos.sum() / g.a_pos.sum() if g.a_pos.sum() > 0 else 1.0
        r_all = g.bw_pos.sum() / g.bf_pos.sum() if g.bf_pos.sum() > 0 else 0.0
        self.kf_global_ = pd.Series(np.where(g.a_pos > 0, g.bf_pos / g.a_pos.where(g.a_pos > 0, 1), kf_all),
                                    index=g.index, name="kf_global").astype(float)
        self.r_global_ = pd.Series(np.where(g.bf_pos > 0, g.bw_pos / g.bf_pos.where(g.bf_pos > 0, 1), r_all),
                                   index=g.index, name="r_global").astype(float)
        self.a_global_ = pd.Series(np.where(g.zero > 0, g.b_zero / g.zero.where(g.zero > 0, 1), 0.0),
                                   index=g.index, name="a_global").astype(float)

        p = (t.groupby(["cell", "M"])[cols].sum().reset_index()
               .rename(columns={"a_pos": "sa_pos", "bf_pos": "sbf_pos", "bw_pos": "sbw_pos",
                                "zero": "n_zero", "b_zero": "sb_zero"}))
        kfg = self.kf_global_.reindex(p.M).to_numpy()
        rg = self.r_global_.reindex(p.M).to_numpy()
        ag = self.a_global_.reindex(p.M).to_numpy()
        lam = self.lam
        den_k, den_r = p.sa_pos + lam, p.sbf_pos + lam
        p["k_f"] = np.where(den_k > 0, (p.sbf_pos + lam * kfg) / den_k.where(den_k > 0, 1), kfg).astype(float)
        p["r"] = np.where(den_r > 0, (p.sbw_pos + lam * rg) / den_r.where(den_r > 0, 1), rg).astype(float)
        p["k"] = p.k_f * (1 + p.r)
        p["add_term"] = np.where(p.n_zero > 0, p.sb_zero / p.n_zero.where(p.n_zero > 0, 1), ag).astype(float)
        self.params_ = p[PARAM_COLS].astype({c: float for c in ["sa_pos", "sbf_pos", "sbw_pos", "sb_zero"]})
        self.cells_ = set(p.cell)
        self.years_ = list(years)
        return self

    # ---------- previsão (igual ao M1, com k = k_f·(1+r)) ----------
    def transform(self, A: pd.DataFrame, months: list[int] | None = None) -> pd.DataFrame:
        months = base.default_months(A, months)
        d = base.densify(A[["cell", "ym", "n"]], self.cells_ | set(A.cell), months)   # R5: só n
        M = (d.ym % 100).astype("int64")
        par = self.params_.set_index(["cell", "M"])[["k", "add_term"]]
        key = pd.MultiIndex.from_arrays([d.cell, M])
        k = par.k.reindex(key).to_numpy()
        a = par["add_term"].reindex(key).to_numpy()
        kg = (self.kf_global_ * (1 + self.r_global_)).reindex(M).to_numpy()
        k = np.where(np.isnan(k), kg, k)                                                # célula/mês sem ajuste
        a = np.where(np.isnan(a), self.a_global_.reindex(M).to_numpy(), a)
        n = d.n.to_numpy(dtype=float)
        pred = np.where(n > 0, k * n, a)
        return pd.DataFrame({"cell": d.cell.to_numpy(), "ym": d.ym.astype("int64").to_numpy(),
                             "n_pred": pred.astype(float)})

    # ---------- inspeção ----------
    def params(self) -> pd.DataFrame:
        return self.params_.copy()

    def tau_table(self) -> pd.DataFrame:
        """τ por trimestre × dia/noite — vai para a página Method (resultado físico)."""
        return self.tau_.copy()

    def global_table(self) -> pd.DataFrame:
        return pd.DataFrame({"M": range(1, 13), "kf_global": self.kf_global_.to_numpy(),
                             "r_global": self.r_global_.to_numpy(),
                             "k_global": (self.kf_global_ * (1 + self.r_global_)).to_numpy(),
                             "a_global": self.a_global_.to_numpy()})


# ---------- conferência (a nota oficial é o validation.json do Samuel) ----------
def _collect_all(model, A, B, fit_years, eval_years, cfg) -> pd.DataFrame:
    """Ajusta em fit_years e prevê eval_years em TODAS as célula-mês: cell, ym, a, real, n_pred.

    Próprio do M2 (não usa funções internas do m1.py, que mudam entre versões)."""
    model.fit(A, B, fit_years)
    months = base.scoring_months(cfg, eval_years)
    Ay, By = A[A.ym.isin(months)], B[B.ym.isin(months)]
    pred = model.transform(Ay, months)
    cells = set(pred.cell) | set(By.cell)
    real = base.densify(By, cells, months).rename(columns={"n": "real"})
    a = base.densify(Ay, cells, months).rename(columns={"n": "a"})
    return real.merge(a, on=["cell", "ym"]).merge(pred, on=["cell", "ym"], how="left").fillna({"n_pred": 0.0})


def _score_split(d: pd.DataFrame) -> dict:
    """Métricas em célula-mês ativas (A > 0 ou B > 0), como `m1 --eval`; total_ratio em todas."""
    act = d[(d.a > 0) | (d.real > 0)]
    return {**score(act.n_pred.to_numpy(), act.real.to_numpy()),
            "total_ratio": float(d.n_pred.sum() / max(d.real.sum(), 1))}


def evaluate(A, B, cfg, bridge_id, lams, passes) -> pd.DataFrame:
    """Bruto × taxa única × M1(λ) × M2(λ): teste do YAML e LOYO no ajuste (mesma regra do m1 --eval)."""
    ctx = base.Context(cfg=cfg, passes=passes)
    fy, ty = base.fit_years(cfg, bridge_id), base.test_years(cfg, bridge_id)
    makers = {"raw": lambda: _Raw(ctx), "global": lambda: _Global(ctx),
              **{f"M1 λ={lam:g}": (lambda lam=lam: M1(lam, ctx)) for lam in lams},
              **{f"M2 λ={lam:g}": (lambda lam=lam: M2(lam, ctx, bridge_id)) for lam in lams}}
    rows = []
    for name, make in makers.items():
        if ty:
            rows.append({"método": name, "split": f"teste {ty[0]}–{ty[-1]}",
                         **_score_split(_collect_all(make(), A, B, fy, ty, cfg))})
        loyo = pd.concat([_collect_all(make(), A, B, [t for t in fy if t != y], [y], cfg) for y in fy])
        rows.append({"método": name, "split": f"LOYO {fy[0]}–{fy[-1]}", **_score_split(loyo)})
    return pd.DataFrame(rows)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Limiar de FRP por estrato + M2 (Guia §3.3).")
    ap.add_argument("--bridge", default="aqua_snpp")
    ap.add_argument("--lam", type=float, help="λ; sem isso usa o vencedor de validation.json (R8)")
    ap.add_argument("--agg", help="agg_monthly (padrão: inputs.agg_monthly do YAML)")
    ap.add_argument("--passes", help="grid2km_pass na MESMA resolução do --agg (padrão: inputs.grid2km_pass)")
    ap.add_argument("--out", default="data/interim")
    ap.add_argument("--config", default=str(base.CONFIG))
    ap.add_argument("--eval", action="store_true", help="bruto × taxa única × M1 × M2 (λ = 0 + lambda_grid)")
    a = ap.parse_args(argv)

    cfg = base.load_config(a.config)
    br = cfg["bridges_by_id"][a.bridge]
    agg_path = Path(a.agg or cfg["inputs"]["agg_monthly"])
    passes = base.passes_reader(cfg, a.passes)
    data = _load_agg(agg_path, [br["from"], br["to"]])
    A, B = data[br["from"]], data[br["to"]]
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 160)

    if a.eval:
        r = evaluate(A, B, cfg, a.bridge, [0, *cfg["lambda_grid"]], passes)
        print(f"Conferência {a.bridge} · {agg_path} · métricas em célula-mês ativas (A > 0 ou B > 0); "
              f"total_ratio em todas; menor consistency = melhor\n")
        for split, g in r.groupby("split", sort=False):
            print(f"{split}:\n" + g.drop(columns="split").round(3).to_string(index=False) + "\n")
        out = out_dir / f"m2_eval_{a.bridge}.csv"
        r.to_csv(out, index=False)
        print(f"→ {out}  (conferência; a nota oficial é o validation.json do Samuel)")
        return

    lam = a.lam
    if lam is None:
        w = base.winner(cfg, a.bridge)
        if not w or w.get("lam") is None:
            raise SystemExit("Sem λ: validation.json ainda não tem vencedor (CP3). Use --lam 20 só para conferência.")
        lam = w["lam"]

    fy, ty = base.fit_years(cfg, a.bridge), base.test_years(cfg, a.bridge)
    m = M2(lam, base.Context(cfg=cfg, passes=passes), a.bridge).fit(A, B, fy)
    tau = m.tau_table()
    tau.to_csv(out_dir / f"m2_tau_{a.bridge}.csv", index=False)
    m.params().to_parquet(out_dir / f"m2_params_{a.bridge}_lam{lam:g}.parquet", index=False)

    print(f"M2 {a.bridge} ({br['from']}→{br['to']}) · λ={lam:g} · fit {fy[0]}–{fy[-1]} · {len(m.cells_)} células · {agg_path}")
    print(f"\nτ por trimestre × dia/noite (MW) — tabela do Method:\n" + tau.round(2).to_string(index=False))
    print(f"\nPrior global por mês:\n" + m.global_table().round(3).to_string(index=False))
    print(f"\nConservação passagens × agg: fortes acima de B em {m.mismatch_:.4%} de ΣB (esperado 0)")
    for label, years in (("ajuste", fy), ("teste", ty)):
        if not years:
            continue
        months = base.scoring_months(cfg, years)
        Ay, By = A[A.ym.isin(months)], B[B.ym.isin(months)]
        s_pred = m.transform(Ay, months).n_pred.sum()
        print(f"{label} {years[0]}–{years[-1]}: ΣA={Ay.n.sum():,.0f} · ΣB={By.n.sum():,.0f} · Σpred={s_pred:,.0f} "
              f"· Σpred/ΣB={s_pred / max(By.n.sum(), 1):.3f}")
    print(f"→ {out_dir}/m2_tau_{a.bridge}.csv · m2_params_{a.bridge}_lam{lam:g}.parquet")


if __name__ == "__main__":
    main()

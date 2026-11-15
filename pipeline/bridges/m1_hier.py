"""M1 hierárquico (proposta D37, teste do D36): detalhe da res 5 com a calibração da res 4.

Ideia ("raking"): o M1 na célula-pai (res 4) acerta o TOTAL (Brasil: Σpred/ΣB 0,99, R² log 0,64); o M1 na
célula-filha (res 5) dá o PADRÃO espacial, mas erra o total (0,92) porque cada filha tem poucos focos.
  1. pred_pai(P, ym)    = M1(res 4) aplicado às contagens somadas dos filhos
  2. pred_filho(c, ym)  = M1(res 5) — só como peso
  3. final(c, ym)       = pred_pai(P, ym) · pred_filho(c, ym) / Σ_{filhos de P} pred_filho
     (se Σ pred_filho = 0: divide pela participação histórica do filho nos focos B do pai; sem histórico: igual)
Σ dos filhos = previsão do pai, sempre. Mesma interface Bridge (R1–R8); célula da saída = célula do filho.

Pai: `ctx.extra["parent"]` (função célula → pai) ou h3.cell_to_parent(cell, parent_res).
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from pipeline.bridges import base
from pipeline.bridges.m1 import M1


def h3_parent(res: int) -> Callable[[str], str]:
    import h3
    return lambda c: h3.cell_to_parent(c, res)


class M1Hier:
    name = "M1H"

    def __init__(self, lam: float, ctx: base.Context, parent_res: int = 4):
        self.lam, self.ctx = float(lam), ctx
        self.parent = ctx.extra.get("parent") or h3_parent(parent_res)
        self._cache: dict[str, str] = {}

    def _p(self, cells) -> np.ndarray:
        out = []
        for c in cells:
            p = self._cache.get(c)
            if p is None:
                p = self._cache[c] = self.parent(c)
            out.append(p)
        return np.array(out, dtype=object)

    def _up(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df[["cell", "ym", "n"]].assign(cell=self._p(df.cell))
        return d.groupby(["cell", "ym"], as_index=False).n.sum()

    def fit(self, A: pd.DataFrame, B: pd.DataFrame, years: list[int]) -> "M1Hier":
        self.child_ = M1(self.lam, self.ctx).fit(A, B, years)
        self.par_ = M1(self.lam, self.ctx).fit(self._up(A), self._up(B), years)
        t = base.paired(A, B, years, self.ctx.cfg)                     # participação histórica do filho no pai
        sb = t.groupby("cell").b.sum()
        sp = pd.Series(sb.values, index=self._p(sb.index)).groupby(level=0).transform("sum")
        self.share_ = pd.Series(np.where(sp.values > 0, sb.values / np.where(sp.values > 0, sp.values, 1), np.nan),
                                index=sb.index)
        return self

    def transform(self, A: pd.DataFrame, months: list[int] | None = None) -> pd.DataFrame:
        months = base.default_months(A, months)
        A = A[["cell", "ym", "n"]]
        ch = self.child_.transform(A, months)                           # filhos: fit ∪ A
        ch["P"] = self._p(ch.cell)
        par = self.par_.transform(self._up(A), months).rename(columns={"cell": "P", "n_pred": "tot"})
        d = ch.merge(par, on=["P", "ym"], how="left").fillna({"tot": 0.0})
        g = d.groupby(["P", "ym"])
        s = g.n_pred.transform("sum")
        share = self.share_.reindex(d.cell).to_numpy()
        k = g.cell.transform("size").to_numpy()
        share = np.where(np.isnan(share), 1.0 / k, share)
        ssum = pd.Series(share).groupby([d.P.to_numpy(), d.ym.to_numpy()]).transform("sum").to_numpy()
        w = np.where(s.to_numpy() > 0, d.n_pred.to_numpy() / np.where(s.to_numpy() > 0, s.to_numpy(), 1),
                     share / np.where(ssum > 0, ssum, 1))
        return pd.DataFrame({"cell": d.cell.to_numpy(), "ym": d.ym.astype("int64").to_numpy(),
                             "n_pred": (d.tot.to_numpy() * w).astype(float)})

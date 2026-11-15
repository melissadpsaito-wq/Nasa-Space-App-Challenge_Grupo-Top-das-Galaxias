"""M1 hierárquico (D37 proposta): soma dos filhos = pai; contrato Bridge; padrão espacial do filho."""
import numpy as np
import pandas as pd
import pytest

from pipeline.bridges import base
from pipeline.bridges.m1 import M1
from pipeline.bridges.m1_hier import M1Hier


@pytest.fixture(scope="module")
def cfg():
    return base.load_config()


def parent(c):            # filhos "P1.a", "P1.b" → pai "P1"
    return c.split(".")[0]


def ctx(cfg):
    return base.Context(cfg=cfg, extra={"parent": parent})


def synth(seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for P in ["P1", "P2", "P3"]:
        for ch, w in [("a", 0.6), ("b", 0.3), ("c", 0.1)]:
            for ym in base.months_of(range(2012, 2022)):
                lam_a = 3 * w * (1 + 5 * (ym % 100 in (8, 9, 10)))
                a = rng.poisson(lam_a)
                rows += [("AQUA", f"{P}.{ch}", ym, a), ("SNPP", f"{P}.{ch}", ym, rng.poisson(4 * lam_a + 0.3 * w))]
    df = pd.DataFrame(rows, columns=["sensor", "cell", "ym", "n"])
    df = df[df.n > 0]
    return df[df.sensor == "AQUA"][["cell", "ym", "n"]], df[df.sensor == "SNPP"][["cell", "ym", "n"]]


def test_children_sum_to_parent(cfg):
    A, B = synth()
    fy = list(range(2012, 2020))
    h = M1Hier(20, ctx(cfg)).fit(A, B, fy)
    months = base.months_of([2020, 2021])
    out = h.transform(A[A.ym // 100 >= 2020], months)
    up = out.assign(P=out.cell.map(parent)).groupby(["P", "ym"]).n_pred.sum()
    Ap = A.assign(cell=A.cell.map(parent)).groupby(["cell", "ym"], as_index=False).n.sum()
    Bp = B.assign(cell=B.cell.map(parent)).groupby(["cell", "ym"], as_index=False).n.sum()
    ref = M1(20, base.Context(cfg=cfg)).fit(Ap, Bp, fy).transform(Ap[Ap.ym // 100 >= 2020], months)
    ref = ref.set_index(["cell", "ym"]).n_pred
    np.testing.assert_allclose(up.loc[ref.index].to_numpy(), ref.to_numpy(), rtol=1e-9)


def test_spatial_pattern_kept(cfg):
    A, B = synth()
    h = M1Hier(20, ctx(cfg)).fit(A, B, list(range(2012, 2020)))
    out = h.transform(A[A.ym // 100 >= 2020], base.months_of([2020, 2021]))
    tot = out.assign(ch=out.cell.str[-1]).groupby("ch").n_pred.sum()
    assert tot["a"] > tot["b"] > tot["c"]


def test_bridge_contract(cfg):
    A, B = synth()
    A_new = A[A.ym // 100 == 2015].assign(ym=lambda d: d.ym - 1000).reset_index(drop=True)   # 2005, mesmas células
    A_new = pd.concat([A_new, pd.DataFrame({"cell": ["P9.a"], "ym": [200508], "n": [3]})], ignore_index=True)
    base.check_bridge(M1Hier(20, ctx(cfg)), A.reset_index(drop=True), B.reset_index(drop=True),
                      base.fit_years(cfg, "aqua_snpp"), A_new, cfg)

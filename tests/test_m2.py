"""M2 — limiar de FRP por trimestre × dia/noite + resíduo com encolhimento (Guia §3.3). Dados sintéticos."""
from collections import Counter

import numpy as np
import pandas as pd
import pytest

from pipeline.bridges import base
from pipeline.bridges.check_method import tau_equal_counts
from pipeline.bridges.m1 import M1
from pipeline.bridges.m2 import M2, tau_weighted

FIT = list(range(2012, 2020))


@pytest.fixture(scope="module")
def cfg():
    return base.load_config()


def world(cfg, years=FIT, cells=("c1", "c2", "c3", "c4"), tau_true=10.0, seed=0):
    """Fogos com FRP lognormal; S-NPP vê todos, Aqua só os de FRP ≥ tau_true. Devolve A, B (agg) e passagens."""
    rng = np.random.default_rng(seed)
    rows = []
    for c in cells:
        for ym in base.months_of(years):
            lam = 3 + 25 * (ym % 100 in (8, 9, 10))
            for _ in range(rng.poisson(lam)):
                rows.append((c, ym, "N" if rng.random() < 0.3 else "D", float(rng.lognormal(2.0, 0.9))))
    snpp = pd.DataFrame(rows, columns=["cell", "ym", "daynight", "frp_max"])
    aqua = snpp[snpp.frp_max >= tau_true].reset_index(drop=True)
    return agg(aqua), agg(snpp), {"AQUA": aqua, "SNPP": snpp}


def agg(p):
    return p.groupby(["cell", "ym"]).size().rename("n").reset_index()


def reader(cfg, P):
    ex = base.excluded_months(cfg)

    def read(sensor, years):
        months = [ym for ym in base.months_of(years) if ym not in ex]
        d = P[sensor]
        d = d[d.ym.isin(months)].reset_index(drop=True)
        return d.assign(season=base.season_of(d.ym, cfg))
    return read


def test_tau_weighted_matches_check_method():
    x = np.array([3.0, 9.0, 1.0, 7.0, 5.0])
    for n in range(1, 6):
        assert tau_weighted(x, np.ones(5), n) == tau_equal_counts(x, n)
    assert tau_weighted(x, np.ones(5), 0) == np.inf          # Aqua não viu nada → nenhum forte
    assert tau_weighted(x, np.ones(5), 99) == 1.0             # Aqua viu mais → todos fortes
    assert tau_weighted(x, np.array([1, 2, 1, 1, 1.0]), 3) == 7.0   # 9 pesa 2: cw = 2, 3 → 7


def test_tau_recovers_physical_threshold(cfg):
    A, B, P = world(cfg)
    m = M2(20, base.Context(cfg=cfg, passes=reader(cfg, P))).fit(A, B, FIT)
    tau = m.tau_table()
    assert len(tau) == 8 and set(tau.daynight) == {"D", "N"}
    assert ((tau.tau >= 10.0) & (tau.tau < 11.0)).all()                # τ = menor FRP ≥ limiar real na amostra
    assert np.allclose(tau.n_strong, tau.n_aqua)                       # iguala as contagens por estrato
    assert np.allclose(m.kf_global_, 1.0, atol=0.02)                  # forte por detecção Aqua ≈ 1
    assert m.mismatch_ == 0


def test_lambda0_equals_m1(cfg):
    A, B, P = world(cfg, seed=3)
    ctx = base.Context(cfg=cfg, passes=reader(cfg, P))
    p2 = M2(0, ctx).fit(A, B, FIT).params().set_index(["cell", "M"])
    p1 = M1(0, ctx).fit(A, B, FIT).params().set_index(["cell", "M"])
    ok = p2.sbf_pos > 0
    assert np.allclose(p2.k[ok], p1.k.reindex(p2.index)[ok])          # k_f·(1+r) = ΣB⁺/ΣA⁺
    assert np.allclose(p2.add_term, p1.add_term.reindex(p2.index))


def test_lambda_inf_goes_to_k_global(cfg):
    A, B, P = world(cfg, seed=4)
    ctx = base.Context(cfg=cfg, passes=reader(cfg, P))
    m2, m1 = M2(1e9, ctx).fit(A, B, FIT), M1(1e9, ctx).fit(A, B, FIT)
    kg = m1.k_global_.reindex(m2.params().M).to_numpy()
    assert np.allclose(m2.params().k, kg, rtol=1e-4)
    assert np.allclose(m2.global_table().k_global, m1.global_table().k_global)


def test_bootstrap_weights_tau(cfg):
    A, B, P = world(cfg, years=[2012, 2013], seed=5)
    ctx = base.Context(cfg=cfg, passes=reader(cfg, P))
    t = M2(20, ctx).fit(A, B, [2012, 2012, 2013]).tau_table()
    rep = Counter([2012, 2012, 2013])
    pa, pb = ctx.passes("AQUA", [2012, 2013]), ctx.passes("SNPP", [2012, 2013])
    for _, row in t.iterrows():
        sa = pa[(pa.season == row.season) & (pa.daynight == row.daynight)]
        sb = pb[(pb.season == row.season) & (pb.daynight == row.daynight)]
        dup = pd.concat([sb, sb[sb.ym // 100 == 2012]])                 # 2012 conta 2×
        na = sum(rep[y] for y in sa.ym // 100)
        assert row.n_aqua == na and row.tau == tau_equal_counts(dup.frp_max.to_numpy(), na)


def test_excluded_months_ignored(cfg):
    A, B, P = world(cfg, years=[2020], seed=6)
    m = M2(20, base.Context(cfg=cfg, passes=reader(cfg, P))).fit(A, B, [2020])
    assert set(m.params().M) == set(range(1, 13)) - {8, 9}             # pane do Aqua fora (R3)


def test_requires_passes_and_same_resolution(cfg):
    with pytest.raises(AssertionError, match="passes"):
        M2(20, base.Context(cfg=cfg))
    A, B, P = world(cfg, seed=7)
    bad = {s: d.assign(cell="x" + d.cell) for s, d in P.items()}        # outra resolução H3
    with pytest.raises(AssertionError, match="resolução"):
        M2(20, base.Context(cfg=cfg, passes=reader(cfg, bad))).fit(A, B, FIT)


def test_only_bridges_with_m2(cfg):
    A, B, P = world(cfg, seed=8)
    with pytest.raises(AssertionError, match="methods"):
        M2(20, base.Context(cfg=cfg, passes=reader(cfg, P)), "n20_snpp")


@pytest.mark.parametrize("lam", [0, 5, 20, 50])
def test_m2_conforms(cfg, lam):
    A, B, P = world(cfg, seed=9)
    A_new = world(cfg, years=[2005], cells=("c1", "c9"), seed=10)[0]
    ctx = base.Context(cfg=cfg, passes=reader(cfg, P))
    base.check_bridge(M2(lam, ctx), A, B, FIT, A_new, cfg)            # R1–R7


def test_eval_scores_only_active_cell_months(cfg):
    from pipeline.bridges.m2 import evaluate
    A, B, P = world(cfg, years=range(2012, 2022), cells=[f"c{i}" for i in range(6)], seed=11)
    A = pd.concat([A, pd.DataFrame({"cell": ["dead"], "ym": [201201], "n": [1]})])   # célula quase sempre sem fogo
    r = evaluate(A, B, cfg, "aqua_snpp", [20], reader(cfg, P))
    test = r[r.split.str.startswith("teste")].iloc[0]
    months = base.scoring_months(cfg, [2020, 2021])
    act = (pd.concat([A, B]).query("ym in @months and n > 0")[["cell", "ym"]].drop_duplicates())
    assert test.n == len(act)                                       # zeros duplos fora da nota (como m1 --eval)
    assert "total_ratio" in r.columns

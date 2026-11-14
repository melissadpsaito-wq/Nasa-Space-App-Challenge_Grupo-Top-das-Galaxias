"""M1 (Guia §3.2, D32, D33): fórmula, termo aditivo, prior global por mês, bootstrap, exclusão, cadeia.

Dados sintéticos: roda antes do agg_monthly real. Conformidade R1–R8 em tests/test_bridge_contract.py.
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.bridges import base
from pipeline.bridges.check_method import collapse, decompose, tau_equal_counts
from pipeline.bridges.m1 import M1


@pytest.fixture(scope="module")
def cfg():
    return base.load_config()


@pytest.fixture
def ctx(cfg):
    return base.Context(cfg=cfg)


def agg(rows):
    return pd.DataFrame(rows, columns=["cell", "ym", "n"])


# 2 células, jan e fev de 2012–2013. c1 queima pouco; c2 muito. Em fev/2013 c1 tem A = 0 e B = 6.
A = agg([("c1", 201201, 2), ("c1", 201301, 4), ("c1", 201202, 1),
         ("c2", 201201, 10), ("c2", 201301, 30), ("c2", 201202, 20), ("c2", 201302, 10)])
B = agg([("c1", 201201, 10), ("c1", 201301, 14), ("c1", 201202, 3), ("c1", 201302, 6),
         ("c2", 201201, 30), ("c2", 201301, 90), ("c2", 201202, 80), ("c2", 201302, 40)])
YEARS = [2012, 2013]


def par(m, cell, M):
    return m.params().set_index(["cell", "M"]).loc[(cell, M)]


def test_global_prior(ctx):
    m = M1(20, ctx).fit(A, B, YEARS)
    g = m.global_table().set_index("M")
    assert g.loc[1, "k_global"] == pytest.approx((10 + 14 + 30 + 90) / (2 + 4 + 10 + 30))     # ΣB⁺/ΣA⁺ jan
    assert g.loc[2, "k_global"] == pytest.approx((3 + 80 + 40) / (1 + 20 + 10))               # fev: c1/2013 (A=0) fora
    assert g.loc[2, "a_global"] == pytest.approx(6.0)                                         # único mês A=0 com B
    assert g.loc[1, "a_global"] == 0.0                                                        # jan sem meses A=0
    assert g.loc[3, "k_global"] == pytest.approx(m.k_all_)                                    # mês sem dados → k_all


def test_lambda_extremes(ctx):
    local = M1(0, ctx).fit(A, B, YEARS)
    assert par(local, "c1", 1).k == pytest.approx(24 / 6)                                     # λ=0 → razão local
    big = M1(1e12, ctx).fit(A, B, YEARS)
    kg1 = big.global_table().set_index("M").loc[1, "k_global"]
    assert par(big, "c1", 1).k == pytest.approx(kg1, rel=1e-6)                                # λ→∞ → prior
    m20 = M1(20, ctx).fit(A, B, YEARS)
    assert par(m20, "c1", 1).k == pytest.approx((24 + 20 * kg1) / (6 + 20))                   # fórmula


def test_additive_term_and_no_double_count(ctx):
    m = M1(0, ctx).fit(A, B, YEARS)
    p = par(m, "c1", 2)
    assert (p.sa_pos, p.sb_pos, p.n_zero, p.sb_zero) == (1, 3, 1, 6)                         # B de A=0 só no aditivo
    assert p.k == pytest.approx(3.0) and p.add_term == pytest.approx(6.0)
    out = m.transform(A, base.months_of(YEARS)).set_index(["cell", "ym"]).n_pred
    assert out[("c1", 201302)] == pytest.approx(6.0)
    assert out.sum() == pytest.approx(B.n.sum())                                              # λ=0 conserva o total


def test_unseen_cell(ctx):
    m = M1(20, ctx).fit(A, B, YEARS)
    new = agg([("c9", 200501, 5), ("c9", 200502, 0)])
    out = m.transform(new, [200501, 200502, 200503]).set_index(["cell", "ym"]).n_pred
    g = m.global_table().set_index("M")
    assert out[("c9", 200501)] == pytest.approx(5 * g.loc[1, "k_global"])
    assert out[("c9", 200502)] == pytest.approx(g.loc[2, "a_global"])
    assert out[("c1", 200501)] == pytest.approx(m.params().set_index(["cell", "M"]).loc[("c1", 1), "add_term"])


def test_bootstrap_weights(ctx):
    m = M1(0, ctx).fit(A, B, [2012, 2012, 2013])
    p = par(m, "c1", 1)
    assert (p.sa_pos, p.sb_pos) == (2 * 2 + 4, 2 * 10 + 14)                                  # 2012 pesa 2×


def test_excluded_months_ignored(ctx):
    a = agg([("c1", ym, 1) for ym in base.months_of([2019, 2020])])
    b = agg([("c1", ym, 1000 if ym == 202008 else 3) for ym in base.months_of([2019, 2020])])
    m = M1(0, ctx).fit(a, b, [2019, 2020])
    assert par(m, "c1", 8).k == pytest.approx(3.0)                                           # 202008 fora (R3)
    assert par(m, "c1", 8).sa_pos == 1                                                        # só 201908


def test_chain_terra_to_snpp(cfg, ctx):
    yrs = range(2001, 2020)
    base_n = {ym: 1 + (ym % 100 in (8, 9, 10)) * 4 for ym in base.months_of(yrs)}
    mk = lambda f, lo, hi: agg([("c1", ym, f * n) for ym, n in base_n.items() if lo <= ym // 100 <= hi])  # noqa: E731
    data = {"TERRA": mk(1, 2001, 2019), "AQUA": mk(2, 2003, 2019), "SNPP": mk(8, 2012, 2019)}
    run = base.build_chain("TERRA", lambda bid: M1(20, ctx), data.get, cfg)
    out = run(data["TERRA"], base.months_of([2001])).set_index("ym").n_pred
    np.testing.assert_allclose(out.to_numpy(), 8 * data["TERRA"].set_index("ym").n.loc[out.index].to_numpy())


def test_drift_shows_up_in_test(ctx):
    """Sintético com deriva de +20% no S-NPP/Aqua em 2020+: ajuste 2012–2019 subestima o teste (R05, D30)."""
    rng = np.random.default_rng(0)
    rows_a, rows_b = [], []
    for c in [f"c{i}" for i in range(30)]:
        for ym in base.months_of(range(2012, 2022)):
            lam_a = 5 * (1 + 4 * (ym % 100 in (8, 9, 10)))
            a_ = rng.poisson(lam_a)
            rows_a.append((c, ym, a_))
            rows_b.append((c, ym, rng.poisson(6 * (1.2 if ym >= 202001 else 1.0) * lam_a)))
    a_, b_ = agg(rows_a), agg(rows_b)
    m = M1(20, ctx).fit(a_, b_, list(range(2012, 2020)))
    months = base.scoring_months(ctx.cfg, [2020, 2021])
    pred = m.transform(a_[a_.ym.isin(months)], months).n_pred.sum()
    real = b_[b_.ym.isin(months)].n.sum()
    assert 0.78 < pred / real < 0.88                                                          # ≈ 1/1,2


# ---------- check_method ----------
def test_check_method_decomposition(cfg):
    ts = pd.Timestamp("2025-08-10 17:00")
    # Aqua: 2 fogos (1 por célula). S-NPP: os mesmos 2 fogos em 3 pixels cada (FRP 50) + 4 fogos fracos (FRP 2)
    aqua = pd.DataFrame({"ts": [ts, ts], "latitude": [-10.005, -12.005], "longitude": [-50.005, -52.005],
                         "frp": [40.0, 30.0], "daynight": ["D", "D"]})
    s_lat = [-10.005, -10.004, -10.003, -12.005, -12.004, -12.003, -14.0, -15.0, -16.0, -17.0]
    s_lon = [-50.005] * 3 + [-52.005] * 3 + [-54.0, -55.0, -56.0, -57.0]
    snpp = pd.DataFrame({"ts": [ts] * 10, "latitude": s_lat, "longitude": s_lon,
                         "frp": [50.0] * 6 + [2.0] * 4, "daynight": ["D"] * 10})
    r = decompose(aqua, snpp, cfg)
    assert r["raw"] == pytest.approx(5.0)
    assert r["grid"][0.02]["ratio"] == pytest.approx(3.0)                                     # 6 células / 2
    assert r["grid"][0.02]["tau"] == pytest.approx(50.0)
    assert r["grid"][0.02]["ratio_after_tau"] == pytest.approx(1.0)
    assert set(r["strata"].season) == {"JJA"}
    assert len(collapse(snpp.assign(ts=[ts] * 5 + [ts + pd.Timedelta("1h")] * 5), 0.02)) == 7  # célula B em 2 passagens conta 2×
    assert tau_equal_counts([1, 5, 3], 2) == 3

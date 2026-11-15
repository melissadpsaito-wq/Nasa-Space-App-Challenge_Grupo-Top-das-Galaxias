"""Série harmonizada provisória (M1): linha do tempo, emenda e schema (DATA_DICTIONARY §5)."""
import numpy as np
import pandas as pd
import pytest

from pipeline.bridges import base
from pipeline.bridges.harmonize import OUT_COLS, analysis_months, harmonize


@pytest.fixture(scope="module")
def cfg():
    return base.load_config()


def synth(seed=0):
    """Brasil sintético: 4 células; Aqua = 2× Terra, S-NPP = 8× Terra (determinístico, sazonal)."""
    rows = []
    for c in ["c1", "c2", "c3", "c4"]:
        for ym in base.months_of(range(2000, 2026)):
            base_n = 2 + 6 * (ym % 100 in (8, 9, 10))
            for s, f, (lo, hi) in [("TERRA", 1, (200011, 202512)), ("AQUA", 2, (200207, 202512)),
                                   ("SNPP", 8, (201201, 202512)), ("N20", 8, (201801, 202512))]:
                if lo <= ym <= hi:
                    rows.append((s, c, ym, f * base_n))
    return pd.DataFrame(rows, columns=["sensor", "cell", "ym", "n"])


def test_timeline_and_schema(cfg):
    h = harmonize(synth(), cfg, lam=20)
    assert list(h.columns) == OUT_COLS
    months = analysis_months(cfg)
    assert len(h) == 4 * len(months) and h.ym.min() == 200011 and h.ym.max() == 202512
    src = h.drop_duplicates("ym").set_index("ym").src
    assert src[200011] == "TERRA" and src[200206] == "TERRA" and src[200207] == "AQUA"
    assert src[201201] == "AQUA" and src[201202] == "SNPP" and src[202512] == "SNPP"
    assert (h.loc[h.src == "TERRA", "low_conf"] == 1).all() and (h.loc[h.src != "TERRA", "low_conf"] == 0).all()
    assert (h.lo == h.n_harm).all() and (h.hi == h.n_harm).all()
    assert not h.n_harm.isna().any() and (h.n_harm >= 0).all()


def test_scale_is_snpp(cfg):
    h = harmonize(synth(), cfg, lam=20)
    snpp = h[h.src == "SNPP"]
    np.testing.assert_allclose(snpp.n_harm, snpp.n_raw)                         # nativo
    aq = h[h.src == "AQUA"]
    np.testing.assert_allclose(aq.n_harm, 4 * aq.n_raw, rtol=1e-6)              # Aqua × 4 = escala S-NPP
    te = h[h.src == "TERRA"]
    np.testing.assert_allclose(te.n_harm, 8 * te.n_raw, rtol=1e-6)              # Terra × 2 × 4
    y = h.assign(a=h.ym // 100).groupby("a").n_harm.sum()
    assert y[2011] == pytest.approx(y[2012], rel=1e-6)                           # sem degrau na emenda

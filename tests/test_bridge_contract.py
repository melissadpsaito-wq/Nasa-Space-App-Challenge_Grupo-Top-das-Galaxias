"""Contrato da Ciência (§3.1): YAML coerente + regras R1–R7 de pipeline/bridges/base.py.

Usa dados sintéticos: roda antes do agg_monthly real. Dona: Melissa. Toda ponte nova tem de passar em
base.check_bridge (M1/M2 aqui; baselines do Samuel no teste dele).
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.bridges import base


@pytest.fixture(scope="module")
def cfg():
    return base.load_config()


def fake_agg(sensor, years, cells=("c1", "c2", "c3"), scale=1.0, seed=0):
    rng = np.random.default_rng(seed)
    rows = [(sensor, c, ym, int(rng.poisson(scale * (1 + 4 * (ym % 100 in (8, 9, 10))))))
            for c in cells for ym in base.months_of(years)]
    df = pd.DataFrame(rows, columns=["sensor", "cell", "ym", "n"])
    return df[df.n > 0].reset_index(drop=True)       # esparso, como o agg_monthly real


class _GlobalFactor:  # exemplo mínimo de ponte que cumpre o contrato (não é o baseline oficial do Samuel)
    name = "global"

    def __init__(self, ctx):
        self.ctx = ctx

    def fit(self, A, B, years):
        t = base.paired(A, B, years, self.ctx.cfg)
        self.cells_ = set(t.cell)
        self.k_ = (t.b.sum() + 1) / (t.a.sum() + 1)
        return self

    def transform(self, A, months=None):
        months = base.default_months(A, months)
        d = base.densify(A, self.cells_ | set(A.cell), months)
        return pd.DataFrame({"cell": d.cell, "ym": d.ym.astype("int64"), "n_pred": d.n * float(self.k_)})


def test_yaml(cfg):
    assert cfg["reference"] == "SNPP"
    assert set(cfg["chains"]) == {"TERRA", "AQUA", "N20"}
    for b in cfg["bridges"]:
        assert not set(base.fit_years(cfg, b["id"])) & set(base.test_years(cfg, b["id"])), "fit ∩ test"
    assert base.excluded_months(cfg) == {202008, 202009}
    assert [t["sensor"] for t in cfg["timeline"]] == ["TERRA", "AQUA", "SNPP"]
    assert cfg["analysis_period"] == [200011, 202512]                  # D33
    assert "biome" not in str(cfg).lower()                            # D33


def test_check_config_catches_errors(cfg):
    import copy
    bad = copy.deepcopy(cfg)
    bad["timeline"][1]["from"] = 200208                               # buraco em jul/2002
    with pytest.raises(AssertionError, match="timeline"):
        base.check_config(bad)
    bad = copy.deepcopy(cfg)
    bad["bridges_by_id"]["n20_snpp"]["fit"] = [2015, 2025]            # N20 não existia em 2015
    with pytest.raises(AssertionError, match="sobreposição"):
        base.check_config(bad)


def test_context_has_no_biome(cfg):
    assert not hasattr(base.Context(cfg=cfg), "cell_biome")           # D33


def test_winner(cfg, tmp_path):
    p = tmp_path / "validation.json"
    assert base.winner(cfg, "aqua_snpp", p) is None                   # antes do Samuel rodar
    p.write_text('{"aqua_snpp": {"winner": {"method": "M2", "lam": 20}}}')
    assert base.winner(cfg, "aqua_snpp", p) == {"method": "M2", "lam": 20}
    assert base.winner(cfg, "n20_snpp", p) is None
    p.write_text('{"aqua_snpp": {"winner": {"method": "M2", "lam": 7}}}')
    with pytest.raises(AssertionError, match="lambda_grid"):
        base.winner(cfg, "aqua_snpp", p)


def test_passes_reader(cfg, tmp_path):
    pytest.importorskip("pyarrow")
    p = tmp_path / "grid2km_pass.parquet"
    pd.DataFrame({"sensor": ["SNPP", "SNPP", "SNPP", "AQUA"], "cell": ["c1"] * 4,
                  "ym": [202001, 202008, 202107, 202001], "daynight": ["D", "N", "D", "D"],
                  "frp_max": [5.0, 9.0, 12.0, 30.0], "n_pix": [1, 2, 3, 1]}).to_parquet(p)
    out = base.passes_reader(cfg, p)("SNPP", [2020, 2020])
    assert list(out.columns) == base.PASS_COLS + ["season"]
    assert out.ym.tolist() == [202001] and out.season.tolist() == ["DJF"]   # 202008 excluído (R3); só SNPP; 2021 fora


def test_paired_rules(cfg):
    A, B = fake_agg("AQUA", [2019, 2020]), fake_agg("SNPP", [2019, 2020], scale=4, seed=1)
    t = base.paired(A, B, [2019, 2019, 2020], cfg)
    assert list(t.columns) == ["cell", "ym", "rep", "a", "b"]
    assert not t.ym.isin([202008, 202009]).any()                    # R3
    assert (t[t.ym // 100 == 2019].groupby("cell").size() == 24).all()   # R2: 2019 entra 2×
    assert t.b.sum() == B[(B.ym // 100 == 2019)].n.sum() * 2 + B[(B.ym // 100 == 2020) & ~B.ym.isin([202008, 202009])].n.sum()


def test_season(cfg):
    assert list(base.season_of([202001, 202004, 202007, 202010, 202012], cfg)) == ["DJF", "MAM", "JJA", "SON", "DJF"]


BRIDGES = {"global": _GlobalFactor}   # Melissa acrescenta M1, M2. Samuel testa os baselines no próprio teste com base.check_bridge (R12)


@pytest.mark.parametrize("name", BRIDGES)
def test_bridge_conforms(cfg, name):
    ctx = base.Context(cfg=cfg)
    A, B = fake_agg("AQUA", range(2012, 2020)), fake_agg("SNPP", range(2012, 2020), scale=4, seed=1)
    A_new = fake_agg("AQUA", [2005], cells=("c1", "c9"), seed=2)
    base.check_bridge(BRIDGES[name](ctx), A, B, base.fit_years(cfg, "aqua_snpp"), A_new, cfg)


def test_chain(cfg):
    ctx = base.Context(cfg=cfg)
    data = {"TERRA": fake_agg("TERRA", range(2001, 2011)), "AQUA": fake_agg("AQUA", range(2003, 2020), scale=2),
            "SNPP": fake_agg("SNPP", range(2012, 2020), scale=8)}
    run = base.build_chain("TERRA", lambda bid: _GlobalFactor(ctx), data.get, cfg)
    out = run(data["TERRA"], base.months_of([2001]))
    base.check_output(out, set(data["TERRA"].cell), base.months_of([2001]))

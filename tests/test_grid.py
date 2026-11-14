"""2.2 grade: peneira por passagem, H3, conservação e schema do agg_monthly (DATA_DICTIONARY §2 e §5)."""
from pathlib import Path

import pandas as pd
import pytest

duckdb = pytest.importorskip("duckdb")
h3 = pytest.importorskip("h3")
pytest.importorskip("pyarrow")

from pipeline import grid  # noqa: E402


def write_clean(root: Path, rows: list[tuple]) -> None:
    df = pd.DataFrame(rows, columns=["sensor", "ts", "latitude", "longitude", "frp", "daynight", "pixel_area"])
    df["ts"] = pd.to_datetime(df.ts)
    df = df.astype({"frp": "float32", "pixel_area": "float32"})
    for (s, y), d in df.groupby([df.sensor, df.ts.dt.year]):
        (root / s).mkdir(parents=True, exist_ok=True)
        d.to_parquet(root / s / f"{y}.parquet", index=False)


@pytest.fixture
def built(tmp_path):
    t1, t2 = "2020-08-10 17:00", "2020-08-11 04:10"
    rows = [  # S-NPP: 1 fogo em 3 pixels (mesma célula 0,02°) + 1 fogo fraco; o mesmo fogo na passagem noturna
        ("SNPP", t1, -19.005, -57.005, 30.0, "D", 0.14), ("SNPP", t1, -19.004, -57.004, 20.0, "D", 0.14),
        ("SNPP", t1, -19.003, -57.003, 10.0, "D", 0.14), ("SNPP", t1, -18.501, -56.501, 2.0, "D", 0.14),
        ("SNPP", t2, -19.005, -57.005, 8.0, "N", 0.14),
        ("AQUA", t1, -19.005, -57.005, 50.0, "D", 1.3), ("AQUA", "2021-01-05 17:00", -19.005, -57.005, 9.0, "D", 1.3),
    ]
    write_clean(tmp_path / "clean", rows)
    s = grid.build(tmp_path / "clean", tmp_path / "out")
    p = pd.read_parquet(tmp_path / "out" / "grid2km_pass.parquet")
    a = pd.read_parquet(tmp_path / "out" / "agg_monthly.parquet")
    return s, p, a


def test_sieve_per_pass(built):
    s, p, _ = built
    snpp = p[p.sensor == "SNPP"]
    assert len(snpp) == 3                                              # 3 pixels → 1; fraco → 1; noturno → 1
    big = snpp[(snpp.daynight == "D") & (snpp.n_pix == 3)].iloc[0]
    assert (big.frp_max, big.frp_sum) == (30.0, 60.0)
    assert s.set_index(["sensor", "year"]).loc[("SNPP", 2020), "pixels_per_cell"] == pytest.approx(5 / 3)


def test_h3_and_month(built):
    _, p, _ = built
    assert p.cell.map(lambda c: h3.is_valid_cell(c) and h3.get_resolution(c) == 4).all()
    assert set(p.ym) == {202008, 202101}


def test_agg_monthly_schema_and_conservation(built):
    s, p, a = built
    assert list(a.columns) == ["sensor", "cell", "ym", "n", "frp_mean", "frp_p90", "night_frac", "pix_area", "frp_sum"]
    assert a.ym.dtype.kind == "i" and a.n.dtype.kind == "i"
    assert a.n.sum() == len(p)
    assert (s.pixels == s.clean_rows).all()
    aq = a[(a.sensor == "AQUA") & (a.ym == 202008)].iloc[0]
    assert aq.n == 1 and aq.frp_sum == 50.0
    sn = a[(a.sensor == "SNPP")].groupby("ym").n.sum()
    assert sn[202008] == 3


ROOT = Path("data/interim/pantanal")


@pytest.mark.skipif(not (ROOT / "agg_monthly.parquet").exists(), reason="rodar python -m pipeline.grid --area pantanal")
def test_real_pantanal_conservation():
    log = pd.read_csv(ROOT / "grid_log.csv")
    assert (log.pixels == log.clean_rows).all() and (log.agg_n == log.pass_cells).all()
    a = pd.read_parquet(ROOT / "agg_monthly.parquet", columns=["sensor", "ym", "n"])
    assert int(a.n.sum()) == int(log.pass_cells.sum())

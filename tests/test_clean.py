"""Testes do 2.1: conservação (Parquet == log) e schema do contrato (DATA_DICTIONARY §1)."""
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOTS = [p for p in (Path("data/clean"), Path("data/clean_pantanal")) if (p / "filter_log.csv").exists()]
SCHEMA = {"sensor": "VARCHAR", "ts": "TIMESTAMP", "latitude": "DOUBLE", "longitude": "DOUBLE",
          "frp": "FLOAT", "daynight": "VARCHAR", "pixel_area": "FLOAT"}


@pytest.mark.parametrize("root", ROOTS, ids=str)
def test_conservation(root):
    log = pd.read_csv(root / "filter_log.csv")
    exp = log[log.step == "conf"].groupby(["sensor", "year"]).rows_out.sum()
    exp = exp[exp > 0]
    got = duckdb.sql(f"""SELECT sensor, year(ts) AS year, count(*) n
                         FROM read_parquet('{root}/*/*.parquet') GROUP BY ALL""").df()
    got = got.set_index(["sensor", "year"]).n
    assert got.sort_index().to_dict() == exp.sort_index().to_dict()


@pytest.mark.parametrize("root", ROOTS, ids=str)
def test_schema_and_values(root):
    q = f"read_parquet('{root}/*/*.parquet')"
    types = {r[0]: r[1] for r in duckdb.sql(f"DESCRIBE SELECT * FROM {q}").fetchall()}
    assert types == SCHEMA
    bad = duckdb.sql(f"""SELECT
        count(*) FILTER (WHERE sensor NOT IN ('TERRA','AQUA','SNPP','N20','N21')),
        count(*) FILTER (WHERE daynight NOT IN ('D','N')),
        count(*) FILTER (WHERE ts < TIMESTAMP '2000-11-01'),
        count(*) FILTER (WHERE frp IS NULL OR frp < 0),
        count(*) FILTER (WHERE latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180)
        FROM {q}""").fetchall()[0]
    assert bad == (0, 0, 0, 0, 0)

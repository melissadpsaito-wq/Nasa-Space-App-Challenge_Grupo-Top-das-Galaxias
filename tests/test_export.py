"""Testes do export 2.4 (DATA_DICTIONARY §3, §6, §8). Não dependem de h3 nem de Parquet."""
import json

import pandas as pd
import pytest

from pipeline import export as ex


def _harm():
    # 3 células: A com fogo, B só com fogo bruto, Z sem fogo (deve ser omitida)
    rows = [
        ("A1", 200011, 1.24, 0.0, 1.0, 1.5, 1, "TERRA"),
        ("A1", 201202, 3.0, 3.0, 3.0, 3.0, 0, "SNPP"),
        ("A1", 202512, 0.04, 0.0, 0.0, 0.1, 0, "SNPP"),
        ("B2", 201101, 0.0, 2.0, 0.0, 0.0, 0, "AQUA"),
        ("Z9", 201505, 0.0, 0.0, 0.0, 0.0, 0, "SNPP"),
        ("A1", 202601, 9.0, 9.0, 9.0, 9.0, 0, "SNPP"),   # fora do período (D33)
    ]
    return pd.DataFrame(rows, columns=["cell", "ym", "n_harm", "n_raw", "lo", "hi", "low_conf", "src"])


def test_month_range():
    m = ex.month_range()
    assert m[0] == 200011 and m[-1] == 202512 and len(m) == 302
    assert ex.month_range(201911, 202002) == [201911, 201912, 202001, 202002]


def test_payload_contract():
    p = ex.build_payload(_harm())
    assert set(p) == {"months", "cells", "raw", "lo", "hi", "low_conf", "src"}
    assert set(p["cells"]) == {"A1", "B2"}                # Z9 omitida
    i = p["months"].index
    a = p["cells"]["A1"]
    assert a[i(200011)] == 12 and a[i(201202)] == 30 and a[i(202512)] == 0   # × 10, arredondado
    assert p["hi"]["A1"][i(202512)] == 1
    assert p["raw"]["B2"][i(201101)] == 20
    assert p["low_conf"]["A1"][i(200011)] == 1 and sum(p["low_conf"]["B2"]) == 0
    assert ex.validate(p) == 0
    json.dumps(p)                                          # serializável (int nativos)


def test_src_contract():
    p = ex.build_payload(_harm())
    i = p["months"].index
    assert p["src"][i(200011)] == "TERRA" and p["src"][i(200206)] == "TERRA"
    assert p["src"][i(200207)] == "AQUA" and p["src"][i(201201)] == "AQUA"
    assert p["src"][i(201202)] == "SNPP" and p["src"][-1] == "SNPP"


def test_conservation():
    h = _harm()
    p = ex.build_payload(h)
    cons = ex.conservation(h, p, ex.month_range())
    assert cons["raw"] == (5.0, 5.0)


def test_tiles_same_format():
    h = pd.concat([_harm(), pd.DataFrame(
        [("A2", 201909, 5.0, 5.0, 4.0, 6.0, 0, "SNPP")], columns=_harm().columns)])
    p = ex.build_payload(h)
    tiles = ex.split_tiles(p, parent_fn=lambda c: c[0])   # stub no lugar de h3.cell_to_parent
    assert set(tiles) == {"A", "B"}
    assert set(tiles["A"]["cells"]) == {"A1", "A2"}
    for t in tiles.values():
        assert t["months"] == p["months"] and t["src"] == p["src"]
        ex.validate(t)
    total = sum(sum(v) for t in tiles.values() for v in t["cells"].values())
    assert total == sum(sum(v) for v in p["cells"].values())


def test_missing_column():
    with pytest.raises(ValueError):
        ex.build_payload(_harm().drop(columns="lo"))


def test_validate_catches_misaligned():
    p = ex.build_payload(_harm())
    p["lo"]["A1"] = p["lo"]["A1"][:-1]
    with pytest.raises(AssertionError):
        ex.validate(p)

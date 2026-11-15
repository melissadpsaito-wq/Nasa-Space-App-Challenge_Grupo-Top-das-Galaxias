"""Testes do adaptador D48 (RF → Outlook). Base sintética pequena; usa sklearn, sem h3 nem Parquet."""
import json

import numpy as np
import pandas as pd
import pytest

from pipeline.forecast import rf_outlook as rf
from pipeline.forecast import export_forecast as ef

CELLS = ["855f0483fffffff", "85283473fffffff", "8580107bfffffff", "8580a5b3fffffff"]
BIOME = ["amazonia", "cerrado", "pantanal", "amazonia"]


def _history():
    """ΣFRP 2003–2025: célula k queima em ago–out com intensidade k+1; 2024 é ano forte."""
    rows = []
    for k, c in enumerate(CELLS):
        for y in range(2000, 2026):
            for m in range(1, 13):
                v = (k + 1) * 10.0 * (m in (8, 9, 10)) * (2 if y == 2024 else 1) + (y % 3) * (m == 9)
                rows.append((c, 0.0, 0.0, y, m, v))
    return pd.DataFrame(rows, columns=["cell", "lat", "lon", "year", "month", "frp"])


def _data(h):
    d = h[h.year >= 2016].rename(columns={"frp": rf.TARGET}).copy()
    d["lat"] = d.cell.map(dict(zip(CELLS, [2.3, -18.5, -3.4, -7.1])))
    d["lon"] = d.cell.map(dict(zip(CELLS, [-55.9, -57.0, -62.2, -55.4])))
    d["precipitacao"] = np.where(d.month.isin([8, 9, 10]), 1.0, 8.0) + (d.year - 2016) * 0.01
    d["umidade"] = np.where(d.month.isin([8, 9, 10]), 55.0, 85.0)
    d["temp_max"] = 32.0
    for b in rf.BIOMES:
        d[b] = (d.cell.map(dict(zip(CELLS, BIOME))) == b).astype(int)
    return d.reset_index(drop=True)


def test_baselines_no_leak():
    h = _history()
    cube, years = rf.history_cube(h, CELLS)
    assert cube.shape == (4, 23, 12) and years[0] == 2003
    b = rf.baselines(cube, 2024)
    assert b["normal"][1, 8] == np.median([20 + (y % 3) for y in range(2003, 2024)])   # set, célula 1
    assert b["persist"][1, 8] == 20 + (2023 % 3)                                         # valor de 2023
    assert 0 <= b["p_d27"].min() and b["p_d27"].max() <= 1
    # 2024 (forte) não entra no normal de 2024, só no de 2025
    assert rf.normals(cube, 2024)[0, 7] == 10 and rf.normals(cube, 2025)[0, 7] == 10


def test_climatology_replaces_climate_by_biome_month():
    d = _data(_history())
    tr, te = d[d.year < 2020], d[d.year == 2020]
    t = rf.with_climatology(te, tr)
    exp = tr[tr.month == 9].precipitacao.mean()
    assert np.allclose(t[t.month == 9].precipitacao, exp)
    assert (t[rf.TARGET].to_numpy() == te[rf.TARGET].to_numpy()).all()       # alvo intacto
    assert set(rf.biome_of(te)) == {"amazonia", "cerrado", "pantanal"}


def test_outlook_from_trees():
    T = np.array([[0, 5, 10], [2, 5, 30], [4, 5, 50], [6, 5, -1]], dtype=float)   # 4 árvores × 3 linhas
    o = rf.outlook(T, normal=np.array([3, 5, 20]))
    assert o["p"].tolist() == [0.5, 0.0, 0.5]                                     # > normal (empate não conta)
    assert (o["q10"] <= o["q50"]).all() and (o["q50"] <= o["q90"]).all() and o["q10"].min() >= 0


def test_score_year_keys_and_skill_sign():
    y = np.array([0, 10, 0, 10.0])
    b = {"normal": np.array([5, 5, 5, 5.0]), "p_clim": np.full(4, 0.5), "p_d27": np.full(4, 0.5),
         "persist": np.array([10, 0, 10, 0.0])}
    good = {"p": np.array([0, 1, 0, 1.0]), "q10": y * 0.5, "q50": y, "q90": y * 2}
    r = rf.score_year(y, good, b)
    assert r["bss_clim"] == 1.0 and r["auc"] == 1.0 and r["log_err_model"] == 0.0 and r["coverage_80"] == 1.0
    assert r["log_err_persist"] > r["log_err_model"]


def test_main_end_to_end_feeds_exporter(tmp_path):
    h = _history()
    d = _data(h)
    d.to_csv(tmp_path / "data.csv", sep=";", index=False)
    h.to_csv(tmp_path / "hist.csv", index=False)
    out = tmp_path / "fc"
    rf.main(["--data", str(tmp_path / "data.csv"), "--history", str(tmp_path / "hist.csv"), "--out", str(out),
             "--trees", "8", "--final-trees", "8", "--max-depth", "6", "--max-samples", "0.8"])
    skill = json.loads((out / "forecast_skill.json").read_text())
    assert set(skill["years"]) == {"2021", "2022", "2023", "2024", "2025"}
    assert set(ef.SKILL_KEYS) <= set(skill["overall"])
    pred = pd.read_csv(out / "forecast_2026.csv")
    assert len(pred) == 4 * 12 and set(pred.columns) >= {"cell", "month", "p", "q10", "q50", "q90", "normal"}
    # entra direto no exportador (contrato §9)
    ef.main(["--pred", str(out / "forecast_2026.csv"), "--skill", str(out / "forecast_skill.json"),
             "--unit", "frp_mw", "--out", str(tmp_path / "app")])
    tiles = [p for p in (tmp_path / "app").iterdir() if p.name.startswith("forecast_82")]
    assert tiles and "passes_gate" in json.loads((tmp_path / "app" / "forecast_skill.json").read_text())
    # previsão de setembro na célula mais forte > fevereiro
    c = pred[pred.cell == CELLS[3]].set_index("month")
    assert c.loc[9, "q50"] > c.loc[2, "q50"]

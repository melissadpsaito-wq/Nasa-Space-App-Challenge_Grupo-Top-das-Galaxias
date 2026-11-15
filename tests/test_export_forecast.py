"""Testes do export do Fire Outlook 2026 (D35, DATA_DICTIONARY §9). Sem h3 nem Parquet."""
import json

import pandas as pd
import pytest

from pipeline.forecast import export_forecast as ef

A = "855f0483fffffff"          # res 5 (Amapá/PA, base D42)
B = "85283473fffffff"          # res 5, outro pai


def _pred(cells=(A, B), p=0.4):
    rows = []
    for c in cells:
        for m in range(1, 13):
            q50 = 2.0 if m in (8, 9, 10) else 0.04
            rows.append((c, m, p, q50 / 2, q50, q50 * 3))
    return pd.DataFrame(rows, columns=["cell", "month", "p", "q10", "q50", "q90"])


def _skill(model=(0.4, 0.5, 0.3, 0.6, 0.45), clim=0.5, bss_clim=0.08, bss_d27=0.05):
    years = {y: dict(bss_clim=bss_clim, bss_d27=bss_d27, auc=0.7, log_err_model=e, log_err_clim=clim,
                     log_err_persist=0.7, coverage_80=0.78) for y, e in zip(ef.TEST_YEARS, model)}
    return {"years": years, "overall": dict(years["2021"], bss_clim=bss_clim, bss_d27=bss_d27), "passes_gate": True}


def test_h3_bits_match_known_parents():
    assert ef.h3_res(A) == 5
    assert ef.h3_parent_bits("8928308280fffff", 5) == "85283083fffffff"   # exemplo da documentação H3
    assert ef.h3_parent_bits(A, 2) == "825f07fffffffff"
    assert ef.h3_res(ef.h3_parent_bits(A, 2)) == 2
    with pytest.raises(ValueError):
        ef.h3_parent_bits("822837fffffffff", 5)


def test_normalize_accepts_month_or_ym():
    d = ef.normalize(_pred())
    assert d.ym.min() == 202601 and d.ym.max() == 202612
    d2 = ef.normalize(_pred().assign(ym=lambda x: 202600 + x.month).drop(columns="month"))
    assert d2.equals(d)
    with pytest.raises(ValueError):
        ef.normalize(_pred().drop(columns="q90"))


@pytest.mark.parametrize("bad, msg", [
    (lambda d: d.assign(p=d.p * 100), "p fora"),
    (lambda d: d.assign(q10=d.q50 + 1), "cruzados"),
    (lambda d: d[d.month != 7], "12 meses"),
    (lambda d: pd.concat([d, d.head(1)]), "duplicadas"),
    (lambda d: d.assign(cell=d.cell.replace(A, "822837fffffffff")), "res 5"),
])
def test_validate_rejects(bad, msg):
    with pytest.raises(AssertionError, match=msg):
        ef.validate_pred(ef.normalize(bad(_pred())))


def test_tiles_contract_and_scale():
    d = ef.normalize(_pred())
    info = ef.validate_pred(d)
    assert info["cells"] == 2
    tiles = ef.build_tiles(d, "detections")
    assert set(tiles) == {"825f07fffffffff", "822837fffffffff"}
    t = tiles["825f07fffffffff"]
    assert t["months"] == ef.MONTHS and t["unit"] == "detections"
    v = t["cells"][A]
    assert v["p"] == [40] * 12                                  # × 100
    assert v["q50"][7] == 20 and v["q50"][0] == 0               # × 10, arredondado (0,04 → 0)
    assert v["q10"][7] == 10 and v["q90"][7] == 60
    assert all(isinstance(x, int) for k in v for x in v[k])
    json.dumps(tiles)
    with pytest.raises(AssertionError):
        ef.build_tiles(d, "focos")


def test_gate_rules():
    assert ef.check_gate(_skill())["passes"]                    # 3 de 5 anos abaixo da climatologia (0,4/0,3/0,45)
    g = ef.check_gate(_skill(model=(0.6, 0.5, 0.3, 0.6, 0.45)))  # só 2 de 5
    assert not g["passes"] and not g["rules"]["log_err_beats_clim_3_of_5"]
    assert not ef.check_gate(_skill(bss_d27=-0.01))["passes"]    # perde do D27
    assert not ef.check_gate(_skill(bss_clim=0.0))["passes"]     # BSS = 0 não basta
    s = _skill(); del s["years"]["2025"]
    assert not ef.check_gate(s)["passes"]                        # hindcast incompleto


def test_main_writes_tiles_and_recomputed_gate(tmp_path, capsys):
    pred, skill = tmp_path / "pred.csv", tmp_path / "skill.json"
    _pred().to_csv(pred, index=False)
    sk = _skill(model=(0.6, 0.6, 0.6, 0.3, 0.3))               # arquivo diz True, recálculo diz False
    skill.write_text(json.dumps(sk))
    ef.main(["--pred", str(pred), "--skill", str(skill), "--unit", "detections",
             "--out", str(tmp_path / "out"), "--expect-cells", "10"])
    out = capsys.readouterr().out
    assert "REPROVADO" in out and "vale o recalculado" in out and "AVISO: 2 de 10" in out
    files = sorted(p.name for p in (tmp_path / "out").iterdir())
    assert "forecast_skill.json" in files and len([f for f in files if f.startswith("forecast_82")]) == 2
    w = json.loads((tmp_path / "out" / "forecast_skill.json").read_text())
    assert w["passes_gate"] is False and w["unit"] == "detections" and w["gate"]["rules"]


def test_normal_optional_vector():
    d = ef.normalize(_pred().assign(normal=0.55))
    ef.validate_pred(d)
    v = ef.build_tiles(d, "frp_mw")["825f07fffffffff"]["cells"][A]
    assert v["normal"] == [6] * 12                              # 0,55 × 10 → 6 (arredondado)
    with pytest.raises(AssertionError, match="normal"):
        ef.validate_pred(ef.normalize(_pred().assign(normal=-1)))

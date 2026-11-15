"""Previsão P3 — export do Fire Outlook 2026 para o app (D35, PREVISAO §4, DATA_DICTIONARY §9).

Liga QUALQUER modelo ao app: o modelo (notebook ou pipeline/forecast/model.py) grava duas coisas
e este script valida, confere o portão e gera os tiles que o navegador lê.

Entrada 1 — previsões 2026 (CSV ou Parquet), uma linha por célula H3 res 5 × mês:
    cell   str   H3 res 5 (D36)
    month  int   1..12 (ou ym = 2026MM)
    p      float P(acima do normal), 0–1  (normal = mediana do mês nos anos anteriores, sem vazamento)
    q10, q50, q90  float  ≥ 0, q10 ≤ q50 ≤ q90, na unidade --unit
    normal float  opcional (D48): mediana histórica do mês na célula, na unidade --unit
Entrada 2 — forecast_skill.json do hindcast 2021–2025 (PREVISAO §3):
    {"years": {"2021": {"bss_clim":…, "bss_d27":…, "auc":…, "log_err_model":…, "log_err_clim":…,
                        "log_err_persist":…, "coverage_80":…}, …, "2025": {…}},
     "overall": {mesmas chaves}, "passes_gate": bool, …}
    O portão é RECALCULADO aqui (check_gate); se o arquivo disser outra coisa, vale o recálculo.

Saída (app/public/data/):
    forecast_<pai res 2>.json   {"months":[202601..202612], "unit":"detections",
                                 "cells":{"<h3>":{"p":[×100 int], "q10":[×10], "q50":[×10], "q90":[×10],
                                                  "normal":[×10] (opcional, D48)}}}
    forecast_skill.json         skill + "passes_gate" recalculado + "gate" (detalhe por regra)
    Pai sem arquivo = região sem previsão (404 no app).

Uso (raiz do repo):
    python -m pipeline.forecast.export_forecast --pred data/processed/forecast_2026.csv \
        --skill data/processed/forecast_skill.json --unit detections
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

OUT_DEFAULT = "app/public/data"
YEAR = 2026
MONTHS = [YEAR * 100 + m for m in range(1, 13)]
PRODUCT_RES = 5                                     # D36
PARENT_RES = 2                                      # D38 / R06
UNITS = ("detections", "frp_mw")                    # contagem harmonizada (D03) ou ΣFRP harmonizado (D40)
TEST_YEARS = ("2021", "2022", "2023", "2024", "2025")
SKILL_KEYS = ("bss_clim", "bss_d27", "auc", "log_err_model", "log_err_clim", "log_err_persist", "coverage_80")
SEP = (",", ":")


# ---------------------------------------------------------------- H3 sem dependência
def h3_res(cell: str) -> int:
    """Resolução de um índice H3 (bits 52–55)."""
    return (int(cell, 16) >> 52) & 0xF


def h3_parent_bits(cell: str, res: int = PARENT_RES) -> str:
    """cell_to_parent por operação de bits (igual ao h3.cell_to_parent): troca a resolução e
    preenche com 7 (0b111) os dígitos abaixo de `res`. Evita depender do pacote h3 nos testes."""
    x = int(cell, 16)
    r = (x >> 52) & 0xF
    if res > r:
        raise ValueError(f"res {res} > resolução da célula ({r})")
    x = (x & ~(0xF << 52)) | (res << 52)
    for d in range(res + 1, 16):
        x |= 0x7 << ((15 - d) * 3)
    return f"{x:015x}"


# ---------------------------------------------------------------- previsões
def load_pred(path: str) -> pd.DataFrame:
    p = Path(path)
    df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, sep=None, engine="python")
    return df


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Aceita month 1..12 ou ym 2026MM; devolve cell, ym, p, q10, q50, q90 (+ normal, se houver)."""
    d = df.copy()
    d.columns = [c.strip().lower() for c in d.columns]
    if "ym" not in d.columns:
        if "month" not in d.columns:
            raise ValueError("previsões sem coluna month nem ym")
        d["ym"] = YEAR * 100 + d["month"].astype(int)
    need = {"cell", "ym", "p", "q10", "q50", "q90"}
    miss = need - set(d.columns)
    if miss:
        raise ValueError(f"previsões sem colunas: {sorted(miss)}")
    d["cell"] = d["cell"].astype(str)
    d["ym"] = d["ym"].astype(int)
    return d[["cell", "ym", "p", "q10", "q50", "q90"] + (["normal"] if "normal" in d.columns else [])]


def validate_pred(d: pd.DataFrame) -> dict:
    """Regras do contrato §9. Erro = AssertionError; devolve um resumo para o log."""
    assert d["ym"].isin(MONTHS).all(), f"meses fora de {MONTHS[0]}–{MONTHS[-1]}"
    dup = d.duplicated(["cell", "ym"]).sum()
    assert dup == 0, f"{dup} linhas duplicadas (cell, ym)"
    res = d["cell"].drop_duplicates().map(h3_res)
    assert (res == PRODUCT_RES).all(), f"células fora da res {PRODUCT_RES}: {res[res != PRODUCT_RES].unique()[:5]}"
    assert d[["p", "q10", "q50", "q90"]].notna().all().all(), "NaN em p ou quantis"
    assert d["p"].between(0, 1).all(), "p fora de [0, 1] (use probabilidade, não %)"
    assert (d["q10"] >= 0).all(), "q10 negativo"
    if "normal" in d.columns:
        assert d["normal"].notna().all() and (d["normal"] >= 0).all(), "normal ausente ou negativo"
    cross = ((d["q10"] > d["q50"] + 1e-9) | (d["q50"] > d["q90"] + 1e-9)).sum()
    assert cross == 0, f"{cross} linhas com quantis cruzados (q10 ≤ q50 ≤ q90)"
    per_cell = d.groupby("cell")["ym"].nunique()
    incomplete = int((per_cell != 12).sum())
    assert incomplete == 0, f"{incomplete} células sem os 12 meses de {YEAR}"
    return {"cells": int(per_cell.size), "rows": int(len(d)),
            "p_mean": float(d["p"].mean()), "q50_sum": float(d["q50"].sum())}


def parent_fn_default(res: int = PARENT_RES):
    """h3.cell_to_parent se o pacote existir (igual ao export.py); senão, a versão por bits."""
    try:
        import h3  # v4
        return lambda cell: h3.cell_to_parent(cell, res)
    except ImportError:
        return lambda cell: h3_parent_bits(cell, res)


def build_tiles(d: pd.DataFrame, unit: str, parent_fn=h3_parent_bits) -> dict[str, dict]:
    """Previsões → um JSON por célula-pai res 2 (p × 100, quantis × 10, inteiros)."""
    assert unit in UNITS, f"unit deve ser {UNITS}"
    d = d.sort_values(["cell", "ym"])
    tiles: dict[str, dict] = {}
    for cell, g in d.groupby("cell", sort=True):
        parent = parent_fn(cell)
        t = tiles.setdefault(parent, {"months": MONTHS, "unit": unit, "cells": {}})
        t["cells"][cell] = {
            "p": [int(round(v * 100)) for v in g["p"]],
            "q10": [int(round(v * 10)) for v in g["q10"]],
            "q50": [int(round(v * 10)) for v in g["q50"]],
            "q90": [int(round(v * 10)) for v in g["q90"]],
        }
        if "normal" in g.columns:
            t["cells"][cell]["normal"] = [int(round(v * 10)) for v in g["normal"]]
    return tiles


# ---------------------------------------------------------------- portão (PREVISAO §3)
def check_gate(skill: dict) -> dict:
    """Portão do CP5: BSS > 0 contra climatologia E contra D27 (geral) E erro em log do modelo
    menor que o da climatologia em ≥ 3 dos 5 anos de teste. Devolve o detalhe por regra."""
    years = skill.get("years", {})
    overall = skill.get("overall", {})
    missing = [y for y in TEST_YEARS if y not in years]
    keys_missing = [k for k in SKILL_KEYS if k not in overall]
    beats = [y for y in TEST_YEARS if y in years
             and years[y].get("log_err_model", float("inf")) < years[y].get("log_err_clim", float("-inf"))]
    rules = {
        "bss_clim_gt_0": overall.get("bss_clim", -1) > 0,
        "bss_d27_gt_0": overall.get("bss_d27", -1) > 0,
        "log_err_beats_clim_3_of_5": len(beats) >= 3,
        "all_test_years_present": not missing,
    }
    return {"passes": all(rules.values()), "rules": rules, "years_beating_clim": beats,
            "missing_years": missing, "missing_overall_keys": keys_missing}


def write_json(obj: dict, path: Path) -> float:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=SEP, ensure_ascii=False)
    return path.stat().st_size / 1e6


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="P3 — export do Fire Outlook 2026 (D35)")
    ap.add_argument("--pred", required=True, help="previsões 2026: cell, month|ym, p, q10, q50, q90")
    ap.add_argument("--skill", required=True, help="forecast_skill.json do hindcast 2021–2025")
    ap.add_argument("--unit", choices=UNITS, required=True,
                    help="unidade dos quantis: detections (n_harm, D03/D35) ou frp_mw (ΣFRP, D40)")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--expect-cells", type=int, default=0,
                    help="nº de hexágonos esperados (ex.: 31946 da base D42); avisa se faltar")
    args = ap.parse_args(argv)

    d = normalize(load_pred(args.pred))
    info = validate_pred(d)
    print(f"previsões: {info['cells']:,} células × 12 meses · P média {info['p_mean']:.2f} · "
          f"Σ q50 {info['q50_sum']:,.0f} ({args.unit})")
    if args.expect_cells and info["cells"] < args.expect_cells:
        print(f"  AVISO: {info['cells']:,} de {args.expect_cells:,} hexágonos "
              f"({100 * info['cells'] / args.expect_cells:.0f}%) — o resto do Brasil fica sem Outlook")

    skill = json.loads(Path(args.skill).read_text(encoding="utf-8"))
    gate = check_gate(skill)
    if "passes_gate" in skill and bool(skill["passes_gate"]) != gate["passes"]:
        print(f"  AVISO: passes_gate do arquivo = {skill['passes_gate']} × recalculado = {gate['passes']} "
              "→ vale o recalculado")
    skill = {**skill, "passes_gate": gate["passes"], "gate": gate, "unit": args.unit,
             "issued_with_data_until": "2025-12", "year": YEAR}
    print(f"portão: {'APROVADO' if gate['passes'] else 'REPROVADO'} · {gate['rules']} · "
          f"anos com erro < climatologia: {gate['years_beating_clim']}")

    tiles = build_tiles(d, args.unit, parent_fn_default())
    out = Path(args.out)
    sizes = {p: write_json(t, out / f"forecast_{p}.json") for p, t in tiles.items()}
    write_json(skill, out / "forecast_skill.json")
    s = pd.Series(sizes)
    n_back = sum(len(t["cells"]) for t in tiles.values())
    assert n_back == info["cells"], "células perdidas no split"
    print(f"gravados {len(s)} tiles forecast_<pai>.json em {out}: total {s.sum():.2f} MB · "
          f"máx {s.max():.2f} MB · + forecast_skill.json")
    if not gate["passes"]:
        print("  → o app mostra a chance histórica (D27) no lugar do Outlook (R18).")


if __name__ == "__main__":
    main()

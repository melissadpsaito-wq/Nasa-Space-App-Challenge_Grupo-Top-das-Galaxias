"""Previsão P2 (D48) — Fire Outlook 2026 com o RandomForest da equipe (`notebooks/Model`).

O que faz
  1. Hindcast 2021–2025 (origem móvel, PREVISAO §3): para cada ano Y treina o RF só com anos < Y
     e prevê Y com o clima = média por bioma × mês dos anos de treino (em 2026 o clima real não existe).
     Compara com climatologia, D27 e persistência → forecast_skill.json (o portão é recalculado no export).
  2. Previsão 2026: treina em 2016–2025 (ou reaproveita o .pkl com --model-pkl) e prevê 2026 com a
     climatologia do clima 2016–2025 → forecast_2026.csv (cell, month, p, q10, q50, q90, normal).

Saída por célula × mês, a partir das árvores do RF (cada árvore = um cenário):
  p      = fração das árvores com previsão > normal
  q10/q50/q90 = percentis 10/50/90 das previsões das árvores (MW)
  normal = mediana do ΣFRP harmonizado da célula no mês, anos 2003..Y−1 (sem vazamento, PREVISAO §1)

Entradas
  --data     base do modelo (saída do notebooks/Model/fileModeling.py, 2016–2025):
             cell, lat, lon, year, month, monthly_frp, precipitacao, umidade, temp_max,
             amazonia, caatinga, cerrado, mata_atlantica, pampa, pantanal   (parquet ou csv com ';')
  --history  série ΣFRP harmonizada D40/D42: cell, lat, lon, year, month, frp
             (data/processed/res5_frp/frp_harm_brasil.csv.gz — NÃO abrir/salvar no Excel: corta em 1.048.575 linhas)

Uso (raiz do repo):
  python -m pipeline.forecast.rf_outlook --data notebooks/Model/dataset_model_ready_2016_2025.parquet \
      --history data/processed/res5_frp/frp_harm_brasil.csv.gz
  python -m pipeline.forecast.export_forecast --pred data/processed/forecast/forecast_2026.csv \
      --skill data/processed/forecast/forecast_skill.json --unit frp_mw --expect-cells 31946
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["lat", "lon", "year", "month", "precipitacao", "umidade", "temp_max",
            "amazonia", "caatinga", "cerrado", "mata_atlantica", "pampa", "pantanal"]   # = feature_names_in_ do .pkl
CLIMATE = ["precipitacao", "umidade", "temp_max"]
BIOMES = ["amazonia", "caatinga", "cerrado", "mata_atlantica", "pampa", "pantanal"]
TARGET = "monthly_frp"
TEST_YEARS = [2021, 2022, 2023, 2024, 2025]
FORECAST_YEAR = 2026
HIST_FROM = 2003          # normal e baselines a partir de 2003 (Terra-only fora, PREVISAO §2)
D27_WINDOW = 10
OUT_DEFAULT = "data/processed/forecast"


# ------------------------------------------------------------------ leitura
def read_any(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p, sep=None, engine="python") if ".csv" in p.name else pd.read_csv(p)


def load_data(path: str) -> pd.DataFrame:
    d = read_any(path)
    miss = set(FEATURES + ["cell", TARGET]) - set(d.columns)
    if miss:
        raise ValueError(f"--data sem colunas: {sorted(miss)} (gerar com notebooks/Model/fileModeling.py)")
    d["cell"] = d["cell"].astype(str)
    d[["year", "month"]] = d[["year", "month"]].astype(int)
    return d


def load_history(path: str) -> pd.DataFrame:
    h = pd.read_csv(path, usecols=["cell", "year", "month", "frp"])
    h["cell"] = h["cell"].astype(str)
    return h


def history_cube(h: pd.DataFrame, cells: list[str]) -> tuple[np.ndarray, list[int]]:
    """ΣFRP (MW) em cubo [célula × ano × mês] para as células do modelo; ausente = 0 (D42)."""
    years = list(range(HIST_FROM, FORECAST_YEAR))
    ci = pd.Index(cells)
    h = h[(h.year >= HIST_FROM) & (h.year < FORECAST_YEAR)]
    i = ci.get_indexer(h.cell)
    ok = i >= 0
    cube = np.zeros((len(cells), len(years), 12), dtype=np.float64)
    cube[i[ok], (h.year.to_numpy()[ok] - HIST_FROM), h.month.to_numpy()[ok] - 1] = h.frp.to_numpy()[ok]
    return cube, years


# ------------------------------------------------------------------ baselines (PREVISAO §3)
def normals(cube: np.ndarray, Y: int) -> np.ndarray:
    """Mediana de cada (célula, mês) nos anos 2003..Y−1 → [célula × 12]."""
    k = Y - HIST_FROM
    return np.median(cube[:, :k, :], axis=1)


def baselines(cube: np.ndarray, Y: int) -> dict[str, np.ndarray]:
    """Climatologia (P = fração histórica acima do normal; q50 = normal), D27 (últimos 10 anos)
    e persistência (valor de Y−1). Tudo só com anos < Y. Arrays [célula × 12]."""
    k = Y - HIST_FROM
    past = cube[:, :k, :]
    nrm = np.median(past, axis=1)
    above = past > nrm[:, None, :]
    return {
        "normal": nrm,
        "p_clim": above.mean(axis=1),
        "p_d27": above[:, -D27_WINDOW:, :].mean(axis=1),
        "persist": cube[:, k - 1, :],
    }


# ------------------------------------------------------------------ clima de previsão
def biome_of(d: pd.DataFrame) -> pd.Series:
    """Nome do bioma a partir do one-hot (linha sem bioma → 'none')."""
    oh = d[BIOMES].to_numpy()
    name = np.array(BIOMES)[oh.argmax(axis=1)]
    return pd.Series(np.where(oh.max(axis=1) > 0, name, "none"), index=d.index)


def with_climatology(target: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    """Troca o clima de `target` pela média por bioma × mês de `train` (D48). Sem par → média do mês."""
    t, tr = target.copy(), train
    kb, kt = biome_of(tr), biome_of(t)
    clim = tr.assign(_b=kb).groupby(["_b", "month"])[CLIMATE].mean()
    by_month = tr.groupby("month")[CLIMATE].mean()
    key = pd.MultiIndex.from_arrays([kt, t["month"]])
    vals = clim.reindex(key).to_numpy()
    fb = by_month.reindex(t["month"]).to_numpy()
    vals = np.where(np.isnan(vals), fb, vals)
    t[CLIMATE] = vals
    return t


# ------------------------------------------------------------------ RF → cenários
def make_model(n_estimators=100, max_depth=15, max_samples=None, n_jobs=-1, seed=42):
    from sklearn.ensemble import RandomForestRegressor
    return RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, max_samples=max_samples,
                                 n_jobs=n_jobs, random_state=seed)


def tree_matrix(model, X: pd.DataFrame) -> np.ndarray:
    """Previsão de cada árvore: [n_árvores × n_linhas] (float32 para caber na memória)."""
    Xv = X[FEATURES].to_numpy(dtype=np.float32)
    return np.stack([t.predict(Xv) for t in model.estimators_]).astype(np.float32)


def outlook(T: np.ndarray, normal: np.ndarray) -> dict[str, np.ndarray]:
    """Cenários das árvores → P(acima do normal) e quantis 10/50/90 (≥ 0)."""
    T = np.maximum(T, 0)
    q10, q50, q90 = np.percentile(T, [10, 50, 90], axis=0)
    return {"p": (T > normal[None, :]).mean(axis=0), "q10": q10, "q50": q50, "q90": q90}


# ------------------------------------------------------------------ métricas
def _auc(y: np.ndarray, p: np.ndarray) -> float:
    if y.min() == y.max():
        return float("nan")
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p))


def score_year(y, o, b) -> dict:
    """y = observado (MW); o = saída do modelo; b = baselines alinhados. PREVISAO §3."""
    above = (y > b["normal"]).astype(float)
    brier = lambda p: float(np.mean((p - above) ** 2))
    bm, bc, bd = brier(o["p"]), brier(b["p_clim"]), brier(b["p_d27"])
    lerr = lambda q: float(np.median(np.abs(np.log((q + 1) / (y + 1)))))
    return {
        "n": int(len(y)), "frac_above": float(above.mean()),
        "brier_model": bm, "brier_clim": bc, "brier_d27": bd,
        "bss_clim": 1 - bm / bc if bc > 0 else float("nan"),
        "bss_d27": 1 - bm / bd if bd > 0 else float("nan"),
        "auc": _auc(above, o["p"]),
        "log_err_model": lerr(o["q50"]), "log_err_clim": lerr(b["normal"]), "log_err_persist": lerr(b["persist"]),
        "coverage_80": float(np.mean((y >= o["q10"]) & (y <= o["q90"]))),
        # só célula-mês com fogo no histórico (R23: zeros dominam)
        "active": None,
    }


def _align(df: pd.DataFrame, cells: pd.Index, arr: np.ndarray) -> np.ndarray:
    """Valor [célula × 12] de cada linha (cell, month) de df."""
    return arr[cells.get_indexer(df.cell), df.month.to_numpy() - 1]


def evaluate_year(model, data, cube, cells: pd.Index, Y: int) -> tuple[dict, pd.DataFrame]:
    train = data[data.year < Y]
    test = with_climatology(data[data.year == Y], train)
    b = baselines(cube, Y)
    bl = {k: _align(test, cells, v) for k, v in b.items()}
    o = outlook(tree_matrix(model, test), bl["normal"])
    y = test[TARGET].to_numpy(dtype=float)
    res = score_year(y, o, bl)
    act = (bl["normal"] > 0) | (bl["p_clim"] > 0)                     # célula-mês com fogo antes de Y
    if act.any():
        sub = score_year(y[act], {k: v[act] for k, v in o.items()}, {k: v[act] for k, v in bl.items()})
        sub.pop("active")
        res["active"] = sub
    return res, test.assign(**{k: v for k, v in o.items()}, normal=bl["normal"])


def overall(per_year: dict) -> dict:
    """Média simples dos anos (mesma peso por ano) para as chaves do portão."""
    keys = ["bss_clim", "bss_d27", "auc", "log_err_model", "log_err_clim", "log_err_persist", "coverage_80"]
    return {k: float(np.nanmean([per_year[y][k] for y in per_year])) for k in keys}


# ------------------------------------------------------------------ principal
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="D48 — hindcast 2021–2025 e Outlook 2026 com o RF da equipe")
    ap.add_argument("--data", required=True)
    ap.add_argument("--history", required=True)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--trees", type=int, default=50, help="árvores no hindcast (50 por tempo; declarado)")
    ap.add_argument("--final-trees", type=int, default=100)
    ap.add_argument("--max-depth", type=int, default=15)
    ap.add_argument("--max-samples", type=float, default=0.3,
                    help="fração da base por árvore no hindcast (tempo); 1.0 = igual ao .pkl")
    ap.add_argument("--years", default=",".join(map(str, TEST_YEARS)))
    ap.add_argument("--model-pkl", default=None, help="reaproveitar o .pkl treinado em 2016–2025 para 2026")
    ap.add_argument("--skip-hindcast", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    data = load_data(args.data)
    cells = pd.Index(sorted(data.cell.unique()))
    cube, _ = history_cube(load_history(args.history), list(cells))
    print(f"base: {len(data):,} linhas · {len(cells):,} células · {data.year.min()}–{data.year.max()} · "
          f"histórico {HIST_FROM}–{FORECAST_YEAR - 1}")

    skill = {"model": "RandomForestRegressor (D48)", "target": "sum FRP harmonized, MW (D40)",
             "features": FEATURES, "climate_in_test_year": "mean by biome x month of training years",
             "hindcast": {"trees": args.trees, "max_depth": args.max_depth, "max_samples": args.max_samples},
             "years": {}}
    if not args.skip_hindcast:
        rows = []
        for Y in [int(y) for y in args.years.split(",")]:
            t0 = time.time()
            train = data[data.year < Y]
            m = make_model(args.trees, args.max_depth, args.max_samples)
            m.fit(train[FEATURES], train[TARGET])
            res, test = evaluate_year(m, data, cube, cells, Y)
            skill["years"][str(Y)] = res
            rows.append(test[["cell", "year", "month", TARGET, "p", "q10", "q50", "q90", "normal"]])
            print(f"  {Y}: BSS clim {res['bss_clim']:+.3f} · BSS D27 {res['bss_d27']:+.3f} · AUC {res['auc']:.3f} · "
                  f"erro log {res['log_err_model']:.3f} (clim {res['log_err_clim']:.3f}, pers {res['log_err_persist']:.3f}) · "
                  f"cobertura {res['coverage_80']:.2f} · {time.time() - t0:.0f} s")
        skill["overall"] = overall(skill["years"])
        pd.concat(rows).to_csv(out / "hindcast_rows.csv.gz", index=False)
        print(f"geral: {json.dumps({k: round(v, 3) for k, v in skill['overall'].items()})}")

    # ---- previsão 2026
    if args.model_pkl:
        import joblib
        final = joblib.load(args.model_pkl)
        assert list(final.feature_names_in_) == FEATURES, "o .pkl usa outras variáveis"
        skill["final"] = {"source": Path(args.model_pkl).name}
    else:
        final = make_model(args.final_trees, args.max_depth, None)
        final.fit(data[FEATURES], data[TARGET])
        skill["final"] = {"trees": args.final_trees, "max_depth": args.max_depth, "train_years": "2016-2025"}
    last = data[data.year == data.year.max()].copy()
    fut = with_climatology(last.assign(year=FORECAST_YEAR), data)
    nrm = _align(fut, cells, normals(cube, FORECAST_YEAR))
    o = outlook(tree_matrix(final, fut), nrm)
    pred = pd.DataFrame({"cell": fut.cell.to_numpy(), "month": fut.month.to_numpy(), **o, "normal": nrm})
    pred.to_csv(out / "forecast_2026.csv", index=False)
    (out / "forecast_skill.json").write_text(json.dumps(skill, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"2026: {pred.cell.nunique():,} células × 12 meses · P média {pred.p.mean():.2f} · "
          f"Σ q50 {pred.q50.sum():,.0f} MW → {out / 'forecast_2026.csv'} + forecast_skill.json")


if __name__ == "__main__":
    main()

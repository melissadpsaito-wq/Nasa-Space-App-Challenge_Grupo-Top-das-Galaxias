"""Contrato interno da Ciência (Guia 48h v2 §3.1, docs/CONTRATO-CIENCIA.md).

Dona: Melissa. Samuel só consome (R12). Mudar assinatura ou regra = decisão nova (Dxx).

Regras do contrato
------------------
R1  A, B = agg_monthly de UM sensor cada (colunas mínimas: cell:str, ym:int AAAAMM, n:int).
    Linhas ausentes = 0 focos. Use `paired()` para o zero-fill: ninguém densifica por conta própria.
R2  `years` pode repetir ano (bootstrap C4): cada repetição pesa 1 vez a mais.
R3  Meses tocados por `exclude` do YAML saem do ajuste e da nota (`paired()` e `scoring_months()` já fazem).
R4  Dados extras (cfg, passagens 2 km, λ) entram no construtor (`lam`, `Context`), nunca em fit/transform.
    D33: não há bioma. Prior do M1 = k_global(M), a_global(M) (Brasil, mês do calendário).
R5  transform(A, months) usa só a coluna `n` de A (permite encadear Terra→Aqua→S-NPP) e nunca lê B.
R6  Saída de transform: exatamente [cell, ym, n_pred]; n_pred float ≥ 0, sem NaN, na escala do sensor `to`;
    uma linha por (cell, ym) para cell ∈ células vistas no fit ∪ células de A e ym ∈ months.
R7  fit devolve self; fit e transform não alteram A/B (cópia se precisar) e são determinísticos.
R8  λ de produção = `winner()` de validation.json (D31); ninguém escreve λ à mão.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

import numpy as np
import pandas as pd
import json

import yaml

CONFIG = Path("config/sensors.yaml")
OUT_COLS = ["cell", "ym", "n_pred"]


# ---------- configuração ----------
def load_config(path: Path | str = CONFIG) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    cfg["bridges_by_id"] = {b["id"]: b for b in cfg["bridges"]}
    check_config(cfg)
    return cfg


def _next_ym(ym: int) -> int:
    y, m = divmod(ym, 100)
    return ym + 89 if m == 12 else ym + 1


def check_config(cfg: dict) -> None:
    """Coerência do YAML. Roda a cada load_config(): YAML quebrado falha cedo, não no meio do bootstrap."""
    ref, by_id = cfg["reference"], cfg["bridges_by_id"]
    assert len(by_id) == len(cfg["bridges"]), "id de ponte repetido"
    for b in cfg["bridges"]:
        assert set(b["methods"]) <= {"M1", "M2", "M3"}, f"{b['id']}: método desconhecido"
        lo, hi = cfg["sensor_years"][b["from"]], cfg["sensor_years"][b["to"]]
        assert max(lo[0], hi[0]) <= b["fit"][0] and b["fit"][1] <= min(lo[1], hi[1]), f"{b['id']}: fit fora da sobreposição"
        t = b.get("test")
        assert not t or t[0] > b["fit"][1], f"{b['id']}: test deve vir depois do fit"
    for sensor, chain in cfg["chains"].items():
        assert by_id[chain[0]]["from"] == sensor, f"cadeia {sensor} não começa no sensor"
        for x, y in zip(chain, chain[1:]):
            assert by_id[x]["to"] == by_id[y]["from"], f"cadeia {sensor}: {x} → {y} não encaixa"
        assert by_id[chain[-1]]["to"] == ref, f"cadeia {sensor} não chega à referência"
    tl = cfg["timeline"]
    assert tl[0]["from"] == cfg["analysis_period"][0] and tl[-1]["to"] == cfg["analysis_period"][1], "timeline ≠ analysis_period"
    for a, b in zip(tl, tl[1:]):
        assert _next_ym(a["to"]) == b["from"], f"timeline com buraco/sobreposição: {a['to']} → {b['from']}"
    assert all(t["sensor"] == ref or t["sensor"] in cfg["chains"] for t in tl), "sensor da timeline sem cadeia"
    assert set(cfg["strata"]) == {"season", "daynight"}, "D33: estratos = trimestre × dia/noite"


def fit_years(cfg: dict, bridge_id: str) -> list[int]:
    a, b = cfg["bridges_by_id"][bridge_id]["fit"]
    return list(range(a, b + 1))


def test_years(cfg: dict, bridge_id: str) -> list[int]:
    t = cfg["bridges_by_id"][bridge_id].get("test")
    return list(range(t[0], t[1] + 1)) if t else []


def excluded_months(cfg: dict) -> set[int]:
    out: set[int] = set()
    for start, end in cfg.get("exclude", []):
        for p in pd.period_range(start, end, freq="M"):
            out.add(p.year * 100 + p.month)
    return out


# ---------- tempo ----------
def months_of(years) -> list[int]:
    return [y * 100 + m for y in sorted(set(years)) for m in range(1, 13)]


def month_of_year(ym) -> np.ndarray:
    return np.asarray(ym) % 100


def season_of(ym, cfg: dict) -> np.ndarray:
    lut = {m: s for s, ms in cfg["seasons"].items() for m in ms}
    return np.array([lut[int(m)] for m in month_of_year(ym)], dtype=object)


def scoring_months(cfg: dict, years) -> list[int]:
    ex = excluded_months(cfg)
    return [ym for ym in months_of(years) if ym not in ex]


# ---------- tabelas canônicas ----------
def densify(df: pd.DataFrame, cells, months, col: str = "n") -> pd.DataFrame:
    """cell × ym completo, ausente = 0. Saída: cell, ym, <col>."""
    idx = pd.MultiIndex.from_product([sorted(set(cells)), sorted(set(months))], names=["cell", "ym"])
    s = df.groupby(["cell", "ym"])[col].sum().reindex(idx, fill_value=0)
    return s.reset_index()


def paired(A: pd.DataFrame, B: pd.DataFrame, years: list[int], cfg: dict) -> pd.DataFrame:
    """Tabela de ajuste: cell, ym, rep, a, b — densa, sem meses excluídos, uma cópia por repetição do ano (R1–R3)."""
    ex = excluded_months(cfg)
    uniq = sorted(set(years))
    months = [ym for ym in months_of(uniq) if ym not in ex]
    cells = set(A.loc[(A.ym // 100).isin(uniq), "cell"]) | set(B.loc[(B.ym // 100).isin(uniq), "cell"])
    a = densify(A[A.ym.isin(months)], cells, months).rename(columns={"n": "a"})
    b = densify(B[B.ym.isin(months)], cells, months).rename(columns={"n": "b"})
    base = a.merge(b, on=["cell", "ym"])
    reps = pd.Series(years).value_counts()
    parts = []
    for y, k in reps.items():
        chunk = base[base.ym // 100 == y]
        parts += [chunk.assign(rep=r) for r in range(int(k))]
    out = pd.concat(parts, ignore_index=True) if parts else base.assign(rep=0).iloc[:0]
    return out[["cell", "ym", "rep", "a", "b"]]


# ---------- contexto e interface ----------
@dataclass
class Context:
    """D33: sem bioma. `passes` só o M2 usa (limiar de FRP por trimestre × dia/noite)."""
    cfg: dict
    passes: Callable[[str, list[int]], pd.DataFrame] | None = None   # (sensor, anos) → passagens 2 km (ver passes_reader)
    extra: dict = field(default_factory=dict)


PASS_COLS = ["cell", "ym", "daynight", "frp_max"]


def passes_reader(cfg: dict, path: Path | str | None = None) -> Callable[[str, list[int]], pd.DataFrame]:
    """Leitor de grid2km_pass para o M2: (sensor, anos) → cell, ym, daynight, frp_max, season.

    Uma linha = uma célula de 0,02° numa passagem (DATA_DICTIONARY §5). Meses de `exclude` já saem (R3).
    Anos repetidos (bootstrap) NÃO são replicados aqui: o M2 pondera pelos `years` que recebe no fit.
    """
    path = Path(path or cfg["inputs"]["grid2km_pass"])
    ex = excluded_months(cfg)

    def read(sensor: str, years) -> pd.DataFrame:
        months = [ym for ym in months_of(years) if ym not in ex]
        df = pd.read_parquet(path, columns=["sensor", *PASS_COLS],
                             filters=[("sensor", "==", sensor), ("ym", "in", months)])
        df = df[(df.sensor == sensor) & df.ym.isin(months)][PASS_COLS].reset_index(drop=True)   # garante sem pushdown
        return df.assign(season=season_of(df.ym, cfg))

    return read


def winner(cfg: dict, bridge_id: str, path: Path | str | None = None) -> dict | None:
    """{"method", "lam"} vencedor da ponte em validation.json (Samuel, D31). None se ainda não existe."""
    path = Path(path or cfg["outputs"]["validation"])
    if not path.exists():
        return None
    w = json.loads(path.read_text(encoding="utf-8")).get(bridge_id, {}).get("winner")
    if w is not None:
        assert w["method"] in cfg["bridges_by_id"][bridge_id]["methods"] + ["raw", "global"], f"{bridge_id}: vencedor {w}"
        assert w.get("lam") is None or w["lam"] in cfg["lambda_grid"], f"{bridge_id}: λ fora de lambda_grid"
    return w


@runtime_checkable
class Bridge(Protocol):
    name: str                                 # "M1", "M2", "raw", "global", "M3"

    def fit(self, A: pd.DataFrame, B: pd.DataFrame, years: list[int]) -> "Bridge": ...

    def transform(self, A: pd.DataFrame, months: list[int] | None = None) -> pd.DataFrame: ...   # cell, ym, n_pred


def default_months(A: pd.DataFrame, months) -> list[int]:
    return sorted(months) if months is not None else months_of(A.ym // 100)


def compose(bridges: list[Bridge]) -> Callable[[pd.DataFrame, list[int] | None], pd.DataFrame]:
    """Encadeia pontes já ajustadas (ex.: terra_aqua → aqua_snpp)."""
    def run(A: pd.DataFrame, months: list[int] | None = None) -> pd.DataFrame:
        x = A[["cell", "ym", "n"]]
        for br in bridges:
            x = br.transform(x, months).rename(columns={"n_pred": "n"})
        return x.rename(columns={"n": "n_pred"})
    return run


def build_chain(sensor: str, make: Callable[[str], Bridge], data: Callable[[str], pd.DataFrame], cfg: dict):
    """make(bridge_id) → ponte nova; data(sensor) → agg_monthly do sensor. Ajusta cada elo na sua janela."""
    fitted = []
    for bid in cfg["chains"][sensor]:
        b = cfg["bridges_by_id"][bid]
        fitted.append(make(bid).fit(data(b["from"]), data(b["to"]), fit_years(cfg, bid)))
    return compose(fitted)


# ---------- conformidade (rodar em toda ponte nova: M1, M2, baselines, M3) ----------
def check_output(out: pd.DataFrame, cells, months) -> None:
    assert list(out.columns) == OUT_COLS, f"colunas {list(out.columns)} ≠ {OUT_COLS}"
    assert out.ym.dtype.kind == "i" and out.n_pred.dtype.kind == "f", "tipos: ym int, n_pred float"
    assert not out.n_pred.isna().any(), "n_pred com NaN"
    assert (out.n_pred >= 0).all(), "n_pred negativo"
    assert not out.duplicated(["cell", "ym"]).any(), "(cell, ym) duplicado"
    need = pd.MultiIndex.from_product([sorted(set(cells)), sorted(set(months))])
    got = pd.MultiIndex.from_frame(out[["cell", "ym"]])
    assert need.difference(got).empty, "faltam (cell, ym) na saída"


def check_bridge(bridge: Bridge, A: pd.DataFrame, B: pd.DataFrame, years: list[int], A_new: pd.DataFrame,
                 cfg: dict, uses_features: bool = False) -> None:
    """uses_features=True só para M3 (ML): lê frp_mean etc. e por isso só pode ser o 1º elo de uma cadeia."""
    assert isinstance(bridge, Bridge)
    snap = (A.copy(), B.copy(), A_new.copy())
    assert bridge.fit(A, B, years) is bridge, "fit deve devolver self"
    months = months_of(A_new.ym // 100)
    out = bridge.transform(A_new, months)
    fit_cells = set(paired(A, B, years, cfg).cell)
    check_output(out, fit_cells | set(A_new.cell), months)                                  # R6
    pd.testing.assert_frame_equal(out, bridge.transform(A_new, months), obj="determinismo")
    if not uses_features:
        pd.testing.assert_frame_equal(bridge.transform(A_new[["cell", "ym", "n"]], months), out, obj="R5: só usa n")
    for before, after in zip(snap, (A, B, A_new)):
        pd.testing.assert_frame_equal(before, after, obj="entrada alterada")

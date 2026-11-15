"""Dados 2.4 — export da série harmonizada para o app (DATA_DICTIONARY §3, §6, §10).

Entrada : harm_series.parquet  (cell, ym, n_harm, n_raw, lo, hi, low_conf, src)
          produto = res 5 (D36): data/processed/res5/harm_series.parquet
Saída   : app/public/data/harm_<parent>.json  (tiles por célula-pai H3 res 2, R06)
          ou app/public/data/harm_monthly.json (arquivo único: Pantanal / áreas pequenas)

Regras do contrato (§3):
  - "months" = 200011 … 202512 (período fechado, D33), todos os vetores alinhados com ele;
  - cells / raw / lo / hi = valor × 10, arredondado, inteiro; low_conf = 0/1;
  - células sem fogo (n_harm e n_raw zerados no período) omitidas;
  - "src" = sensor que fornece cada mês (§8: TERRA 200011–200206 · AQUA 200207–201201 · SNPP 201202–202512).
Cada tile tem o mesmo formato do arquivo único (§6), com "months" e "src" repetidos.

Uso (raiz do repo):
  python -m pipeline.export                                   # res 5 Brasil → tiles
  python -m pipeline.export --harm data/processed/pantanal/harm_series.parquet --mode single
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HARM_DEFAULT = "data/processed/res5/harm_series.parquet"
OUT_DEFAULT = "app/public/data"
YM_START, YM_END = 200011, 202512          # D33
PARENT_RES = 2                              # R06 / D28
MAX_FILE_MB = 5.0                           # R06
KEYS = ("cells", "raw", "lo", "hi")         # vetores × 10
COLS = {"cells": "n_harm", "raw": "n_raw", "lo": "lo", "hi": "hi"}
SEP = (",", ":")


def month_range(start: int = YM_START, end: int = YM_END) -> list[int]:
    """AAAAMM de start a end, inclusive."""
    y, m = divmod(start, 100)
    out = []
    while y * 100 + m <= end:
        out.append(y * 100 + m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def timeline_src(ym: int) -> str:
    """Fonte por mês do contrato (§8) — usada quando a série não traz o mês."""
    if ym <= 200206:
        return "TERRA"
    if ym <= 201201:
        return "AQUA"
    return "SNPP"


def src_by_month(harm: pd.DataFrame, months: list[int]) -> list[str]:
    """Sensor mais frequente por mês na série; fallback = linha do tempo do contrato."""
    if "src" in harm.columns and len(harm):
        mode = harm.groupby("ym")["src"].agg(lambda s: s.value_counts().index[0]).to_dict()
    else:
        mode = {}
    return [str(mode.get(m, timeline_src(m))) for m in months]


def build_payload(harm: pd.DataFrame, months: list[int] | None = None) -> dict:
    """Série longa (cell × ym) → dicionário no formato §3 (um arquivo)."""
    months = months or month_range()
    need = {"cell", "ym", "n_harm", "n_raw", "lo", "hi", "low_conf"}
    miss = need - set(harm.columns)
    if miss:
        raise ValueError(f"harm_series sem colunas do contrato: {sorted(miss)}")

    h = harm[harm.ym.isin(months)].copy()
    out_of_range = len(harm) - len(h)
    if out_of_range:
        print(f"  aviso: {out_of_range} linhas fora de {months[0]}–{months[-1]} ignoradas")

    cells, ci = np.unique(h.cell.astype(str).to_numpy(), return_inverse=True)
    mi = np.searchsorted(np.asarray(months), h.ym.to_numpy())
    shape = (len(cells), len(months))

    mats = {}
    for key, col in COLS.items():
        a = np.zeros(shape, dtype=np.float64)
        np.add.at(a, (ci, mi), h[col].fillna(0).to_numpy(dtype=np.float64))
        mats[key] = np.rint(10 * a).astype(np.int64)
    lc = np.zeros(shape, dtype=np.int64)
    np.maximum.at(lc, (ci, mi), h.low_conf.fillna(0).astype(int).to_numpy())

    keep = (mats["cells"].sum(axis=1) + mats["raw"].sum(axis=1)) > 0   # células sem fogo omitidas
    payload = {"months": list(months)}
    for key in KEYS:
        payload[key] = {c: row.tolist() for c, row, k in zip(cells, mats[key], keep) if k}
    payload["low_conf"] = {c: row.tolist() for c, row, k in zip(cells, lc, keep) if k}
    payload["src"] = src_by_month(h, months)
    return payload


def h3_parent(res: int = PARENT_RES):
    import h3  # v4; import tardio para os testes não dependerem dele
    return lambda cell: h3.cell_to_parent(cell, res)


def split_tiles(payload: dict, parent_fn) -> dict[str, dict]:
    """Um payload §3 por célula-pai (§6)."""
    groups: dict[str, list[str]] = {}
    for c in payload["cells"]:
        groups.setdefault(parent_fn(c), []).append(c)
    tiles = {}
    for p, cs in groups.items():
        t = {"months": payload["months"]}
        for key in (*KEYS, "low_conf"):
            t[key] = {c: payload[key][c] for c in cs}
        t["src"] = payload["src"]
        tiles[p] = t
    return tiles


def validate(payload: dict) -> int:
    """Contrato §3: vetores alinhados, inteiros, lo ≤ hi, low_conf 0/1, mesmas células.
    Devolve quantas célula-mês têm o harmonizado fora de [lo, hi] (aviso, não erro: o
    bootstrap da 3.4 pode não envolver a estimativa pontual)."""
    n = len(payload["months"])
    assert payload["months"] == sorted(payload["months"]), "months fora de ordem"
    assert len(payload["src"]) == n, "src desalinhado"
    ids = set(payload["cells"])
    for key in (*KEYS, "low_conf"):
        assert set(payload[key]) == ids, f"{key}: células diferentes de cells"
        for c, v in payload[key].items():
            assert len(v) == n, f"{key}[{c}] com {len(v)} ≠ {n} meses"
            assert all(isinstance(x, int) and x >= 0 for x in v), f"{key}[{c}] não inteiro ≥ 0"
    outside = 0
    for c in ids:
        assert set(payload["low_conf"][c]) <= {0, 1}, f"low_conf[{c}] fora de 0/1"
        lo, mid, hi = payload["lo"][c], payload["cells"][c], payload["hi"][c]
        assert all(a <= d for a, d in zip(lo, hi)), f"lo > hi em {c}"
        outside += sum(not (a <= b <= d) for a, b, d in zip(lo, mid, hi))
    return outside


def conservation(harm: pd.DataFrame, payload: dict, months: list[int]) -> dict:
    """Σ exportado ÷ 10 contra Σ da série (erro de arredondamento ≤ 0,05 por célula-mês)."""
    h = harm[harm.ym.isin(months)]
    res = {}
    for key, col in COLS.items():
        exp = sum(sum(v) for v in payload[key].values()) / 10
        src = float(h[col].fillna(0).sum())
        tol = 0.05 * h[["cell", "ym"]].drop_duplicates().shape[0] + 1e-6
        assert abs(exp - src) <= tol, f"conservação {key}: export {exp:.1f} × série {src:.1f}"
        res[key] = (src, exp)
    return res


def write_json(obj: dict, path: Path) -> float:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=SEP)
    return path.stat().st_size / 1e6


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Dados 2.4 — export para o app")
    ap.add_argument("--harm", default=HARM_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--mode", choices=["auto", "tiles", "single"], default="auto",
                    help="auto = tiles se o arquivo único passar de 5 MB (R06)")
    ap.add_argument("--parent-res", type=int, default=PARENT_RES)
    args = ap.parse_args(argv)

    harm = pd.read_parquet(args.harm)
    months = month_range()
    print(f"série: {args.harm} · {harm.cell.nunique()} células · {len(harm):,} linhas")

    payload = build_payload(harm, months)
    outside = validate(payload)
    if outside:
        print(f"  aviso: {outside} célula-mês com harmonizado fora de [lo, hi]")
    cons = conservation(harm, payload, months)
    print(f"células exportadas: {len(payload['cells'])} · meses: {len(months)} "
          f"({months[0]}–{months[-1]})")
    for k, (s, e) in cons.items():
        print(f"  conservação {k:5s}: série {s:,.1f} · export {e:,.1f}")

    out = Path(args.out)
    mode = args.mode
    if mode == "auto":
        mb = len(json.dumps(payload, separators=SEP)) / 1e6
        mode = "tiles" if mb > MAX_FILE_MB else "single"
        print(f"arquivo único teria {mb:.1f} MB → {mode}")

    if mode == "single":
        mb = write_json(payload, out / "harm_monthly.json")
        print(f"gravado {out / 'harm_monthly.json'} ({mb:.2f} MB)")
        return

    tiles = split_tiles(payload, h3_parent(args.parent_res))
    sizes = {p: write_json(t, out / f"harm_{p}.json") for p, t in tiles.items()}
    s = pd.Series(sizes)
    print(f"gravados {len(s)} tiles res {args.parent_res} em {out}: total {s.sum():.1f} MB · "
          f"mediana {s.median():.2f} · máx {s.max():.2f} MB ({s.idxmax()})")
    big = s[s > MAX_FILE_MB]
    if len(big):
        print(f"  ATENÇÃO R06: {len(big)} tiles > {MAX_FILE_MB} MB: {', '.join(big.index)}")


if __name__ == "__main__":
    main()

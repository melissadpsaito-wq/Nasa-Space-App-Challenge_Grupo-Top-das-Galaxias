"""Previsão climatológica 2026: frequência de fogo por hexágono e mês (últimos N anos).

Para cada célula H3 e mês do ano, conta em quantos anos da janela houve fogo
(ΣFRP harmonizado > --min-frp). A probabilidade de 2026 é hits / n_anos.
Não usa o Random Forest.

Uso (raiz do repo):
    python climatologia_2026.py
    python climatologia_2026.py --y0 2016 --y1 2025 --min-frp 0
Saídas:
    data/processed/forecast/climatologia_2026.csv        (cell, month, hits, n_years, pct)
    app/public/data/climatologia_<pai>.json              (tiles por hexágono-pai H3 res 2)
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def to_str(cell):
    """H3 como string hex (aceita string ou inteiro)."""
    if isinstance(cell, str):
        return cell
    return format(int(cell), "x")


def parent_fn():
    import h3
    if hasattr(h3, "cell_to_parent"):  # h3 v4
        return h3.cell_to_parent
    return h3.h3_to_parent  # h3 v3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data/processed/res5_frp/frp_harm_brasil.csv.gz")
    ap.add_argument("--y0", type=int, default=2016)
    ap.add_argument("--y1", type=int, default=2025)
    ap.add_argument("--min-frp", type=float, default=0.0, help="fogo = frp > este valor")
    ap.add_argument("--parent-res", type=int, default=2)
    ap.add_argument("--csv-out", default="data/processed/forecast/climatologia_2026.csv")
    ap.add_argument("--tiles-out", default="app/public/data")
    ap.add_argument("--expect-cells", type=int, default=31946)
    a = ap.parse_args()

    df = pd.read_csv(a.src, usecols=["cell", "year", "month", "frp"])
    df = df[(df["year"] >= a.y0) & (df["year"] <= a.y1)]
    n_years = a.y1 - a.y0 + 1
    if df["year"].nunique() != n_years:
        sys.exit(f"Anos na base: {sorted(df['year'].unique())}; esperado {n_years} anos.")

    df["hit"] = (df["frp"] > a.min_frp).astype(int)

    # painel completo? cada (cell, month) precisa ter n_years linhas (zeros incluídos)
    size = df.groupby(["cell", "month"]).size()
    incompleto = (size != n_years).sum()
    if incompleto:
        print(f"ATENÇÃO: {incompleto} pares (cell, month) sem {n_years} linhas. "
              "A base pode não ter zeros explícitos; as frequências ficariam infladas.")

    hits = (df.groupby(["cell", "month"])["hit"].sum()
              .unstack(fill_value=0)
              .reindex(columns=range(1, 13), fill_value=0))
    n_cells = len(hits)
    print(f"{n_cells:,} células × 12 meses · janela {a.y0}–{a.y1} ({n_years} anos) · "
          f"fogo = frp > {a.min_frp}")
    if n_cells != a.expect_cells:
        sys.exit(f"Células: {n_cells:,}, esperado {a.expect_cells:,}.")

    # --- CSV longo ---
    long = hits.stack().rename("hits").reset_index()
    long["n_years"] = n_years
    long["pct"] = (100 * long["hits"] / n_years).round(1)
    csv = Path(a.csv_out)
    csv.parent.mkdir(parents=True, exist_ok=True)
    long.to_csv(csv, index=False)

    # --- tiles por hexágono-pai ---
    par = parent_fn()
    tiles = {}
    for cell, row in hits.iterrows():
        c = to_str(cell)
        tiles.setdefault(par(c, a.parent_res), {})[c] = [int(x) for x in row.tolist()]
    out = Path(a.tiles_out)
    out.mkdir(parents=True, exist_ok=True)
    for pai, cells in tiles.items():
        payload = {
            "method": "climatologia",
            "label": "Previsão climatológica 2026 (frequência histórica; não usa o Random Forest)",
            "window": [a.y0, a.y1],
            "n_years": n_years,
            "unit": "anos_com_fogo",
            "months": 12,
            "cells": cells,  # cell -> 12 inteiros (jan..dez); pct = valor / n_years
        }
        (out / f"climatologia_{pai}.json").write_text(
            json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    tot = sum((out / f"climatologia_{p}.json").stat().st_size for p in tiles) / 1e6
    print(f"{len(tiles)} tiles em {out} ({tot:.2f} MB) · CSV: {csv}")
    print("pct médio por mês (Brasil):")
    print((100 * hits.mean() / n_years).round(1).to_string())


if __name__ == "__main__":
    main()

"""2.1 ingest — acha os CSVs anuais por país do FIRMS (soltos ou dentro dos ZIPs), limpa e grava Parquet.

Uso:
  python -m pipeline.ingest --area pantanal            # piloto (sáb tarde) -> data/clean_pantanal/
  python -m pipeline.ingest --area brasil              # Brasil inteiro (D28) -> data/clean/
  python -m pipeline.ingest --area brasil --years 2025 # conferir contra claude/08-fatos-dados

Entrada esperada em --raw (qualquer profundidade): arquivos `<produto>_<ano>_<País>.csv`
(ex.: modis_2020_Brazil.csv, viirs-snpp_2020_Brazil.csv, viirs-jpss1_2020_Brazil.csv) ou ZIPs que os contenham.
Saídas: <out>/<SENSOR>/<ano>.parquet · <out>/filter_log.csv · <out>/manifest.csv
"""
from __future__ import annotations

import argparse
import os
import re
import time
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

from pipeline import clean

AREAS = {"pantanal": (-22.5, -15.5, -59.5, -54.5), "brasil": None}  # lat_min, lat_max, lon_min, lon_max
PRODUCTS = {"modis": "modis", "viirs-snpp": "viirs", "viirs-jpss1": "viirs", "viirs-noaa21": "viirs"}
ISO3 = {"BRA": "Brazil", "BOL": "Bolivia", "PRY": "Paraguay"}
NAME = re.compile(r"(?P<prod>modis|viirs-snpp|viirs-jpss1|viirs-noaa21)_(?P<year>\d{4})_(?P<country>[A-Za-z_]+)\.csv$")

# Brasil 2025 após filtros, medido em 13/11 (claude/08-fatos-dados) — sanidade do clean
EXPECTED_BR_2025 = {"TERRA": 81_436, "AQUA": 140_750, "SNPP": 762_985, "N20": 748_387}


def discover(raw: Path, country: str, years: set[int], cache: Path) -> list[dict]:
    """Lista (produto, ano, caminho do CSV). Extrai do ZIP só o CSV do país (bruto continua intocado)."""
    found: dict[tuple, Path] = {}
    for p in sorted(raw.rglob("*")):
        if p.suffix.lower() == ".csv":
            m = NAME.search(p.name)
            if m and m["country"] == country and int(m["year"]) in years:
                found.setdefault((m["prod"], int(m["year"])), p)
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                for member in z.namelist():
                    m = NAME.search(member)
                    if not (m and m["country"] == country and int(m["year"]) in years):
                        continue
                    key = (m["prod"], int(m["year"]))
                    if key in found:
                        continue
                    dst = cache / m["prod"] / Path(member).name
                    if not dst.exists() or dst.stat().st_size != z.getinfo(member).file_size:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(member) as fin, open(dst, "wb") as fout:
                            fout.write(fin.read())
                    found[key] = dst
    return [{"product": k[0], "year": k[1], "path": v} for k, v in sorted(found.items())]


def parse_years(s: str) -> set[int]:
    a, _, b = s.partition("-")
    return set(range(int(a), int(b or a) + 1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw", type=Path)
    ap.add_argument("--area", default="pantanal", choices=AREAS)
    ap.add_argument("--country", default=os.getenv("COUNTRY", "Brazil"))
    ap.add_argument("--years", default="2000-2025")
    ap.add_argument("--out", type=Path, help="padrão: data/clean (brasil) ou data/clean_<area>")
    a = ap.parse_args()

    country = ISO3.get(a.country.upper(), a.country)
    out = a.out or Path("data/clean" if a.area == "brasil" else f"data/clean_{a.area}")
    out.mkdir(parents=True, exist_ok=True)
    files = discover(a.raw, country, parse_years(a.years), Path("data/interim/_csv"))
    if not files:
        raise SystemExit(f"Nenhum CSV '<produto>_<ano>_{country}.csv' encontrado em {a.raw}")

    print(f"área={a.area} bbox={AREAS[a.area]} país={country} arquivos={len(files)} saída={out}")
    con = duckdb.connect()
    logs, manifest, written = [], [], set()
    for f in files:
        t0 = time.time()
        info = clean.stage(con, f["path"], PRODUCTS[f["product"]], AREAS[a.area])
        log = clean.filter_log(con, f["path"].name)
        parts = clean.write_partitions(con, out, written)
        logs.append(log)
        kept = sum(n for *_, n in parts)
        raw_n = int(log.loc[log.step == "parse", "rows_in"].sum())
        manifest.append({"file": f["path"].name, "product": f["product"], "year": f["year"],
                         "rows_raw": raw_n, "rows_kept": kept, "has_type": info["has_type"],
                         "partitions": ";".join(f"{s}/{y}" for s, y, _ in parts),
                         "seconds": round(time.time() - t0, 1)})
        warn = "" if info["has_type"] else "  ⚠ sem coluna `type`"
        print(f"  {f['path'].name:<32} {raw_n:>10,} -> {kept:>9,}  ({time.time() - t0:.1f}s){warn}")

    log = pd.concat(logs, ignore_index=True)
    log.to_csv(out / "filter_log.csv", index=False)
    pd.DataFrame(manifest).to_csv(out / "manifest.csv", index=False)
    summarize(log, a.area)


def summarize(log: pd.DataFrame, area: str) -> None:
    unm = log[log.sensor.str.startswith("UNMAPPED")]
    if len(unm):
        print("\n⚠ satélites não mapeados:", unm.sensor.unique().tolist())
    final = log[log.step == "conf"]
    pv = final.pivot_table(index="year", columns="sensor", values="rows_out", aggfunc="sum", fill_value=0)
    print("\nFocos limpos por sensor × ano\n", pv.to_string())
    eff = log.groupby(["sensor", "step"], sort=False)[["rows_in", "removed"]].sum()
    eff["pct_removed"] = (100 * eff.removed / eff.rows_in.where(eff.rows_in > 0)).round(2)
    print("\nEfeito de cada filtro (todos os anos)\n", eff.to_string())
    if area == "brasil" and 2025 in set(final.year):
        got = final[final.year == 2025].groupby("sensor").rows_out.sum()
        print("\nConferência Brasil 2025 vs 08-fatos-dados")
        for s, exp in EXPECTED_BR_2025.items():
            g = int(got.get(s, 0))
            print(f"  {s:<6} esperado {exp:>9,}  obtido {g:>9,}  diff {100 * (g - exp) / exp:+.2f}%")


if __name__ == "__main__":
    main()

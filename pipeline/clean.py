"""2.1 clean — um CSV FIRMS -> schema único (DATA_DICTIONARY §1) + log de filtros.

Filtros (DATA_GOVERNANCE, D12–D14), aplicados nesta ordem:
  parse  : campos essenciais válidos e satélite mapeado
  date   : ts >= 2000-11-01 (Guia MODIS C6 §7.2.1)
  bbox   : só se houver área (piloto Pantanal)
  type   : type = 0 (vegetação presumida)
  conf   : MODIS confidence >= 30 · VIIRS confidence in {n, h}
Não deduplica VIIRS: a diferença de contagem é o que as pontes calibram.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

MIN_TS = "2000-11-01"
STEPS = ["raw", "parse", "date", "bbox", "type", "conf"]
OUT_COLS = "sensor, ts, latitude, longitude, frp, daynight, pixel_area"

SAT_CASE = {
    "modis": "CASE upper(trim(satellite)) WHEN 'TERRA' THEN 'TERRA' WHEN 'T' THEN 'TERRA' "
             "WHEN 'AQUA' THEN 'AQUA' WHEN 'A' THEN 'AQUA' END",
    "viirs": "CASE upper(trim(satellite)) WHEN 'N' THEN 'SNPP' WHEN 'N20' THEN 'N20' "
             "WHEN '1' THEN 'N20' WHEN 'N21' THEN 'N21' END",
}
CONF_OK = {
    "modis": "TRY_CAST(conf_raw AS INTEGER) >= 30",
    "viirs": "conf_raw IN ('n', 'h')",
}


def _q(path: Path) -> str:
    return str(path).replace("'", "''")


def stage(con, path: Path, kind: str, bbox: tuple | None) -> dict:
    """Cria a tabela temporária `stg` com colunas tipadas e flags de cada filtro."""
    src = f"read_csv('{_q(path)}', all_varchar=true, header=true)"
    cols = {r[0].lower() for r in con.sql(f"DESCRIBE SELECT * FROM {src}").fetchall()}
    has_type = "type" in cols  # arquivos NRT não têm `type`
    bbox_sql = ("TRUE" if bbox is None else
                f"latitude BETWEEN {bbox[0]} AND {bbox[1]} AND longitude BETWEEN {bbox[2]} AND {bbox[3]}")
    con.sql(f"""
      CREATE OR REPLACE TEMP TABLE stg AS
      WITH r AS (
        SELECT {SAT_CASE[kind]}                                   AS sensor,
               trim(satellite)                                    AS sat_raw,
               TRY_CAST(latitude  AS DOUBLE)                      AS latitude,
               TRY_CAST(longitude AS DOUBLE)                      AS longitude,
               try_strptime(trim(acq_date) || ' ' ||
                            lpad(replace(trim(acq_time), ':', ''), 4, '0'),
                            '%Y-%m-%d %H%M')                      AS ts,
               TRY_CAST(frp AS FLOAT)                             AS frp,
               upper(trim(daynight))                              AS daynight,
               CAST(TRY_CAST(scan AS DOUBLE) * TRY_CAST(track AS DOUBLE) AS FLOAT) AS pixel_area,
               {"TRY_CAST(type AS INTEGER)" if has_type else "NULL::INTEGER"} AS type_,
               lower(trim(confidence))                            AS conf_raw,
               trim(version)                                      AS version
        FROM {src}),
      f AS (
      SELECT *,
             coalesce(sensor IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
                      AND ts IS NOT NULL AND frp IS NOT NULL AND daynight IN ('D','N'), FALSE) AS f_parse,
             coalesce(ts >= TIMESTAMP '{MIN_TS}', FALSE)                                    AS f_date,
             coalesce({bbox_sql}, FALSE)                                                    AS f_bbox,
             {"coalesce(type_ = 0, FALSE)" if has_type else "TRUE"}                         AS f_type,
             coalesce({CONF_OK[kind]}, FALSE)                                               AS f_conf
      FROM r)
      SELECT *, f_parse AND f_date AND f_bbox AND f_type AND f_conf AS keep FROM f""")
    return {"has_type": has_type}


def filter_log(con, file_tag: str) -> pd.DataFrame:
    """Linhas que sobrevivem a cada etapa (cumulativo), por satélite bruto × ano. Formato longo."""
    w = pd.DataFrame(con.sql("""
      SELECT coalesce(sensor, 'UNMAPPED:' || coalesce(sat_raw, '?')) AS sensor,
             year(ts) AS year,
             count(*)                                                        AS raw,
             count(*) FILTER (WHERE f_parse)                                 AS parse,
             count(*) FILTER (WHERE f_parse AND f_date)                      AS date,
             count(*) FILTER (WHERE f_parse AND f_date AND f_bbox)           AS bbox,
             count(*) FILTER (WHERE f_parse AND f_date AND f_bbox AND f_type) AS type,
             count(*) FILTER (WHERE keep)                                    AS conf,
             string_agg(DISTINCT version, ';')                               AS versions
      FROM stg GROUP BY ALL ORDER BY ALL""").df())
    rows = []
    for _, r in w.iterrows():
        for prev, step in zip(STEPS[:-1], STEPS[1:]):
            rows.append({"file": file_tag, "sensor": r.sensor, "year": r.year, "step": step,
                         "rows_in": int(r[prev]), "rows_out": int(r[step]),
                         "removed": int(r[prev] - r[step]),
                         "pct_removed": round(100 * (r[prev] - r[step]) / r[prev], 2) if r[prev] else 0.0,
                         "versions": r.versions})
    return pd.DataFrame(rows)


def write_partitions(con, out_root: Path, written: set) -> list[tuple[str, int, int]]:
    """Grava data/clean/<sensor>/<ano>.parquet a partir das linhas `keep` de `stg`."""
    parts = con.sql("SELECT sensor, year(ts) y, count(*) n FROM stg WHERE keep GROUP BY ALL ORDER BY ALL").fetchall()
    for sensor, y, n in parts:
        if (sensor, y) in written:
            raise RuntimeError(f"{sensor}/{y} já foi gravado por outro arquivo nesta execução (fonte duplicada?)")
        written.add((sensor, y))
        dst = out_root / sensor / f"{y}.parquet"
        dst.parent.mkdir(parents=True, exist_ok=True)
        con.sql(f"""COPY (SELECT {OUT_COLS} FROM stg
                         WHERE keep AND sensor = '{sensor}' AND year(ts) = {y} ORDER BY ts)
                    TO '{_q(dst)}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    return parts

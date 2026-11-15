# Contrato de dados

Congelar no CP1 (sáb 15:00, D23). Mudanças exigem decisão registrada (Dados + Front).

## 1. `data/clean/<sensor>/<ano>.parquet` (focos limpos)
| Coluna | Tipo | Descrição |
|---|---|---|
| sensor | str | TERRA, AQUA, SNPP, N20, N21 |
| ts | timestamp UTC | `acq_date` + `acq_time` (HHMM com zfill(4)) |
| latitude, longitude | float64 | graus |
| frp | float32 | Fire Radiative Power (MW) |
| daynight | str | D / N |
| pixel_area | float32 | scan × track (km²) |
Mapeamentos: MODIS `satellite` Terra/Aqua → TERRA/AQUA; VIIRS `N` → SNPP, `N20` → N20.
Filtros já aplicados: `type = 0`, MODIS conf ≥ 30, VIIRS conf ∈ {n, h}, ts ≥ 2000-11-01. Piloto: mesma estrutura em `data/clean_pantanal/`. Arquivos auxiliares (nota 14/11, sem mudança de schema): `filter_log.csv` (file, sensor, year, step, rows_in, rows_out, removed, pct_removed, versions) e `manifest.csv`.

## 2. `data/interim/agg_monthly.parquet`
| Coluna | Tipo | Descrição |
|---|---|---|
| sensor | str | — |
| cell | str | H3 res 4 |
| ym | int | AAAAMM |
| n | int | focos (após grade comum ~2 km por passagem) |
| frp_mean, frp_p90 | float | FRP médio e percentil 90 |
| night_frac | float | fração noturna |
| pix_area | float | área média do pixel (km²) |

## 3. `app/public/data/harm_monthly.json` (consumido pelo Front)
```json
{
  "months": [200011, 200012, "..."],
  "cells": { "<h3>": [12, 0, 35, "... n_harm × 10, inteiro"] },
  "raw":   { "<h3>": ["... n bruto"] },
  "lo":    { "<h3>": ["... limite inferior × 10"] },
  "hi":    { "<h3>": ["... limite superior × 10"] },
  "low_conf": { "<h3>": [0, 1, "..."] },
  "src": ["TERRA", "AQUA", "...", "SNPP", "N20"]
}
```
Regras: vetores alinhados com `months`; valores multiplicados por 10 e arredondados; células sem fogo omitidas.

## 4. Outros arquivos do app
| Arquivo | Conteúdo |
|---|---|
| `season.json` | `{ "<h3>": { "onset": doy, "peak": doy, "end": doy, "trend_d_decade": float, "p": float } }` |
| `validation.json` | por ponte e método: consistency, r2_log, bias, n_test, vencedor |
| `pettitt.json` | por ponte: % células com quebra (raw, harm) + lista de células |
| `nrt_last7.json` | ~~focos NOAA-20 dos últimos 7 dias~~ — fora por D33 |
| `sensors4.json` | Brasil e áreas prontas: série anual harmonizada de cada sensor (TERRA, AQUA, SNPP, N20) 2000–2025, × 10 inteiro — gráfico "4 satélites, 1 curva" (D33) |
| `consistency_4sat.json` | razão harmonizado/harmonizado por par de sensores e ano (Samuel, D33) |
| `meta.json` | fontes, versões, datas de download, commit do pipeline |

## 5. Arquivos entre Dados e Ciência (proposta — aprovar na revisão das 10:00, R13)
| Arquivo | Colunas mínimas | Escreve | Lê |
|---|---|---|---|
| `data/interim/grid2km_pass.parquet` | sensor, ts, daynight, gy, gx (`floor(lat/0,02)`, `floor(lon/0,02)`), cell (H3 res 4), ym, `frp_max`, n_pix, pix_area · passagem = sensor + ts + daynight · o M2 lê `sensor, cell, ym, daynight, frp_max` (`base.passes_reader`) | Murilo | Melissa |
| `data/processed/harm_series.parquet` | cell, ym, n_harm, n_raw, lo, hi, low_conf, src | Melissa | Murilo |
Resumo do FRP dentro da célula de 2 km: **máximo** (D26, proposta). Unidade de `n_harm`: detecções por célula de 0,02° por passagem, escala S-NPP (D03). Contrato interno Melissa × Samuel: `docs/CONTRATO-CIENCIA.md`.

## 6. Arquivos novos do app (v2)
| Arquivo | Conteúdo | Escreve |
|---|---|---|
| `areas.json` | `[{ "id", "name", "polygon": [[lat, lng], ...], "story" }]` — Pantanal e SP canavieira (D22) | Murilo |
| `harm_<parent>.json` (só se R06 acionar) | Mesmo formato da §3, um arquivo por célula-pai H3 res 2 | Murilo |
| `tests/score_cases.json` | 3 áreas × mês: entrada (vetor da área) e saída esperada (score, razão, pico) | Samuel |

## 7. CSV baixado pelo usuário
`year,month,harmonized,lo,hi,raw,low_conf` — valores já divididos por 10; uma linha por mês da área selecionada.

## 8. Fonte do valor por mês (`src`)
TERRA 200011–200206 (low_conf) · AQUA 200207–201201 · SNPP 201202–202512 (D10, D33). Período fechado: nov/2000 → dez/2025

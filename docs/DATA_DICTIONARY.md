# Contrato de dados

Fixar até sáb 10:00. Mudanças exigem decisão registrada (Dados + Front).

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
| `nrt_last7.json` | focos NOAA-20 dos últimos 7 dias (lat, lon, ts, frp) + contagem do mês corrente por célula |
| `meta.json` | fontes, versões, datas de download, commit do pipeline |

## 5. Arquivos entre Dados e Ciência (proposta — aprovar na revisão das 10:00, R13)
| Arquivo | Colunas mínimas | Escreve | Lê |
|---|---|---|---|
| `data/interim/grid2km_pass.parquet` | sensor, passagem (sensor + ts + daynight), célula 2 km (`floor(lat/0,02)`, `floor(lon/0,02)`), cell (H3 res 4), ym, frp, daynight | Murilo | Melissa |
| `data/interim/cell_biome.parquet` | cell (H3 res 4), bioma (RESOLVE 2017) | Murilo | Melissa, Samuel |
| `data/processed/harm_series.parquet` | cell, ym, n_harm, n_raw, lo, hi, low_conf, src | Melissa | Murilo |
Pendente de decisão de método: resumo do FRP dentro da célula de 2 km (soma ou máximo).

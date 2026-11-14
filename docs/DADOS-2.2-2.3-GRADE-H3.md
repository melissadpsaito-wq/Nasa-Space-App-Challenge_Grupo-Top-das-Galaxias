# Dados 2.2 + 2.3 — Grade 0,02° por passagem + H3 res 4 (Pantanal e Brasil) — concluído sáb 14/11 17:53

Dono: Murilo · Branch `ciencia/m1` (PR aberto → `main`, commit `f30b43d`) · Código: `pipeline/grid.py`, `tests/test_grid.py` · Sem bioma (D33)

## 1. O que a etapa faz
| Passo | Como |
|---|---|
| Ler | `read_parquet('<clean>/*/*.parquet')` (DuckDB), opcional `--years` |
| Peneira (passo 1) | 1 linha por célula 0,02° × passagem (passagem = `sensor + ts + daynight`, conferida pelo `check_method`): `gy = floor(lat/0,02)`, `gx = floor(lon/0,02)`, `frp_max` (D26), `frp_sum` (Σ FRP de todos os pixels, D29 ajustada), `n_pix`, `pix_area` |
| Bairro (passo 2) | Célula H3 res 4 do **centro** de cada célula 0,02° (`h3.latlng_to_cell`, só para as distintas) · `ym = ano·100 + mês` |
| Agregar | `agg_monthly`: `GROUP BY sensor, cell, ym` → `n = count(*)`, `frp_mean`, `frp_p90`, `night_frac`, `pix_area`, `frp_sum` |
| Conferir | Σ `n_pix` = focos limpos e Σ `n` = linhas da grade, por sensor × ano (assert); `grid_log.csv` |

## 2. Como rodar (raiz do repo)
```bat
python -m pip install "h3>=4"
python -m pytest -q tests/test_grid.py
python -m pipeline.grid --area pantanal      :: data/clean_pantanal → data/interim/pantanal/
python -m pipeline.ingest --area brasil      :: 2.3: 48 arquivos, ~40 M linhas, ~1 min
python -m pipeline.grid --area brasil        :: data/clean → data/interim/ (caminhos do sensors.yaml), 19 s
```
Saídas (fora do Git): `grid2km_pass.parquet`, `agg_monthly.parquet`, `grid_log.csv`.

## 3. Resultados
| | Pantanal | Brasil |
|---|---|---|
| Tempo | 1 s | 19 s |
| Conservação | OK (4 sensores × 26 anos) | OK |
| Células H3 | 199 | ~3.700–4.200 por ano |
| Pixels por fogo MODIS / VIIRS | 1,34–1,38 / 2,79–2,94 | 1,25–1,27 / 2,02 |

Brasil — focos limpos e células-passagem:
| Sensor | Focos limpos | Células-passagem |
|---|---|---|
| TERRA | 3.521.179 | 2.805.976 |
| AQUA | 5.840.991 | 4.601.119 |
| SNPP | 17.303.874 | 8.554.315 |
| N20 | 9.711.325 | 4.800.525 |
Ingest Brasil: 2025 = 08-fatos (0,00% nos 4); filtros removem Terra 7,6% · Aqua 5,4% · S-NPP 10,0% · N20 10,3%.

S-NPP/Aqua na grade 0,02° por ano (Brasil): 2012 3,89 · 2013 4,09 · 2014 3,99 · 2015 4,13 · 2016 3,90 · 2017 3,84 · 2018 4,07 · 2019 3,84 · 2020 4,10 · 2021 3,85 · 2022 3,76 · 2023 3,91 · 2024 3,28 · 2025 **3,45** (= `check_method`, por outro caminho ✔).
Por período: 2012–2019 **3,96** · 2020–2021 **3,98** · 2022–2025 3,58. Pantanal: 3,40 · 3,41 · 3,28 (bruto 5,94 · 7,17 · ~7,1).

## 4. Achado (revisa a §6 do `29-dados-2.1`)
O degrau de +20% do bruto em 2020 (Pantanal 5,94 → 7,17) **some na grade** (3,40 → 3,41; Brasil 3,96 → 3,98). Era efeito de pixels por fogo: em anos de muito fogo (2020, 2024) cada incêndio vira mais pixels VIIRS (Pantanal 3,0–3,6 contra 1,9–2,7). A deriva real do Aqua aparece em **2024–2025** (harmonizado +15–23% acima do S-NPP) → R05 atualizado, D30 com motivo revisto, D34.

## 5. Problemas e correções
| Problema | Correção |
|---|---|
| Patch `0004` não estava em Downloads | Arquivos gravados direto na pasta do repo pelo app (pasta conectada) |
| `No module named pipeline.grid` | Consequência do item acima |
| Avisos LF → CRLF no `git add` | Inofensivo (Windows) |

## 6. Pendente
Merge do PR `ciencia/m1` · Samuel/Melissa geram `agg_monthly` na máquina deles (`ingest` + `grid`, ~1 min) ou recebem pelo Drive · DATA_DICTIONARY §2/§5: registrar `frp_sum` (D29, texto a ajustar) · Makefile `grid` com `AREA`.

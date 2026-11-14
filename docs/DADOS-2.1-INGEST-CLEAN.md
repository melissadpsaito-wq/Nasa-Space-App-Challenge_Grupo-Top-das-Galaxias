# Dados 2.1 — Ingest + clean (concluído sáb 14/11 15:13)

Dono: Murilo · Commit `2e66d2e` (branch `dados/ingest-clean`) · Código: `pipeline/ingest.py`, `pipeline/clean.py`, `tests/test_clean.py`

## 1. O que a etapa faz
| Passo | Como |
|---|---|
| Descobrir | Procura `<produto>_<ano>_Brazil.csv` em `--raw` (qualquer profundidade), solto ou dentro dos ZIPs `*_all_countries.zip`. Produtos: `modis`, `viirs-snpp`, `viirs-jpss1` (`viirs-noaa21` aceito) |
| Extrair | Do ZIP sai só o CSV do país → `data/interim/_csv/<produto>/` (cache). O ZIP bruto não é alterado |
| Ler | DuckDB, tudo como texto (`all_varchar`) + `TRY_CAST`: valor inválido vira nulo e é contado, não trava |
| Mapear | `satellite`: Terra/T → TERRA · Aqua/A → AQUA · N → SNPP · N20/1 → N20 · N21 → N21; não mapeado → `UNMAPPED:x` no log |
| Timestamp | `acq_date` + `lpad(acq_time, 4, '0')` → `ts` (UTC, sem fuso) |
| Filtrar (ordem) | 1 parse (campos válidos) · 2 date ≥ 2000-11-01 · 3 bbox (só piloto) · 4 `type = 0` · 5 MODIS conf ≥ 30 / VIIRS conf ∈ {n, h} |
| Não faz | Não deduplica VIIRS (a diferença de contagem é o que as pontes calibram) |
| Gravar | `<out>/<SENSOR>/<ano>.parquet` (ZSTD, ordenado por `ts`), schema `DATA_DICTIONARY` §1 |
| Registrar | `<out>/filter_log.csv` (linhas antes/depois de cada filtro por sensor × ano + `version` FIRMS) · `<out>/manifest.csv` (arquivo, linhas, partições, segundos, presença de `type`) |

## 2. Como rodar (Windows, a partir da raiz do repo)
```bat
python -m pip install duckdb pandas pytest
mklink /J data\raw "C:\Users\muril\Documents\SPACE APP\FIRMS"   :: atalho p/ os ZIPs; remover só com "rmdir data\raw" (sem /s)
python -m pipeline.ingest --area brasil --years 2025            :: conferência → data/clean/
python -m pipeline.ingest --area pantanal                        :: piloto 2000–2025 → data/clean_pantanal/
python -m pytest -q tests/test_clean.py
```
Áreas: `pantanal` = bbox lat −22,5 a −15,5, lon −59,5 a −54,5 aplicado aos arquivos do Brasil (= parte brasileira, D28) · `brasil` = sem bbox. Outro país: `--country` (nome FIRMS ou ISO3 BRA/BOL/PRY).
No CMD não colar `# comentário` depois do comando (vira argumento).

## 3. Entradas encontradas
`C:\Users\muril\Documents\SPACE APP\FIRMS`: `modis_2000…2025_all_countries.zip` (26) · `viirs-snpp_2012…2025` (14) · `viirs-jpss1_2018…2025` (8) = 48 ZIPs. Dentro: `viirs-snpp/2025/viirs-snpp_2025_Brazil.csv` (padrão confirmado).

## 4. Resultado 1 — conferência Brasil 2025 (vs `08-fatos-dados`)
| Sensor | Bruto | type ≠ 0 | conf baixa | Limpo | Esperado 13/11 | Diferença |
|---|---|---|---|---|---|---|
| TERRA | 87.639 | −2.271 (2,59%) | −3.932 (4,61%) | 81.436 | 81.436 | 0,00% |
| AQUA | 149.092 | −2.498 (1,68%) | −5.844 (3,99%) | 140.750 | 140.750 | 0,00% |
| SNPP | 861.621 | −15.939 (1,85%) | −82.697 (9,78%) | 762.985 | 762.985 | 0,00% |
| N20 | 853.909 | −16.042 (1,88%) | −89.480 (10,68%) | 748.387 | 748.387 | 0,00% |
parse e date removeram 0. Tempo: < 1 s por arquivo.
**Frase para Method:** "O pipeline reproduz 100% das contagens de referência (Brasil 2025); os filtros removem ~6% dos focos MODIS e ~11% dos VIIRS."

## 5. Resultado 2 — piloto Pantanal 2000–2025
| Sensor | Bruto (Brasil) | No bbox | type ≠ 0 | conf baixa | Limpo |
|---|---|---|---|---|---|
| TERRA | 3.809.236 | 214.348 (5,6%) | −153 (0,07%) | −13.281 (6,20%) | 200.914 |
| AQUA | 6.173.230 | 266.885 (4,3%) | −336 (0,13%) | −14.571 (5,47%) | 251.978 |
| SNPP | 19.229.379 | 1.005.230 (5,2%) | −5.315 (0,53%) | −86.870 (8,69%) | 913.045 |
| N20 | 10.830.346 | 729.123 (6,7%) | −5.170 (0,71%) | −61.655 (8,52%) | 662.298 |
| **Total** | **40.042.191** | | | | **2.028.235** |
Leitura: parse 0% em ~40 M linhas (26 anos íntegros); date 0% (arquivo MODIS 2000 já começa em nov); `type` remove pouco no Pantanal (sem indústria/gás).

### Focos limpos por ano (Pantanal)
| Ano | AQUA | N20 | SNPP | TERRA | Aqua/Terra | SNPP/Aqua | N20/SNPP |
|---|---|---|---|---|---|---|---|
| 2000 | – | – | – | 708 | | | |
| 2001 | – | – | – | 11.649 | | | |
| 2002 | 18.480 | – | – | 15.905 | | | |
| 2003 | 6.868 | – | – | 5.156 | 1,33 | | |
| 2004 | 13.028 | – | – | 8.592 | 1,52 | | |
| 2005 | 18.451 | – | – | 11.875 | 1,55 | | |
| 2006 | 5.917 | – | – | 4.230 | 1,40 | | |
| 2007 | 16.474 | – | – | 10.329 | 1,59 | | |
| 2008 | 7.570 | – | – | 5.528 | 1,37 | | |
| 2009 | 7.308 | – | – | 5.464 | 1,34 | | |
| 2010 | 14.405 | – | – | 10.059 | 1,43 | | |
| 2011 | 5.917 | – | – | 4.964 | 1,19 | | |
| 2012 | 9.229 | – | 52.679 | 5.867 | 1,57 | 5,71 | |
| 2013 | 5.237 | – | 34.007 | 4.334 | 1,21 | 6,49 | |
| 2014 | 2.702 | – | 15.678 | 2.053 | 1,32 | 5,80 | |
| 2015 | 6.767 | – | 39.510 | 5.030 | 1,35 | 5,84 | |
| 2016 | 7.505 | – | 44.117 | 5.412 | 1,39 | 5,88 | |
| 2017 | 8.194 | – | 48.657 | 5.686 | 1,44 | 5,94 | |
| 2018 | 3.019 | 17.886 | 18.832 | 2.462 | 1,23 | 6,24 | 0,95 |
| 2019 | 15.375 | 91.271 | 91.081 | 11.557 | 1,33 | 5,92 | 1,00 |
| 2020 | 30.028 | 209.592 | 214.881 | 23.991 | 1,25 | 7,16 | 0,98 |
| 2021 | 12.992 | 90.554 | 93.676 | 11.459 | 1,13 | 7,21 | 0,97 |
| 2022 | 2.898 | 20.691 | 20.344 | 2.831 | 1,02 | 7,02 | 1,02 |
| 2023 | 9.373 | 62.536 | 67.137 | 8.065 | 1,16 | 7,16 | 0,93 |
| 2024 | 22.553 | 158.518 | 161.083 | 16.380 | 1,38 | 7,14 | 0,98 |
| 2025 | 1.688 | 11.250 | 11.363 | 1.328 | 1,27 | 6,73 | 0,99 |

| Checagem | Resultado |
|---|---|
| Início de cada sensor | Terra nov/2000 · Aqua 2002 · S-NPP 2012 · N20 2018 ✅ |
| Pico | 2020 nos 4 sensores; 2024 em 2º ✅ |
| N20/SNPP | 0,976 no total (0,93–1,02) ≈ Brasil 0,98 ✅ |
| 2025 muito baixo | Plausível (ano fraco no Pantanal) — confirmar com INPE (V1) 🟡 |

## 6. Achado — deriva de órbita do MODIS (evidência para R05)
| Período | SNPP/Aqua | Aqua/Terra |
|---|---|---|
| 2012–2019 | **5,94** (5,7–6,5) | 1,42 (2003–2019) |
| 2020–2025 | **7,15** (6,7–7,2) | 1,24 |
Degrau de ~+20% em 2020 que não volta: os MODIS detectam relativamente menos, coerente com a deriva de órbita de Aqua e Terra. Consequência: ajustar Aqua→S-NPP em 2012–2021 (sensors.yaml do Guia) mistura os dois regimes → proposta **D30** (ajuste 2012–2019, teste 2020–2021). Terra→Aqua (2003–2010) já está antes da deriva.

> **Revisão 14/11 17:53 (`claude/32` §4):** na grade 0,02° por passagem o degrau some (Pantanal 3,40 → 3,41; Brasil 3,96 → 3,98). O salto do bruto vinha de mais pixels VIIRS por fogo em anos de muito fogo, não da órbita. A deriva real do Aqua aparece em 2024–2025 (+15–23% no harmonizado). D30 segue (teste fora do tempo), com motivo revisto; R05 atualizado.

## 7. Testes (`tests/test_clean.py`) — 4/4 passando
| Teste | Verifica |
|---|---|
| `test_conservation` (Brasil, Pantanal) | Σ linhas nos Parquet por sensor × ano == `rows_out` final do `filter_log` |
| `test_schema_and_values` (Brasil, Pantanal) | Tipos = contrato §1 (sensor VARCHAR, ts TIMESTAMP, lat/lon DOUBLE, frp FLOAT, daynight VARCHAR, pixel_area FLOAT); sensor válido, D/N, ts ≥ 2000-11-01, frp ≥ 0, coordenadas válidas |

## 8. Problemas encontrados e correções
| Problema | Causa | Correção |
|---|---|---|
| `No module named 'duckdb'` | Pacotes não instalados | `python -m pip install duckdb pandas pytest` |
| "Nenhum CSV encontrado" | `data/raw` vazio | `--raw` para a pasta FIRMS ou junction `data\raw` |
| 96 ZIPs alheios copiados para `data/raw` | Exemplo de `copy` genérico (erro do Claude) | `rmdir /s /q data\raw` (só cópias) |
| `fetchone()` inexistente | DuckDB 2.0 removeu o método em relações | `.fetchall()[0]` no teste |
| `git add` falhou | Faltava `pipeline/__init__.py` | `type nul > pipeline\__init__.py` |
| `data/clean_pantanal/` como untracked | `.gitignore` sem a regra | Linha `data/clean_*/` |
| Datas `07/01/2025` no PDF da equipe | Arquivo aberto no Excel | Ler só o CSV original (`AAAA-MM-DD`); prova: parse 0% |

## 9. Saídas e próximos passos
| Saída | Local | Git? |
|---|---|---|
| Focos limpos Brasil 2025 | `data/clean/<SENSOR>/2025.parquet` | não |
| Focos limpos Pantanal 2000–2025 | `data/clean_pantanal/<SENSOR>/<ano>.parquet` | não |
| Log de filtros e manifesto | `filter_log.csv`, `manifest.csv` nas pastas acima | não (vai para a página Method) |
| Código + testes | `pipeline/`, `tests/` | sim (`2e66d2e`) |

Pendente: Makefile com `AREA` · texto da D29 · ~~PR para `main`~~ ✅ · ~~linha em `AI_USAGE.md`~~ ✅ · ~~Brasil 2000–2025 (2.3)~~ ✅ 17:53 · 2026 fora (D33).
Próximo: ~~2.2 grade + H3~~ ✅ (sem bioma, D33) → ver `claude/32-dados-2.2-2.3-grade-h3.md`.

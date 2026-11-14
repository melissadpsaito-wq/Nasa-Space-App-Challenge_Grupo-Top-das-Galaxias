# Ciência 3.2 — M1: razão com encolhimento (sáb 14/11, D32 + D33)

Dona: Melissa · Branch `ciencia/m1` · Código: `pipeline/bridges/m1.py`, `pipeline/bridges/check_method.py` · Testes: `tests/test_m1.py` (9) + M1 com λ ∈ {0, 5, 20, 50} em `tests/test_bridge_contract.py` → 21 passam, 1 pulado sem pyarrow

## 1. Fórmula (Guia v2 §3.2 · D32 · D33 sem bioma)
| Item | Regra |
|---|---|
| k(c,M) | (ΣB⁺ + λ·k_global(M)) / (ΣA⁺ + λ); ⁺ = só meses com A > 0 nos anos de ajuste |
| add_term(c,M) | média de B nos meses com A = 0 |
| Previsão | k·A se A > 0; add_term se A = 0 |
| k_global(M) | ΣB⁺/ΣA⁺ de todas as células no mês M → sem dados: k de todos os meses → 1,0 |
| a_global(M) | média de B nos meses com A = 0 de todas as células → sem dados: 0 |
| Célula sem ΣA⁺ ou nova | k = k_global(M); sem meses A = 0 → add_term = a_global(M) |
| Contrato | `M1(lam, ctx)`; tabela via `base.paired` (zero-fill, pane do Aqua fora, pesos do bootstrap); λ de produção = `base.winner` (R8) |
| Inspeção | `.params()` → cell, M, sa_pos, sb_pos, n_zero, sb_zero, k, add_term · `.global_table()` → M, k_global, a_global |

## 2. Testes
| Teste | Verifica |
|---|---|
| `test_global_prior` | k_global(M) e a_global(M) pela fórmula; mês sem dados → k de todos os meses |
| `test_lambda_extremes` | λ = 0 → razão local; λ → ∞ → k_global(M); λ = 20 = fórmula |
| `test_additive_term_and_no_double_count` | B de mês com A = 0 só no aditivo; λ = 0 conserva ΣB |
| `test_unseen_cell` | célula nova → k_global(M), a_global(M) |
| `test_bootstrap_weights` | ano repetido pesa 2× |
| `test_excluded_months_ignored` | 202008 fora |
| `test_chain_terra_to_snpp` | Terra → Aqua → S-NPP = 8× quando os fatores são 2× e 4× |
| `test_drift_shows_up_in_test` | deriva +20% em 2020+: ajuste 2012–2019 subestima o teste (~0,83) |
| `test_check_method_decomposition` | bruto, grade por passagem, τ e razão ≈ 1 num caso montado à mão |
| `test_bridge_conforms[M1_lam0/5/20/50]` | R1–R7 de `base.check_bridge` |

## 3. Como rodar (raiz do repo, Windows)
```bat
python -m pytest -q tests/test_m1.py tests/test_bridge_contract.py
python -m pipeline.bridges.check_method --clean data/clean --year 2025
python -m pipeline.bridges.m1 --bridge aqua_snpp --lam 20 --agg <agg_monthly do Pantanal>
```
1. `check_method` (pedido pelo Guia antes do M1): esperado bruto 5,42 · 0,02° ≈ 3,45 · com τ → ≈ 1,0. Imprime também razão por mês e prévia do τ por trimestre × dia/noite (insumo do §3.3). Se não bater: rever definição de passagem (`ts` + `daynight`) com Murilo.
2. `m1`: sem `--lam` usa o vencedor de `validation.json`; antes do CP3 sai com erro (λ = 20 só para conferência). Grava `data/interim/m1_params_<ponte>_lam<λ>.parquet` e mostra k_global(M), a_global(M) e Σpred/ΣB no ajuste e no teste (a nota oficial é do Samuel).

## 4. Resultado — `check_method` Brasil 2025 (sáb 16:54) ✅
| Etapa | Razão S-NPP/Aqua | METHOD.md |
|---|---|---|
| Bruto (140.750 Aqua · 762.985 S-NPP) | 5,42 | 5,42 |
| Grade 0,01° por passagem | 3,58 | 3,58 |
| Grade 0,02° por passagem | 3,45 | 3,45 |
| + limiar de FRP τ = 9,4 MW (0,02°) | 1,00 | ≈ 1,0 |
τ na grade 0,01° = 9,8 MW. Razão bruta por mês 3,53–6,43 = `08-fatos`. Definição de passagem (`ts` + `daynight`) confirmada.

Prévia do §3.3 (grade 0,02°, 8 estratos):
| Estrato | Aqua | S-NPP | Razão | τ (MW) |
|---|---|---|---|---|
| DJF D / N | 12.415 / 373 | 33.831 / 7.198 | 2,73 / 19,30 | 8,2 / 6,4 |
| MAM D / N | 6.634 / 417 | 19.510 / 7.055 | 2,94 / 16,92 | 8,1 / 6,2 |
| JJA D / N | 26.052 / 2.507 | 67.558 / 30.513 | 2,59 / 12,17 | 9,2 / 6,1 |
| SON D / N | 59.495 / 5.189 | 160.268 / 64.494 | 2,69 / 12,43 | 10,7 / 6,1 |
Leitura: de dia sobra ~2,7× após a grade; à noite, 12–19× (o MODIS quase não vê fogo noturno fraco). τ noturno ~6 MW, diurno 8–11 MW. Estratificar dia/noite (D33) é necessário. Estratos noturnos de DJF e MAM têm < 420 focos Aqua: τ menos estável.

ΣFRP S-NPP/Aqua (Brasil 2025): bruto 1,17 (meses 0,82–1,60, CV 16%) · Σ frp_max 0,02° 0,76 · dia 0,73 / noite 1,38. Contagem na grade varia menos (CV 12%) → unidade principal segue contagem (D03); ΣFRP = camada extra (D34, depois do CP3). D29: `frp_sum` = Σ FRP de todos os pixels.

## 5. Resultado — grade 2.2 + M1 no Pantanal (sáb 17:45) ✅
Grade (`python -m pipeline.grid --area pantanal`, 1 s): conservação OK nos 4 sensores × 26 anos; 199 células H3 res 4.
| Sensor | Focos limpos | Células-passagem | Pixels por fogo |
|---|---|---|---|
| TERRA | 200.914 | 150.027 | 1,34 |
| AQUA | 251.978 | 182.360 | 1,38 |
| SNPP | 913.045 | 327.495 | 2,79 |
| N20 | 662.298 | 225.249 | 2,94 |

S-NPP/Aqua por período (Pantanal):
| Período | Bruto | Grade 0,02° |
|---|---|---|
| 2012–2019 | 5,94 | 3,40 |
| 2020–2021 | 7,17 | 3,41 |
| 2022–2025 | ~7,1 | 3,28 |
**Achado:** o degrau de +20% visto no bruto (R05, base da D30) some na grade. Em anos de fogo grande (2020, 2024) cada fogo vira mais pixels (VIIRS 3,0–3,6 por fogo × 1,9–2,7 nos outros anos). A "deriva" do bruto parece ser, em boa parte, efeito do tamanho dos fogos, não da órbita → rever D30/R05.

M1 (`--lam 20`, ajuste 2012–2019):
| Item | Valor |
|---|---|
| k_global(M) | 2,04 (mar) → 3,54 (out); maior na estação do fogo |
| a_global(M) | 0,6 (abr) → 2,7 (out) focos/mês onde o Aqua viu 0 |
| Ajuste: Σpred/ΣB | 0,993 |
| Teste 2020–2021 (sem ago–set/2020): Σpred/ΣB | **0,904** |
| Fator global único no mesmo teste | 0,932 |
Leitura: no teste, ΣB/ΣA = 3,64 (sem ago–set/2020) contra 3,40 no ajuste. A razão sobe em anos/meses de muito fogo e o M1 (linear em A) não acompanha. Na soma, o M1 fica atrás do fator global; a nota oficial (mediana do erro por célula-mês, LOYO) é do Samuel e decide o CP3 (`beats_global`).

## 6. Pendências
| Item | Dono |
|---|---|
| Sensibilidade a λ (5, 50) no Pantanal | Melissa |
| Samuel: rodar LOYO + teste com M1 e baselines → `validation.json` | Samuel |
| Rever D30/R05 com o achado da grade | Capitão |
| Aprovar D30, D31, D32 (D32 já com prior global por D33) | Capitão |
| λ vencedor via `validation.json` (CP3, 23:30) | Samuel |

## 7. Leitura esperada
k(c,M) de meses com pouco fogo sai abaixo do k global (os meses com A = 0 vão para o aditivo). Com λ = 0 o total do ajuste é conservado. No sintético com deriva de +20% em 2020+, o teste 2020–2021 fica em Σpred/ΣB ≈ 0,85 — é a assinatura que esperamos ver no Pantanal se R05 for real (Aqua 5,94 → 7,15).

## 8. Diferenças em relação ao rascunho das 15:50
Bioma removido (D33): k_bioma/a_bioma → k_global(M)/a_global(M); sem `cell_biome`. Coluna `add` → `add_term` (`add` colide com `DataFrame.add`). Novos: CLI usa `winner()` (R8), `--agg` para o arquivo do Pantanal, teste de deriva e teste do `check_method`.

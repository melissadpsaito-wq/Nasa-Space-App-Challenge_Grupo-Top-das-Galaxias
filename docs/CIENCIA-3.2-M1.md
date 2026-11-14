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

## 4. Pendências
| Item | Dono |
|---|---|
| `agg_monthly` do Pantanal (Dados 2.2) — sem ele o M1 só roda no sintético | Murilo |
| Rodar `check_method` em Brasil 2025 e colar o resultado aqui | Melissa |
| Aprovar D30, D31, D32 (D32 já com prior global por D33) | Capitão |
| λ vencedor via `validation.json` (CP3, 23:30) | Samuel |

## 5. Leitura esperada
k(c,M) de meses com pouco fogo sai abaixo do k global (os meses com A = 0 vão para o aditivo). Com λ = 0 o total do ajuste é conservado. No sintético com deriva de +20% em 2020+, o teste 2020–2021 fica em Σpred/ΣB ≈ 0,85 — é a assinatura que esperamos ver no Pantanal se R05 for real (Aqua 5,94 → 7,15).

## 6. Diferenças em relação ao rascunho das 15:50
Bioma removido (D33): k_bioma/a_bioma → k_global(M)/a_global(M); sem `cell_biome`. Coluna `add` → `add_term` (`add` colide com `DataFrame.add`). Novos: CLI usa `winner()` (R8), `--agg` para o arquivo do Pantanal, teste de deriva e teste do `check_method`.

# Contrato interno da Ciência — Melissa × Samuel (Guia 48h v2 §3.1 · final sáb 16:30, YAML v3)

Fonte da verdade: `config/sensors.yaml` + `pipeline/bridges/base.py` (regras R1–R7 no topo do arquivo). Teste: `pytest tests/test_bridge_contract.py`. Mudança = decisão nova (Dxx).

## 1. Quem mexe em quê (R12)
| Arquivo | Escreve | Lê |
|---|---|---|
| `config/sensors.yaml` | Melissa | todos |
| `pipeline/bridges/` (`base.py`, M1, M2, C4) | Melissa | Samuel |
| `tests/test_bridge_contract.py` | Melissa | — |
| `pipeline/validate/` (Identity, GlobalFactor, `run.py`, M3) | Samuel | Melissa (só `validation.json`) |
| `pipeline/analytics/` (Pettitt, sazonalidade) | Samuel | — |
| `app/public/data/validation.json`, `pettitt.json` | Samuel | Melissa, Luana |
| `data/processed/harm_series.parquet` | Melissa | Murilo |
Branches: `ciencia/contrato` → `ciencia/m1`, `ciencia/m2` (Melissa) · `ciencia/validacao`, `ciencia/homog` (Samuel).

## 2. Interface `Bridge`
| Item | Regra |
|---|---|
| `fit(A, B, years)` | A, B = `agg_monthly` de 1 sensor; ausente = 0; `years` pode repetir (bootstrap); devolve `self` |
| `transform(A, months=None)` | Usa só `A.n`; saída `cell, ym, n_pred` (float ≥ 0) para células do fit ∪ de A × `months` |
| Construtor | `(lam, ctx: Context)`; `ctx = Context(cfg, passes=base.passes_reader(cfg))`. Sem bioma (D33): prior = k_global(M), a_global(M) |
| Passagens (M2) | `ctx.passes(sensor, anos)` → `cell, ym, daynight, frp_max, season`; meses excluídos já saem; anos repetidos não são replicados |
| λ de produção | `base.winner(cfg, bridge_id)` → `{method, lam}` de `validation.json`; `None` antes do CP3 (usar λ = 20 só em teste) |
| YAML | `load_config()` roda `check_config()`: timeline contínua, fit dentro da sobreposição, test depois do fit, cadeias encaixam |
| Tabela de ajuste | Sempre `base.paired()` (zero-fill, exclusão, pesos do bootstrap). Nota sempre em `base.scoring_months()` |
| Cadeia | `base.build_chain(sensor, ...)`: Terra → Aqua → S-NPP; N20 → S-NPP |
| Conformidade | Toda ponte passa em `base.check_bridge` (M3 com `uses_features=True` e só como 1º elo) |

## 3. `validation.json` (Samuel → Melissa, Luana)
```json
{"aqua_snpp": {
   "split": "LOYO no fit + teste 2020–2021",
   "results": [{"method": "M1", "lam": 20, "consistency": 0.31, "r2_log": 0.74, "bias": -0.02, "n_test": 1234}],
   "winner": {"method": "M1", "lam": 20}, "beats_raw": true, "beats_global": true}}
```
Melissa lê `winner` por ponte; ninguém edita λ à mão. Regra do CP3: `beats_raw` e `beats_global` verdadeiros.

## 4. Entregas
| Quando | O quê | De → para |
|---|---|---|
| Sáb 15:00 | Este contrato no `main` | Melissa → Samuel |
| Sáb 15:00–19:00 | M1 Pantanal (§3.2) · Samuel monta `validate/run.py` com Identity e GlobalFactor | — |
| Sáb 22:00 | M1 + M2 do Pantanal | Melissa → Samuel |
| Sáb 22:00–23:30 | `validation.json` Pantanal; λ vencedor (CP3) | Samuel → Melissa |
| Sáb 23:30 → noite | C4 (bootstrap) com o vencedor | Melissa |
| Dom 07:30–10:00 | `harm_series.parquet` Brasil · Pettitt raw × harm | Melissa → Murilo · Samuel |

## 5. Pendente de aprovação do Capitão
| ID | Ponto |
|---|---|
| D30 | Ajuste Aqua→S-NPP 2012–2019 e teste 2020–2021 (o Guia v2 §3.1 ainda traz 2012–2021) |
| D31 | Meses tocados pela pane do Aqua (202008, 202009) saem inteiros; `transform` recebe `months`; λ vem de `validation.json` |

## 6. D33 (sem bioma, 2000–2025)
| Item | Como fica |
|---|---|
| `Context` | sem `cell_biome` (removido no YAML v3); o M1 usa direto k_global(M) e a_global(M) |
| Estratos do limiar (M2) | trimestre × dia/noite, Brasil inteiro (8 estratos) |
| `validation.json` | sem `by_biome`; acrescentar `by_season` (opcional) |
| Nova saída Samuel | `consistency_4sat.json`: para cada par de sensores na sobreposição, razão harmonizado/harmonizado por ano (esperado ≈ 1) |

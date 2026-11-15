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

## 9. Previsão 2026 (Samuel → Murilo, Luana)
Fonte: `pipeline/forecast/rf_outlook.py` → `data/processed/forecast/forecast_2026.csv` + `forecast_skill.json` → `pipeline/forecast/export_forecast.py` → tiles `app/public/data/forecast_<pai>.json` + `forecast_skill.json`.

| Campo | Significado |
|---|---|
| `cell` | hexágono H3 res. 5 (31.946 células; `export_forecast --expect-cells 31946` falha se o total divergir) |
| `month` | mês de 2026 (1–12) |
| `p` | fração das árvores com previsão > `normal`, em [0, 1] |
| `q10`, `q50`, `q90` | quantis das previsões das árvores, na unidade `unit`, ≥ 0 |
| `unit` | unidade de `q10/q50/q90` e `normal`; hoje `frp_mw` (ΣFRP harmonizado mensal da célula, MW, D40). Passado ao exportador por `--unit` e gravado nos tiles; o app não deve assumir a unidade |
| `normal` | mediana do ΣFRP harmonizado da célula naquele mês, 2003..Y−1, na mesma unidade de `unit`. É o limiar de `p`. Quando vale 0, `p` significa "qualquer fogo acima de zero" |

**Portão (D35).** `forecast_skill.json` traz o resultado do hindcast; o exportador avalia `bss_clim_gt_0`, `bss_d27_gt_0`, `log_err_beats_clim_3_of_5` e `all_test_years_present`. Aprovado: a aba mostra o Outlook. Reprovado (estado atual): a aba mostra a chance histórica (D27, R18) e o Outlook só aparece com `?force-outlook`, e apenas em desenvolvimento.

**Agregação por área desenhada (proposta, decisão nova a numerar).** O app consulta valores pré-calculados por célula; não recalcula o modelo. Células da área = as de centroide dentro do polígono. Para `unit = frp_mw`:
| Valor | Regra |
|---|---|
| `q10/q50/q90` da área | soma das células, rotulada "ΣFRP da área (MW)". Os quantis somados são aproximação (os quantis de uma soma não são a soma dos quantis) e devem ser rotulados como tal |
| `normal` da área | soma dos `normal` das células |
| `p` da área | "pelo menos uma célula acima do normal": 1 − ∏(1 − pᵢ), assumindo independência (o que superestima a chance); ou média dos pᵢ. Escolher uma e rotular na interface |
| Limite de tamanho | área máxima em número de células, a definir, para o app não somar milhares de células |
| Fora da grade | ponto ou área sem célula no Brasil: mensagem clara, nunca zero |
Enquanto o portão estiver reprovado, esta agregação só vale para o Outlook em modo de desenvolvimento; a aba pública usa a chance histórica.

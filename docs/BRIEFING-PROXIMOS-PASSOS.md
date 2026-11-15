# Briefing para os próximos passos (sáb 14/11 19:31) — ponto de partida da 3.3 em diante

Fonte: Guia 48h v2.4 (§2 cronograma, §3 checkpoints, §5 passagens de bastão) + o que já rodou hoje (`31`, `32`, `08`, `01`, `18`).

## 1. Onde estamos (adiantados em relação ao Guia)
| Item do Guia | Previsto | Situação real |
|---|---|---|
| CP2 (19:00): Pantanal agregado · M1 no validador · site | sáb 19:00 | Pantanal **e Brasil** agregados ✅ · M1 pronto e conferido (`--eval`) ✅ · validador oficial (Samuel) e site (Luana): **confirmar** |
| 2.3 Brasil inteiro (19:45 → madrugada) | à noite | **feito às 17:53** (ingest ~1 min, grade 19 s) ✅ |
| Reproduzir 5,42 → 3,45 → ≈1,0 | antes do M1 | ✅ exato (`check_method`) |
| M1 | 15:00–19:00 | ✅ Brasil: consistency 0,45 (teste 2020–21) × 0,69 taxa única × 1,10 bruto |

## 2. Artefatos prontos (máquina do Murilo; `data/` fora do Git)
| Arquivo | Conteúdo | Quem usa |
|---|---|---|
| `data/clean/<SENSOR>/<ano>.parquet` | Focos limpos Brasil 2000–2025 (4 sensores) | todos |
| `data/interim/grid2km_pass.parquet` | Peneira 0,02° × passagem, Brasil: sensor, ts, daynight, gy, gx, cell, ym, frp_max, frp_sum, n_pix, pix_area | **Melissa (M2, via `base.passes_reader`)** |
| `data/interim/agg_monthly.parquet` | Brasil, sensor × cell (H3 res 4) × ym | Melissa, Samuel |
| `data/interim/pantanal/…` | Mesmos dois arquivos, só Pantanal | piloto / app |
| `data/interim/m1_eval_aqua_snpp.csv` | Conferência M1 (Brasil) | Samuel (referência) |
| `data/interim/previa/m1_*.csv` | Série anual 4 satélites bruto × harmonizado; taxas por mês e por célula | Method, gráfico D34 |
| `data/interim/previa/extra_fires_2025_{day,month}.csv` | Distância dos fogos extras do VIIRS ao MODIS | Method, pitch |

Código no PR `ciencia/m1` (`f30b43d`): `pipeline/grid.py`, `pipeline/bridges/{m1,check_method,m1_preview,check_extra}.py`, testes (`test_m1` 12, `test_grid` 3+1, contrato com M1). **Falta: merge no `main`.**

## 3. 3.3 — M2, limiar de FRP (Melissa, 19:45–23:30) · o que já sabemos
Fórmula (Guia §3.3, D13, D33): por estrato s = trimestre × dia/noite (8, Brasil):
```
τ_s = quantil( frp_max das passagens S-NPP em s , 1 − N_Aqua,s / N_SNPP,s )   (na sobreposição, anos de ajuste)
forte = S-NPP com frp_max ≥ τ_s      fraco = o resto
r(c,M) = (Σfraco + λ·r_global(M)) / (Σforte + λ)
M2: pred_SNPP = k_forte(c,M)·A·(1 + r(c,M)) + termo aditivo onde A = 0
```
Entrada: `ctx = Context(cfg, passes=base.passes_reader(cfg))` → `passes(sensor, anos)` devolve cell, ym, daynight, frp_max, season (meses da pane já fora). O `grid2km_pass` do Brasil já existe no caminho do YAML.

Prévia do τ (Brasil **2025**, grade 0,02°, `check_method`) — na 3.3 recalcular em **2012–2019**:
| Estrato | Aqua | S-NPP | Razão | τ (MW) |
|---|---|---|---|---|
| DJF D / N | 12.415 / 373 | 33.831 / 7.198 | 2,73 / 19,30 | 8,2 / 6,4 |
| MAM D / N | 6.634 / 417 | 19.510 / 7.055 | 2,94 / 16,92 | 8,1 / 6,2 |
| JJA D / N | 26.052 / 2.507 | 67.558 / 30.513 | 2,59 / 12,17 | 9,2 / 6,1 |
| SON D / N | 59.495 / 5.189 | 160.268 / 64.494 | 2,69 / 12,43 | 10,7 / 6,1 |

Pontos de atenção para o M2:
| Ponto | Por quê | Sugestão |
|---|---|---|
| Estratos noturnos DJF/MAM têm < 420 focos Aqua (2025) | τ instável | Com 2012–2019 haverá ~8× mais; registrar n por estrato na tabela do Method |
| À noite a razão é 12–19× e 77% dos fogos "invisíveis ao MODIS" são noturnos (`check_extra`) | O "fraco" noturno é grande; r(c,M) noturno alto | Conferir se M2 ganha do M1 separadamente de dia e de noite |
| `check_extra`: 65% dos extras a ≤ 10 km de fogo MODIS no mês; 9% em lugares sem MODIS a 50 km (1,6 MW, 77% noite) | Estes 9% são o que o termo aditivo cobre | Termo aditivo continua essencial no M2 |
| Meta para o CP3 | M2 precisa ganhar do M1 para ser o vencedor | Bater **0,447** (teste 2020–21) e **0,418** (LOYO) da conferência M1 |
| Aqua 2024–25 em deriva (+15–23%) | Fora do ajuste 2012–2019 | Não usar 2022+ para ajustar |

Contrato: M2 entra em `pipeline/bridges/m2.py`, passa em `base.check_bridge` e no `test_bridge_contract.py` (λ ∈ {0, 5, 20, 50}). Mesma interface do M1 (`M2(lam, ctx)`).

## 4. Validação (Samuel, 19:45–23:30) → `validation.json`
| Item | Referência |
|---|---|
| Métrica | Guia §3.6: mediana \|log((p+1)/(r+1))\|, R² log1p, viés mediano; LOYO nos anos de ajuste + teste 2020–2021; meses via `base.scoring_months` |
| Números para reproduzir | `m1_eval_aqua_snpp.csv`: bruto 1,099 · taxa única 0,693 · M1 λ5 0,447 / λ20 0,448 (teste) — conferência só em célula-mês ativas (A > 0 ou B > 0). Definir no `run.py` se usa só ativas (recomendado; senão os zeros dominam a mediana) |
| Formato | `CONTRATO-CIENCIA.md` §3; `winner` com λ ∈ `lambda_grid` (5, 20, 50) |
| Pontes | aqua_snpp (M1, M2) · terra_aqua (M1) · n20_snpp (M1) |
| Dados | Rodar `ingest --area brasil` + `grid --area brasil` (~1 min) ou receber `agg_monthly` pelo Drive |
| Regra do CP3 | `beats_raw` e `beats_global` — M1 já cumpre na conferência |

## 5. Dados / Capitão (Murilo, 19:45–23:30) — horário liberado pela 2.3 adiantada
| Prioridade | Tarefa | Por quê |
|---|---|---|
| 1 | Merge do PR `ciencia/m1` (e do pacote de governança v2.4) | Samuel e Melissa precisam do código; DECISIONS do repo está sem D17–D34 |
| 2 | **2.4 export** (`pipeline/export.py`, Guia Técnico §2.4): `harm_monthly.json` do Pantanal com o **M1 provisório** (λ = 20) → Luana às 23:45 | Desbloqueia o app antes do CP3; troca pelo vencedor depois |
| 3 | `sensors4.json` (gráfico 4 satélites, D34) a partir do `m1_preview` | Domingo 10:00 vira só atualização |
| 4 | Decidir pendências (tabela §7) | Capitão |

## 6. Front (Luana)
Formato `harm_monthly.json`: DATA_DICTIONARY §3 (valores × 10, inteiros; tiles por célula-pai H3 res 2 no Brasil, R06). Unidade a mostrar: "focos em escala VIIRS S-NPP (células de 2 km por passagem)" — senão alguém compara com o INPE. Gráfico D34: 4 linhas harmonizadas, destacar Aqua 2024–25 ("deriva de órbita detectada") e Terra pós-2011 ("fora da janela de calibração").

## 7. Decisões pendentes (Capitão)
| ID | Ponto | Situação / sugestão |
|---|---|---|
| D29 | Texto: `frp_sum` = Σ FRP de **todos os pixels** (não Σ frp_max) | `grid.py` já faz assim; só ajustar o texto (medido: 1,17 × 0,76) |
| D30 | Janela 2012–2019 / teste 2020–21 | Manter; motivo revisto (sem degrau na grade em 2020) |
| D31 | Pane do Aqua fora; `transform(A, months)`; λ via `validation.json` | Em uso no código |
| D32 | Somas só com A > 0; fallback global | Em uso; resultados ok |
| D16, D03, D04, D23, D24 | Propostas antigas | Confirmar |
| ΣFRP como 2ª camada (era "D34" no rascunho) | Depois do CP3, se sobrar tempo | Não registrado; D34 virou o gráfico dos 4 satélites |

## 8. Lições operacionais de hoje
| Situação | Como evitar |
|---|---|
| `git am` grava o commit em nome do Claude | Usar `git apply` + commit próprio, ou `git commit --amend --reset-author --no-edit` |
| Patch não chega em Downloads | Pasta do repo conectada no app: o Claude grava direto (conferir depois — uma gravação não foi aplicada na 1ª vez) |
| `PermissionError` ao gravar CSV | Fechar o Excel; ou `--out` para outra pasta |
| CSV abre numa coluna só | Excel deste PC usa vírgula como separador → CSV padrão (`,` e ponto decimal) |
| Arquivos com CRLF no Windows | Manter CRLF ao reescrever; avisos LF/CRLF do Git são inofensivos |

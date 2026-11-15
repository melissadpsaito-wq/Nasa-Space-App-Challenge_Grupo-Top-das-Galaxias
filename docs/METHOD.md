# Método

## Problema medido (Brasil 2025)
| Comparação | Razão | Variação mensal |
|---|---|---|
| S-NPP / Aqua | 5,42 | 3,5 – 6,4 |
| NOAA-20 / S-NPP | 0,98 | 0,95 – 1,05 |
| Aqua / Terra | 1,73 | 1,3 – 2,4 |

## Decomposição do degrau S-NPP/Aqua
| Etapa | Razão |
|---|---|
| Bruto | 5,42 |
| Grade comum ~1 km por passagem | 3,58 |
| Grade comum ≥ ~2 km por passagem (estabiliza) | 3,45 |
| + limiar de FRP (~9,5 MW em 2025) | ≈ 1,0 |
Leitura: resolução explica ~1/3 do degrau; o resto é sensibilidade a fogos fracos e cobertura.

## Harmonização (D13)
1. Grade comum ~2 km (0,02°) por passagem para todos os sensores.
2. Limiar de FRP por bioma × estação × dia/noite, calibrado na sobreposição.
3. Resíduo: razão com encolhimento por célula × mês + termo aditivo onde o sensor antigo vê zero.
Cadeia de pontes: Terra → Aqua → S-NPP ← NOAA-20 (configurável em `config/sensors.yaml`).

## Métodos concorrentes e escolha
| Método | Ideia |
|---|---|
| M1 Razão | k = (ΣB + λ·k_bioma)/(ΣA + λ) por célula × mês do ano |
| M2 Físico | etapas 1–2 acima + M1 no resíduo |
| M3 ML (AI1) | HistGradientBoosting, perda Poisson; features: contagem, FRP médio/p90, fração noturna, área do pixel, mês, lat/lon, bioma |
Métrica: mediana |log((pred+1)/(real+1))| no período de teste + R² em log + viés por bioma. Divisão por ano. Excluída a pane do Aqua (16/08–02/09/2020).

## Incerteza (C4)
Bootstrap por blocos de ano (200×) → percentis 5–95; baixa confiança se (hi−lo)/valor > 0,5 ou n < 5.

## Testes de homogeneidade (C1, D12)
| Propriedade | Teste |
|---|---|
| Nível | Pettitt na série anual por célula; % de células com quebra (p<0,05) no ano de troca ±1 |
| Força dos focos | Kolmogorov–Smirnov no FRP antes × depois |
| Pegada espacial | % de células ativas por ano |
| Sazonalidade | correlação do ciclo mensal antes × depois |

## Alternativa testada e descartada (D14)
Subdivisão por pegada em grade de 375 m: S-NPP/Aqua = 0,55 — inverte o viés em vez de removê-lo.

## Previsão 2026 (Outlook): modelo, hindcast e portão (D35, D48)
**Modelo.** `RandomForestRegressor` (D48) sobre o ΣFRP mensal harmonizado em MW (D40), por hexágono H3 (res. 5) × mês. Features: lat, lon, ano, mês, precipitação, umidade, temperatura máxima e seis indicadores de bioma. Base de treino: 2016–2025, 31.946 hexágonos × 120 meses (3.833.520 linhas, sem nulos nem duplicatas). Dos 31.946 hexágonos, 1.164 (3,6%) ficam na borda ou na costa e recebem o bioma mais próximo (`sjoin_nearest`, em CRS geográfico), não um cruzamento exato.

**Saídas.** Para cada hexágono e mês de 2026: `p` = fração das árvores com previsão acima do `normal`; `q10`, `q50`, `q90` = quantis das previsões das árvores; `normal` = mediana do ΣFRP harmonizado da célula naquele mês, de 2003 a Y−1 (sem vazamento).

**Hindcast.** Anos de teste 2021–2025, cada um previsto só com os anos anteriores. O hindcast retreina um modelo proxy (50 árvores, profundidade máxima 15, `max_samples` 0,3), não o modelo exportado (`modelo_fogo_random_forest_95_5.pkl`), que só é usado na previsão de 2026. No ano de teste, o clima de entrada é a média por bioma × mês dos anos de treino, então o modelo não vê a anomalia climática do ano. Baselines: climatologia (P = fração histórica acima do normal, últimos 10 anos, D27) e persistência.

**Resultado (geral, 2021–2025).**
| Métrica | Modelo | Referência |
|---|---|---|
| BSS vs. climatologia | −3,66 | > 0 para aprovar |
| BSS vs. chance histórica (D27) | −4,46 | > 0 para aprovar |
| AUC | 0,432 | 0,5 = sem habilidade |
| Erro log (mediana, modelo / climatologia) | 1,177 / 0,189 | modelo deve ganhar em 3 de 5 anos |
| Cobertura do intervalo q10–q90 | 14,3% | nominal 80% |
Por ano, o BSS vs. climatologia vai de −3,25 (2021) a −4,06 (2025) e o AUC de 0,40 a 0,47. Restrito a células-mês com fogo prévio, o resultado melhora mas continua abaixo da climatologia (BSS −1,45 a −2,29; AUC 0,45 a 0,55).

**Portão (D35): REPROVADO.** Nenhum dos critérios de skill passou: BSS vs. climatologia > 0, BSS vs. D27 > 0, erro log menor que o da climatologia em ≥ 3 de 5 anos (0 de 5). Só o critério de que todos os anos de teste estejam presentes foi cumprido. Consequência (R18): a aba mostra a chance histórica (D27) e o Outlook do Random Forest não é exibido. O modelo, os números e os tiles `forecast_*` ficam documentados aqui e no repositório.

**Limitações conhecidas.**
- **Probabilidade saturada.** A P média de 2026 é 0,84, enquanto só 13–18% das células-mês superam o normal nos anos de teste. Causa provável, pelo código: o `normal` é uma mediana e vale zero na maioria das células-mês; um regressor devolve a média da folha, quase sempre levemente positiva, então quase toda árvore prevê "acima do normal". Um regressor não produz probabilidade calibrada de um evento raro. Um classificador ou uma calibração (por exemplo, isotônica) ajustada em um ano e avaliada nos outros é o próximo passo.
- **Sem anomalia climática.** Com o clima médio do ano de teste, o modelo dificilmente supera uma climatologia por célula e mês, mesmo com a probabilidade corrigida.
- **Baselines de erro log.** Como a mediana mensal por célula é zero na maior parte do painel, o erro log da climatologia e da persistência tende a zero no conjunto geral; o recorte "ativo" é a comparação mais informativa.
- **Versão do scikit-learn.** O `.pkl` foi salvo na versão 1.9.1 e carregado na 1.9.0 (aviso de compatibilidade). Isso não afeta o hindcast, que retreina o proxy.

## Referências
Giglio, Schroeder & Justice (2016) RSE 178 · Schroeder et al. (2014) RSE 143 · MODIS C6 Active Fire User's Guide rev. C · VIIRS C2 Burned Area User's Guide v1.1 · Pettitt (1979) Appl. Stat. 28 · Mann (1945) Econometrica 13 · Sen (1968) JASA 63 · Efron & Morris (1975) JASA 70 · Efron & Tibshirani (1993) · Künsch (1989) Ann. Stat. 17 · Friedman (2001) Ann. Stat. 29 · Breiman (2001) Mach. Learn. 45 · Nuñez et al. (2018) PLOS ONE 13 · Giglio et al. (2006) ACP 6.

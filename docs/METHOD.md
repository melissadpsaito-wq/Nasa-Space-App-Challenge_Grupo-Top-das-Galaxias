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

## Referências
Giglio, Schroeder & Justice (2016) RSE 178 · Schroeder et al. (2014) RSE 143 · MODIS C6 Active Fire User's Guide rev. C · VIIRS C2 Burned Area User's Guide v1.1 · Pettitt (1979) Appl. Stat. 28 · Mann (1945) Econometrica 13 · Sen (1968) JASA 63 · Efron & Morris (1975) JASA 70 · Efron & Tibshirani (1993) · Künsch (1989) Ann. Stat. 17 · Friedman (2001) Ann. Stat. 29 · Breiman (2001) Mach. Learn. 45 · Nuñez et al. (2018) PLOS ONE 13 · Giglio et al. (2006) ACP 6.

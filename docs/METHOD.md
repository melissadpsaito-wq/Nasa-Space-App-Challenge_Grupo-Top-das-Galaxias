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
| + limiar de FRP (τ = 9,4 MW na grade 0,02°; 9,8 MW na 0,01°) | 1,00 |
Leitura: resolução explica ~1/3 do degrau; o resto é sensibilidade a fogos fracos e cobertura. Reproduzido exatamente por `pipeline/bridges/check_method.py` (14/11 16:54); a grade do Brasil (`grid.py`) dá o mesmo 3,45 para 2025 por outro caminho.

## Harmonização (D13)
1. Grade comum ~2 km (0,02°) por passagem para todos os sensores.
2. Limiar de FRP por estação (trimestre) × dia/noite, calibrado na sobreposição, Brasil inteiro (D33).
3. Resíduo: razão com encolhimento por célula × mês + termo aditivo onde o sensor antigo vê zero.
Cadeia de pontes: Terra → Aqua → S-NPP ← NOAA-20 (configurável em `config/sensors.yaml`).

## Métodos concorrentes e escolha
| Método | Ideia |
|---|---|
| M1 Razão | k = (ΣB + λ·k_global(M))/(ΣA + λ) por célula × mês do ano (D32, D33) |
| M2 Físico | etapas 1–2 acima + M1 no resíduo |
| M3 ML (AI1) | HistGradientBoosting, perda Poisson; features: contagem, FRP médio/p90, fração noturna, área do pixel, mês, lat/lon |
Métrica: mediana |log((pred+1)/(real+1))| no período de teste + R² em log + viés global e por estação. Divisão por ano. Excluída a pane do Aqua (16/08–02/09/2020).

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

## Escolhas registradas no plano v2 (D26, proposta)
| Escolha | Valor | Motivo |
|---|---|---|
| FRP na célula de 2 km | máximo | Somar pixels VIIRS do mesmo fogo inflaria o FRP do sensor fino |
| Estação | trimestre (DJF, MAM, JJA, SON) | Definição simples e reprodutível |
| Estrato do limiar | trimestre × dia/noite (D33: sem bioma) | 8 estratos com muitos dados cada |
| λ | {5, 20, 50}, escolhido na validação | — |
| Janelas de ajuste | Aqua→S-NPP 2012–2019 (teste 2020–2021, D30) · Terra→Aqua 2003–2010 · N20→S-NPP 2018–2025 | Teste fora do tempo; deriva do Aqua só em 2024–25 (R05) |
Limiar: τ_s = quantil(FRP S-NPP em s, 1 − N_Aqua,s / N_SNPP,s). M2: pred = k_forte · A · (1 + r), r = fracos/fortes com encolhimento.

## Fire Anomaly Score e pico (D25, proposta)
Score = percentil empírico de x = harm(área, ano, mês) entre os mesmos meses dos outros anos: 100·(#{h < x} + 0,5·#{h = x})/|H|. Faixas: < 60 normal · 60–85 acima · 85–95 muito acima · ≥ 95 extremo.
Pico típico: mês com maior % de anos como mês de maior atividade. É climatologia (comparação com o histórico), não previsão (D21).
Incerteza da área no app: soma de `lo` e `hi` das células (aproximação conservadora, declarada).

## Chance histórica de ficar acima do normal (D27, decidida)
Área A, mês do ano M. Normal = mediana de harm(A, y, M) em todos os anos. Chance = % dos últimos 10 anos completos em que harm(A, y, M) > normal, exibida como "40% (4 de 10 anos)".
Leitura: ≈ 50% = sem mudança; > 50% = o mês tem ficado acima do normal com mais frequência na última década. Com menos de 5 anos com fogo em M: "dados insuficientes". É frequência observada no passado, não previsão (D21).

## Período e sensores (D33, decidida)
Análise de nov/2000 a dez/2025 com todos os anos de todos os sensores: Terra 2000–2025, Aqua 2002–2025, S-NPP 2012–2025, NOAA-20 2018–2025. Cada sensor é convertido à escala S-NPP no período inteiro; nas sobreposições, as 4 séries harmonizadas devem coincidir (razão ≈ 1). Desvios medidos (14/11, M1 λ = 20): Aqua 2024–25 +15–23% (deriva de órbita, R05) e Terra depois de 2011 +15–60% (fora da janela 2003–2010) — mostrados como achado no gráfico dos 4 satélites (D34). Sem estratificação por bioma.

## Resultados até sáb 14/11 19:30 (Brasil 2000–2025; detalhes em `docs/CIENCIA-3.2-M1.md`)
### Grade e razão por período
| | 2012–2019 | 2020–2021 | 2022–2025 |
|---|---|---|---|
| S-NPP/Aqua na grade 0,02° (Brasil) | 3,96 | 3,98 | 3,58 |
| Idem, Pantanal (bruto) | 3,40 (5,94) | 3,41 (7,17) | 3,28 (~7,1) |
O degrau de 2020 do bruto some na grade: era efeito de mais pixels VIIRS por fogo em anos de muito fogo.

### M1 — conferência por célula-mês ativa (`python -m pipeline.bridges.m1 --eval`; a nota oficial é o `validation.json`)
| Método | Teste 2020–2021: consistency / R² log / viés / Σpred÷ΣB | LOYO 2012–2019: consistency |
|---|---|---|
| Bruto | 1,099 / −0,11 / −1,10 / 0,26 | 1,099 |
| Taxa única | 0,693 / 0,18 / −0,58 / 1,01 | 0,693 |
| M1 λ = 5 | **0,447** / 0,66 / −0,10 / 0,99 | 0,419 |
| M1 λ = 20 | 0,448 / 0,64 / −0,09 / 0,99 | **0,418** |
Harmonizado ÷ S-NPP real por ano: Aqua ±4% (2012–2023) · NOAA-20 ±3% (2018–2025).

### Por que não ΣFRP como unidade
ΣFRP S-NPP/Aqua (Brasil 2025) = 1,17 (todos os pixels) ou 0,76 (Σ máximo por célula), mas varia mais entre meses que a contagem na grade (CV 16% × 12%) e inverte entre dia (0,73) e noite (1,38). Unidade principal segue contagem (D03); ΣFRP = coluna extra (D29).

### De onde vêm os fogos extras do VIIRS (`pipeline/bridges/check_extra.py`, Brasil 2025)
Distância de cada fogo S-NPP (célula 0,02° × passagem) à detecção Aqua mais próxima no mesmo mês e turno: ≤ 2 km 35% · 2–10 km 30% · 10–50 km 26% · > 50 km **9%** (FRP mediano 1,6 MW, 77% noturnos; pesam 0,30 dos 3,45). No mesmo dia, só 44,5% dos fogos diurnos do Aqua têm par no S-NPP (faixa e horário diferentes) → comparação mensal, como no M1. Frase: "9 em cada 10 fogos extras do VIIRS estão nas mesmas regiões de queima que o MODIS já via; só ~9% são fogos muito fracos, quase sempre noturnos, onde o MODIS não registrou nada no mês."

### Limites declarados
Resolução da série antiga = célula H3 res 4 (~45 km) × mês (não há posição de fogos individuais); erro típico por célula-mês ≈ fator 1,6 (totais e tendências firmes); padrão de 2012–2019 aplicado ao passado; Terra só em nov/2000–jun/2002 (baixa confiança).

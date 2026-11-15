# Fire Almanac — Governança do projeto (consolidada)

**NASA Space Apps 2026 · Harmonization of MODIS and VIIRS Hot Spots · Grupo Top das Galáxias · São Paulo**
Versão **v2.15** · dom 15/11/2026 06:05 · decisões até **D46** · **Front 4.1 concluída no código** (D46: visual do Samuel em `app/` estático, EN/PT, período De/Até; falta build, commit e Pages) · **Ciência 3.3 concluída** (limiar de FRP por trimestre × dia/noite; M2 = M1 → série segue com M1) · **calendário diário harmonizado gerado** (D43–D45: 5.869.988 dias com fogo, 0 dias vazios) (D39 proposta; demais decididas) · **Dados 2.4 concluída** (export provisório res 5 em tiles, D38) · **ΣFRP harmonizado** (D40, validado) e **base de treino Brasil inteiro** (D42) · regra dos 50 MB revogada (D41) · Ciência 3.2 e Dados 2.1–2.3 concluídas
Fonte da verdade: repositório `melissadpsaito-wq/Nasa-Space-App-Challenge_Grupo-Top-das-Galaxias` (`main`). Este arquivo é um retrato consolidado; os arquivos de `docs/` continuam valendo e são atualizados primeiro.

---

## 1. O projeto em uma página
| Item | Definição |
|---|---|
| Produto | **Fire Almanac**: (1) calendário de queimadas harmonizado MODIS + VIIRS, que é o que o desafio da NASA pede; (2) **Fire Outlook 2026**, análise preditiva por localização |
| Para quem (D20, D35) | Coordenador(a) de brigada/Defesa Civil e produtores rurais (fazendeiros) que precisam planejar prevenção e mitigação de incêndios |
| Pergunta | *"For this latitude/longitude, will fire activity be above normal in the coming months, and when does it usually peak?"* |
| Entrada | Latitude/longitude digitadas, busca de cidade ou clique no mapa; período De/Até (ano + mês, D46); opcional: desenhar área (fazenda, parte de cidade ou estado) |
| Site (D05, D46) | Estático (GitHub Pages), 2 páginas: landing + mapa; visual do Samuel; EN/PT; o navegador lê os tiles `harm_<pai>.json` (sem servidor) |
| Saída | Calendário **ano × dia** 2000–2025 (D44; dias harmonizados D43/D45, score/chance/Outlook mensais) · toggle bruto × harmonizado · Fire Anomaly Score · pico típico · **Outlook 2026** (P de fogo acima do normal + focos esperados 10–90%) · CSV |
| Dados | NASA FIRMS 2000–2025: MODIS Terra (2000–25) e Aqua (2002–25), VIIRS S-NPP (2012–25) e NOAA-20 (2018–25) — Brasil inteiro (D28, D33) · contorno do Brasil IBGE (malha `paises/BR`) só para a base de treino (D42) |
| Unidade | Detecções por célula de 0,02° por passagem, na escala S-NPP (D03) · variável extra: ΣFRP mensal (MW) harmonizado na escala S-NPP (D40) |
| Escala espacial (D36) | **H3 res 5 (~250 km², ~17 km de largura) no produto**: série exibida, entrada lat/lon, área desenhada, Outlook 2026. **Res 4 (~1.770 km², ~45 km)** nos bastidores: calibração e validação do método (CP3) e plano B. Res 6 descartada (medida) |
| Não faz | Probabilidade de chuva (sem dado de chuva; confirmado 21:35) · previsão "dentro da fazenda" (precisão é a da célula res 5, ~17 km) · 2026 observado/NRT (D33) |
| Diferencial | A previsão só é possível porque a série foi harmonizada: com dados brutos, o modelo aprenderia o salto falso de 2012 (VIIRS vê 5,4× mais que MODIS) como tendência |

## 2. Equipe e papéis (D16)
| Papel | Pessoa | Responde por | Decide sozinho |
|---|---|---|---|
| Capitão + Dados | **Murilo** | Escopo, checkpoints, decisões, submissão, envio · ingest, clean, grade, H3, export, features da previsão, `forecast_2026.json`, `sensors4`, `consistency_4sat`, casos de teste do score | Cortes de escopo, desempates; detalhes do pipeline que não mudam o contrato |
| Ciência · Harmonização (dupla) | **Melissa** | `sensors.yaml`, interface `Bridge`, M1, limiar FRP + M2, incerteza (bootstrap), 4 sensores 2000–2025 | Detalhes internos das pontes que não mudam a interface |
| Ciência · Validação + Previsão (dupla) | **Samuel** | Métrica, validação fora da amostra, Pettitt + sazonalidade, **modelo preditivo e hindcast** (`forecast_skill.json`) | Detalhes internos do validador e do modelo |
| Front + Demo | **Luana** | App (lat/lon, mapa, calendário, toggle, score, pico, Outlook, CSV, Method), deploy, vídeo, prints | Detalhes visuais e de código do app |
| Claude (IA) | — | Rascunha código, revisa método, redige documentos | Nada: propõe, a equipe decide |
Melissa e Samuel trabalham em dupla, em módulos separados (R12); o contato é a interface `Bridge` (`docs/CONTRATO-CIENCIA.md`). Dono do repositório: Melissa.

## 3. Como decidimos
| Tipo de decisão | Quem | Registro |
|---|---|---|
| Escopo, método, dados ou prazo | Capitão, após ouvir a equipe (≤ 10 min) | `docs/DECISIONS.md` (Dxx) |
| Contrato de dados | Dados + Front juntos | `docs/DECISIONS.md` |
| Interna a uma área | Dono da área | Mensagem de commit |
| Desempate | Capitão | `docs/DECISIONS.md` |
Regras: decisão não registrada não existe · decisões nunca são apagadas (reverter com nova Dxx) · proposta do Claude só vira "decidida" com o Capitão · mudança de rota = 1 linha (o que muda, por quê, custo em horas, o que sai) · depois do CP3 só troca item por item · depois do CP7 nenhuma mudança de escopo.

## 4. Escopo vigente
| Faixa | Itens |
|---|---|
| Núcleo — calendário (NASA) | Harmonização (grade 2 km + limiar FRP por estação × dia/noite + resíduo M1; M2 testado na 3.3, empate técnico → M1) · validação contra bruto e fator global · incerteza (bootstrap) · Pettitt + sazonalidade · mapa, lat/lon, seleção de área · calendário · toggle bruto × harmonizado · Fire Anomaly Score (D25) · pico típico · CSV · página Method · gráfico "4 satélites, 1 curva" (D34) · áreas prontas Pantanal e SP cana (D22) |
| Núcleo — previsão (D35) | Fire Outlook 2026 por célula/área: P(acima do normal) + focos esperados 10–90%; hindcast 2021–2025; **portão no CP5 (dom 10:00)**; plano B = chance histórica (D27) |
| Escala (D36, decidida 22:18) | Res 5 no produto (série, lat/lon, área, previsão, app); res 4 na calibração/validação e como plano B (célula res 5 com poucos dados ou portão do CP5 reprovado em res 5) |
| Export do app (D38) | Tiles por célula-pai H3 res 2 (`harm_<pai>.json`); fora do Git até o export final (antes do CP7); Luana recebe pelo Drive |
| Calendário diário (D43–D45) | Calendário ano × dia: cada dia com detecção, convertido para a escala S-NPP pelo fator do M1 (o dia original é mantido); fogo fraco estimado sem detecção (termo aditivo) fica fora do diário, como nota mensal (D45); score, chance e Outlook seguem mensais; saem SP cana (D22) e polimento do D34 (confirmar no CP4) |
| FRP e base de treino (D40, D42, D39) | ΣFRP mensal harmonizado via M1 (validado no teste 2020–21); base de treino = todos os hexágonos res 5 do Brasil × 302 meses, zeros incluídos; FRP como variável do modelo só se o hindcast melhorar (D39, proposta) |
| Front (D46, 4.1) | `app/` (Vite + Leaflet + h3-js + Plot): landing; mapa com busca, lat/lon, clique, período De/Até, harmonizado × bruto, hexágonos do período (zoom ≥ 7), painel e calendário ano × mês; abas Timeline e Outlook como "próxima etapa"; backend Flask do Samuel não publicado |
| Fora | Chuva · AI1 (ML de harmonização) · KS · pegada espacial · P2 · V1 · índice de agricultores (D19) · 2026 observado e NRT (D33) · bioma (D33) · globo 3D · chatbot |
| Futuro (pós-evento) | Mundo inteiro (pipeline por país, D28) · 2026 + NRT com NOAA-20/21 (D11) |

## 5. Ritmo e checkpoints (D23)
| # | Quando | Critério para seguir | Se falhar |
|---|---|---|---|
| CP0 | Sáb 13:30 | Decisões e ambiente | Capitão decide |
| CP1 | Sáb 15:00 | Contrato de dados congelado; JSON falso com a Luana | Front segue com falso |
| CP2 | Sáb 19:00 | Pantanal (e Brasil) agregado · M1 no validador · site no ar | Cortar Terra/N20 do piloto |
| **CP3** | **Sáb 23:30** | Vencedor (M1/M2) melhor que bruto e fator global · Pantanal real no app | Ficar com M1 |
| CP4 | Dom 07:30 | Série Brasil com incerteza | Só áreas prontas (R14) |
| **CP5** | **Dom 10:00** | **Portão da previsão** + corte final | App mostra D27 (R18) |
| CP6 | Dom 12:00 | Autoavaliação 1–5 por critério | Horas no critério mais fraco |
| CP7 | Dom 15:00 | Congelamento: só `fix/<tema>` | — |
| CP8 | Dom 21:00 | Envio interno, checklist 100% | Prazo oficial 23:59 |
Cada checkpoint: cada pessoa mostra **o que roda** (3 min); o Capitão registra em `docs/STATUS.md`. Sono em turnos ≥ 5 h (01:30–07:30).

## 6. Caminho crítico e dependências
**~~2.1 → 2.2 → 2.3~~ ✅ → ~~2.4 export provisório~~ ✅ → ~~3.3 limiar FRP + M2~~ ✅ → 3.6 validação (vencedor, λ) → 3.4 bootstrap Brasil → 2.4b reexport final → ~~4.1 front estático~~ ✅ (código; build/commit/Pages pendentes) → 4.4 app com dados reais → CP7**
Previsão: **série harmonizada (+ ΣFRP D40, base Brasil D42) → features (Murilo) → modelo + hindcast (Samuel) → portão CP5 → `forecast_2026.json` → card Outlook (Luana)**

| Passo | Dono | Depende de | Libera |
|---|---|---|---|
| 2.1 Ingest + clean 2000–2025 ✅ | Murilo | — | 2.2 |
| 2.2 Grade 0,02° + H3 + `agg_monthly` ✅ (Pantanal, sáb tarde) | Murilo | 2.1 | 2.3, 3.x |
| 2.3 Brasil inteiro 2000–2025 ✅ (res 4 às 17:53 · res 5 até 21:57, D36): ingest ~1 min, grade 19 s / 21 s, conservação OK; plano B (R14) não acionado | Murilo | 2.2 | 3.2 série res 5, 3.3, 3.6, P1, 2.4 |
| 3.1 Contrato `Bridge` ✅ · 3.2 M1 ✅ (22:22: + série provisória res 4 e **res 5**, escolha da resolução) | Melissa (+ Murilo) | 2.2 | 3.6, P1, 2.4 |
| 3.3 Limiar FRP + M2 ✅ (04:21): `pipeline/bridges/m2.py` + `tests/test_m2.py` (14) · τ dia 8,7–13,2 MW, noite 4,5–5,3 MW · M2 = M1 (Δ ≤ 0,001) → fica M1 · `m2_tau_aqua_snpp.csv` | Melissa (rascunho Claude, rodado por Murilo) | 2.2 | 3.6, Method (tabela de τ) |
| 3.6 Validação → `validation.json` | Samuel | 3.2, 3.3 | 3.4, export |
| 3.4 Bootstrap (noite) | Melissa | 3.6 | 2.4c, 3.7, features finais |
| 3.7 Pettitt + sazonalidade | Samuel | série harmonizada | Method |
| 3.5 4 sensores 2000–2025 | Melissa | 3.6 | `sensors4`, `consistency_4sat` |
| P1 Features da previsão | Murilo | **série provisória res 5 ✅** (`data/processed/res5/harm_series.parquet`, 22:22) / final (dom) | P2 |
| P2 Modelo + hindcast → `forecast_skill.json` | Samuel | P1 | portão CP5 |
| P3 `forecast_2026.json` | Murilo | portão aprovado | card Outlook |
| 2.4 Export provisório ✅ (22:44): `pipeline/export.py` + 7 testes · res 5 Brasil (M1 λ 20) · 28.769 células × 302 meses · 128 tiles res 2 (máx 1,35 MB, total 101 MB, R06 acionado) · conservação OK · zip no Drive (D38) · commits `df9f89a`, `47a497b` | Murilo | série provisória res 5 | 4.4 (dados reais no app) |
| 2.4b Reexport final (`python -m pipeline.export`) + commit único dos tiles (D38) | Murilo | 3.6 (vencedor) / 3.4 (`lo/hi`) | 4.4, CP7 |
| ΣFRP harmonizado (D40) ✅ 00:41 · base de treino Brasil (D42) ✅ 01:25 | Murilo | 2.3, M1 | P1, P2 (teste D39) |
| Diário harmonizado (D43, D45) ✅ 03:00: `fogo_diario_harm.csv` 5.869.988 dias com fogo, 0 dias vazios, 28.053 hexágonos; aditivo mensal 2.034.079 hexágono-mês | Murilo | D40, `audit_daily` | 2.4c export diário → calendário (Luana) |
| 2.4c Export diário `harm_daily_<pai>.json` (contrato §13, D44) | Murilo | diário harmonizado | 4.x calendário diário (Luana) |
| 4.1 Front estático ✅ 06:00 (D46): visual do Samuel portado para `app/` sem Flask; EN/PT; período De/Até; leitor de tiles validado nos 128 tiles reais; 11 testes; teste em navegador (Pantanal) · **falta**: `npm run build`, commit `front/setup` + PR, Pages ligado · resumo `docs/FRONT-SISTEMA-WEB.md` | Murilo + Samuel (rascunho Claude) | 2.4 | 4.2–4.5 |
| 4.2–4.3 Desenho de área, score D25, chance D27, pico típico, CSV | Luana | 4.1 | 4.4 |
| 4.4–4.5 Dados reais, score, Outlook, Method, CSV | Luana | 2.4, P3, 3.6, 3.7 | demo |

## 7. Regras de trabalho
| Regra | Como aplicar |
|---|---|
| Branches | `dados/<tema>`, `ciencia/<tema>`, `front/<tema>`; depois do CP7 só `fix/<tema>` |
| Commits | `<área>: <o que mudou>`; com IA, linha `AI-assisted: <ferramenta>` + registro em `AI_USAGE.md`; o commit é feito pela pessoa (não em nome do Claude) |
| Merge em `main` | Só por PR com 1 revisão de outra pessoa (≤ 10 min): roda? quebra o contrato? tem segredo? |
| Escrita exclusiva | Só o Murilo escreve em `app/public/data/` e `open/` |
| Proibido no repo | `.env`, `MAP_KEY`, dados brutos, ZIPs · arquivo > 100 MB vai como `.gz` (limite do GitHub; regra dos 50 MB revogada por D41) |
| Travou | > 30 min → aviso no grupo + issue "Bloqueio" |
| Pronto | Roda na máquina de outra pessoa · não quebra o contrato · testes passam · IA registrada · marcado no `ROADMAP.md` |
| Fonte da verdade | Repositório (`main`); o Projeto no Claude é espelho, atualizado depois de cada checkpoint |

## 8. Governança de dados
| Princípio | Regra |
|---|---|
| Bruto imutável | ZIPs FIRMS em `data/raw/` (Drive), nunca editados |
| Processado por script | `make all` recria tudo; nada editado à mão · exceção D41: `data/processed/res5_frp/` versionada (`git add -f`) para a equipe usar a base de treino sem rodar o pipeline |
| Versão e data | Toda fonte com `version` FIRMS e data de download (`meta.json`) |
| Segredos | `MAP_KEY` só em `.env` local e GitHub Secrets (incidente `541c557`: chave nova) |
| Sem dados pessoais | Só dados de satélite públicos; ponto digitado pelo usuário não é armazenado (app estático) |
| Qualidade | `type = 0` · MODIS conf ≥ 30 · VIIRS conf ∈ {n, h} · desde nov/2000 · pane do Aqua (202008–202009) fora do ajuste · teste de conservação em cada etapa |
| Conferência | Brasil 2025 reproduz 100% das contagens de referência; filtros removem ~6% MODIS e ~11% VIIRS · auditoria diário × mensal 0 divergências nos 4 satélites (`audit_daily`) · recálculo independente focos → CSV 5/5 e sanidade 7/7 (`spot_check`) |
| Linhagem | `data/raw` → `data/clean` → `data/interim` (grade, `agg_monthly`; `res5_frp/` = agg com n = ΣFRP ÷ s) → `data/processed` (série harmonizada, `res5_frp/` ΣFRP, features) → `app/public/data` (tiles JSON) e `open/` |
| Citação | "NASA FIRMS, MODIS Collection 6.1 and VIIRS 375 m active fire products"; código MIT |

## 9. Método (resumo)
| Etapa | Como |
|---|---|
| Problema | S-NPP vê 5,42× o Aqua (Brasil 2025); grade 2 km → 3,45×; + limiar FRP ≈ 1,0 |
| Harmonização (D13, D33) | Grade 0,02° por passagem → limiar FRP por trimestre × dia/noite → resíduo por célula × mês (M1: razão com encolhimento para k_global(M), termo aditivo; M2: física) |
| Pontes | Terra → Aqua (2003–2010) → S-NPP (2012–2019, teste 2020–21, D30) · NOAA-20 → S-NPP (2018–2025) |
| Limiar de FRP (3.3) | Brasil res 4, ajuste 2012–2019: τ de dia 8,7 (MAM) – 13,2 MW (SON), de noite 4,5–5,3 MW; razão após τ = 1,00 nos 8 estratos; r_global 2,2–3,8 fogos fracos por fogo forte. Frase: *MODIS misses fires weaker than ~9–13 MW by day and ~5 MW at night* |
| M2 × M1 (3.3) | k_f·(1+r) = k do M1 em λ = 0 e λ → ∞; teste 2020–21 λ 20: M2 0,449 × M1 0,448 (LOYO 0,418 × 0,418) → empate técnico → **M1** (`07-design` §3.4); M2 vai ao Method como explicação física |
| Escolha | Validação fora da amostra (mediana \|log((p+1)/(r+1))\|, R² log, viés, total previsto ÷ real) contra bruto e fator global; λ ∈ {5, 20, 50}. Conferência M1 λ = 20, teste 2020–21: res 4 consistency **0,448** × taxa única 0,693 × bruto 1,099 (R² 0,64); **res 5 0,522** × 0,693 (R² 0,27; total 1,03) |
| Incerteza | Bootstrap por blocos de ano (200×), p5–p95; `low_conf` se faixa > 50% ou n < 5 e Terra 2000–2002 |
| Homogeneidade | Pettitt (% células com quebra em 2012 ± 1) + sazonalidade, bruto × harmonizado |
| Achados | Aqua em deriva de órbita 2024–25 (+15–23%); Terra fora da janela pós-2011 — gráfico D34 · Degrau de 2020 do bruto some na grade (Brasil 3,96 → 3,98) · 9 em 10 fogos extras do VIIRS ficam nas mesmas regiões de queima do MODIS; ~9% são fogos fracos, noturnos, onde o MODIS não viu nada no mês |
| Resolução (D36) | Calibração na res 4; série e previsão na res 5 com M1 direto (hierárquico testado, D37, não adotado); res 6 descartada (R² log −0,43) |
| Série provisória (3.2) | `pipeline/bridges/harmonize.py`, M1 λ = 20, linha do tempo Terra → Aqua → S-NPP; emenda 2011→2012 sem degrau (res 5: harmonizado 1,26× × bruto 5,3×; fogo real Aqua×Aqua 1,37×); `lo = hi` até a 3.4 |
| Previsão (D35) | HistGradientBoosting global (classificador + quantis) com features só até dez/Y−1; hindcast 2021–2025 vs climatologia, D27 e persistência; BSS, AUC, erro em log, cobertura 10–90% |
| ΣFRP harmonizado (D40) | Mesmo M1 com n = ΣFRP ÷ s (s = 22,8 MW por detecção S-NPP); teste 2020–21 res 5: consistency **0,337** × bruto 0,388 × taxa única 0,394; R² 0,536; total 1,061 (termo aditivo: 2,9 M hexágono-mês pequenos antes de 2012 — limitação declarada) |
| Diário (D43, D45) | Valor do dia = valor mensal convertido × (detecções do dia ÷ detecções do mês) do satélite da época = fator k × detecções do dia; o dia vem da detecção original. Meses sem detecção: termo aditivo vira nota mensal (sem dia). Diário cobre **91,4% dos focos e 95,6% do ΣFRP** harmonizados; aditivo 8,6% e 4,4% (só antes de 2012) |
| Base de treino (D42) | 31.946 hexágonos (31.393 com centro no contorno IBGE + 553 de borda com fogo) × 302 meses = 9.647.692 linhas; 5.667.718 zeros |

## 10. Submissão (padrão Twisters)
| Campo | Conteúdo |
|---|---|
| Summary | Pergunta da persona + "25 years, 4 satellites, one consistent record" + Outlook 2026 com skill |
| Demo | Vídeo ≤ 30 s, legenda EN: lat/lon → calendário → toggle 2012 → Outlook |
| Project | Link do app (GitHub Pages) |
| Details | Pipeline, harmonização, validação, previsão, stack |
| Use of AI | Por ferramenta e finalidade (`AI_USAGE.md`) |
| NASA Data | FIRMS MODIS C6.1 (Terra, Aqua), VIIRS 375 m (S-NPP, NOAA-20) |
| Linguagem | "Seasonal fire outlook validated by hindcast vs climatology"; "location (~cell size)"; nunca "rain" nem precisão de propriedade |

## 11. Pendências do Capitão
| ID | Ponto | Sugestão |
|---|---|---|
| Git | ~~Tirar `data/processed/*.parquet` do commit da `ciencia/m1`~~ — conferido 22:53: nenhum `.parquet`/`.zip` indo para o `main` | ✅ |
| PRs | Merge `ciencia/m1` → `main`; depois `dados/export` (2.4) e `dados/frp-d40` (D40–D42) | Manhã de domingo |
| 2.4b | Reexport com vencedor (CP3) e `lo/hi` (CP4) → zip à Luana → commit único dos tiles antes do CP7 (D38) | Dom 07:30–10:00 |
| Bastão 2.4 | Confirmar que a Luana leu o zip dos tiles (Drive) | Confirmar |
| Conferência | `m1_eval_aqua_snpp.csv` da contagem regerado às 04:10 (0,448 / 0,693 / 1,099 ✅); números do FRP ficam registrados na D40 | ✅ |
| 3.3 | Commit na `ciencia/m2` (`m2.py`, `test_m2.py`, `docs/CIENCIA-3.3-M2.md`, linha em `AI_USAGE.md`) · `m2_tau_aqua_snpp.csv` → Samuel e Method · Samuel inclui M2 no `validate/run.py` | Melissa / Murilo / Samuel — manhã |
| D39 | FRP (D40) como variável do modelo — decidir com o hindcast do Samuel | CP5 |
| D44/D45 | Export diário (`harm_daily_<pai>.json`, contrato §13) + avisar Luana (calendário ano × dia, rodapé mensal do aditivo) + confirmar o que sai (SP cana, polimento D34) | Dom 07:30 (CP4) |
| Arquivos | Fechar o Excel, apagar o `fogo_diario_harm.csv` antigo (versão com dia vazio) e renomear os `_v2` | Agora |
| Repo | Merge do PR `ciencia/m1` (M1, grade, harmonize, res 5) e da governança; copiar D36 (revista) e D37 para `docs/DECISIONS.md` | Antes do CP3 |
| D30, D31, D32 | Janela Aqua→S-NPP, contrato da Ciência, detalhes do M1 | Em uso no código e validados na 3.2: confirmar |
| D03, D04, D05, D16, D22–D26 | Propostas antigas | Confirmar (D04 revisto pelo D36) |
| Texto | "~24 km" e "~22,6 km de lado" da D35/PREVISAO → célula res 5 ~17 km (res 4 ~45 km) | ✅ v2.10 |
| D41 | Retirar "arquivos > 50 MB" de `GOVERNANCE.md` §7, `CONTRIBUTING.md` e `SUBMISSION_CHECKLIST.md` no repo | Feito neste documento (§7); falta nos arquivos do repo |
| Dados (resto da 2.3) | Makefile com `AREA` e `RES` (`make ingest grid AREA=brasil RES=5`) · Samuel/Melissa: gerar `agg_monthly` res 4/res 5 na máquina deles (~1 min) ou receber pelo Drive | Antes do CP3 (não bloqueia) |
| 4.1 | `npm run build` (se falhar: `npm install-scripts approve esbuild`) → commit `git add app/ docs/FRONT-SISTEMA-WEB.md .github/workflows/pages.yml` (nunca `git add .`) → PR `front/setup` → `main` | Agora |
| Pages | Settings → Pages → Source = GitHub Actions (site fica sem dados até o commit final dos tiles, D38) | Melissa, após o merge |
| Front antigo | Avisar Samuel e Luana: front oficial = `app/`; `app.py`, `templates/`, `static/`, `index.html` e `js/` da raiz ficam só como referência (remover antes do CP7) | Agora |
| WIP solto | Arquivos `pipeline/{audit_daily,daily_harm,export_*,frp_harmonize,spot_check}.py`, `bridges/m2.py`, `tests/test_m2.py` (untracked) → commitar na `dados/frp-d40`/`ciencia/m2`; `notebooks/Model/*` modificados/apagados → confirmar com o dono antes de qualquer `restore` | Manhã |
| Sugestão (não decidida) | Previsão usar também features da célula-pai res 4 (vizinhança) e regra de confiança do app (res 5 com < 5 anos de fogo no mês → mostrar res 4) | Decidir com o hindcast do Samuel |

---
# Anexos (cópia dos arquivos de `docs/`)


## Anexo A — Registro de decisões (`docs/DECISIONS.md`)

Regra: Claude propõe; o Capitão decide. Toda decisão que muda escopo, método, dados ou prazo entra aqui.
Status: proposta · decidida · revertida. Nova decisão: próximo ID, uma linha, nunca apagar linhas antigas (reverter com nova decisão).

| ID | Data | Decisão | Motivo | Dono | Status |
|---|---|---|---|---|---|
| D01 | 13/11 | Desafio: Harmonization of MODIS and VIIRS Hot Spots | Dados prontos, desafio viável em 48 h | Equipe | decidida |
| D02 | 13/11 | Equipe de 3; fora do escopo: comparar duas áreas | Capacidade | Murilo | decidida (Terra e NOAA-20 revistos por D10/D11; equipe revista por D16) |
| D03 | 13/11 | Unidade da série: focos VIIRS-equivalentes (escala S-NPP) | S-NPP tem a maior sobreposição com MODIS | Murilo | proposta |
| D04 | 13/11 | Grade H3 res 4, agregação mensal para o app | Detalhe × tamanho no navegador | Dados | proposta |
| D05 | 13/11 | App estático, sem backend | Nada cai na demo | Front | proposta |
| D06 | 13/11 | Piloto Pantanal 2020 | Caso brasileiro forte | Murilo | proposta |
| D07 | 13/11 | Envio interno dom 20:00; congelamento dom 13:00 | 4 h de folga | Murilo | decidida |
| D08 | 13/11 | Manter tese de "25 anos" | Força da narrativa | Murilo | decidida (ver D10) |
| D09 | 13/11 | Brasil + vizinhos; prioridade Bolívia e Paraguai | Pantanal cruza fronteira | Dados | revertida por D28 |
| D10 | 13/11 | Terra nov/2000–jun/2002 via ponte Terra→Aqua, marcado "baixa confiança"; senão "~24 anos" | Sustentar D08 com validade | Murilo | proposta |
| D11 | 13/11 | S-NPP parou em 02/11/2026; continuidade com NOAA-20 convertido para escala S-NPP (sobreposição 2018–2025) | NRT só existe via NOAA-20/21 | Murilo | adiada por D33 (série termina em 2025; NOAA-20 fica harmonizado 2018–2025 como prova de continuidade) |
| D12 | 13/11 | C1 = bateria de testes de homogeneidade (Pettitt, KS no FRP, pegada espacial, sazonalidade) nas trocas de satélite | Prova objetiva; cobre mudança de método de coleta | Murilo | decidida |
| D13 | 13/11 | C2 = harmonização física em 3 etapas: grade comum ~2 km por passagem → limiar FRP por estação × dia/noite (bioma retirado por D33) → resíduo por célula × mês com termo aditivo | Razão estabiliza em ~3,45 a partir de ~2 km | Murilo | decidida |
| D14 | 13/11 | Subdivisão por pegada (375 m) não adotada no núcleo; possível M4 experimental | Inverte o viés (S-NPP/Aqua = 0,55) | Murilo | decidida |
| D15 | 13/11 | Escopo final (núcleo / se der tempo / bônus) conforme `GOVERNANCE.md` §4 | Discussão do grupo com notas por ideia | Equipe | decidida |
| D16 | 13/11 | Equipe de 4: Melissa e Samuel assumem o método (Ciência); Murilo assume Dados e mantém o papel de Capitão; Luana no Front. Atualiza `GOVERNANCE.md` §1 e o checklist (4 membros) | Divisão do Guia de Execução 48h | Murilo | proposta |
| D17 | 14/11 | Global Offers: adotar só o domínio GoDaddy (apontado para GitHub Pages, se gratuito); Copilot livre com registro; Planetary Computer MODIS 14A1 como bônus V4 (fração de observações válidas); não adotar Google Cloud, Meteomatics, Azure/Teams. Detalhes em `docs/RESOURCES.md` | Nenhuma oferta é necessária ao núcleo; evitar backend e chaves no navegador | Murilo | proposta |
| D18 | 14/11 | Persona "Ana, coordenadora de manejo do fogo no Pantanal" e pergunta principal (`claude/21`) | Uma pessoa que decide algo com o app | Murilo | proposta (substituída por D20) |
| D19 | 14/11 | Camada entidades de combate × pequenos agricultores com índice de prioridade (`claude/24`) | Impacto concreto | Equipe | proposta (narrativa absorvida por D20/D22; índice fora por D24) |
| D20 | 14/11 | Persona única: coordenador(a) de brigada/Defesa Civil que protege produtores rurais (pecuária, cana, agricultura familiar). Pergunta: *"Is fire in my area unusual right now, and when does it usually peak?"* (revista por D35: "…in my area or farm… in the coming months…") | Unifica D18, D19 e o PDF da equipe; agro vira o beneficiário | Murilo | proposta |
| D21 | 14/11 | Sem previsão de focos e sem "IA preditiva". "Antecipar" = probabilidade histórica + pico típico + score (padrão Twisters) | O desafio pede histórico × mediana; previsão não é validável em 48 h | Murilo | revertida por D35 (14/11 21:27) |
| D22 | 14/11 | Áreas prontas no app: Pantanal (pecuária, parte brasileira) e região canavieira de SP | Liga o caso agro do PDF da equipe ao app | Murilo | proposta |
| D23 | 14/11 | Cronograma v2 (`docs/PLANO-48H.md`): construção do app a partir de sáb 19:45; checkpoints CP0–CP8; congelamento dom 15:00; envio interno dom 21:00. Revisa D07 | Equipe começou a construção mais tarde que o Guia v1 | Murilo | proposta |
| D24 | 14/11 | Corte de escopo por tempo: AI1 (ML), KS e pegada → "se der tempo"; índice de agricultores (D19) e previsão → fora (previsão revista por D35); núcleo conforme `PLANO-48H.md` §4. Revisa D15 | ~25 h úteis de construção | Murilo | proposta |
| D25 | 14/11 | Fire Anomaly Score = percentil empírico do mês na área entre os mesmos meses do histórico harmonizado (0–100; faixas 60/85/95); pico típico = mês com maior % de anos como mês de pico | Fórmula pendente no Guia v1; transparente e testável | Samuel | proposta (implementação no JS pela Luana, D35) |
| D26 | 14/11 | Método: FRP na célula de 2 km = máximo; estação = trimestre (DJF, MAM, JJA, SON); estrato do limiar por bioma RESOLVE (bioma retirado por D33); λ ∈ {5, 20, 50} escolhido na validação | Escolhas pendentes no Guia v1; máximo evita somar pixels VIIRS do mesmo fogo | Melissa | proposta |
| D27 | 14/11 | "Análise preditiva" do app = indicador **Chance histórica de este mês ficar acima do normal**: normal = mediana do mês M em todos os anos da área; chance = % dos últimos 10 anos completos em que M ficou acima do normal; mostra "(k de 10 anos)"; < 5 anos com fogo em M → "dados insuficientes". Entra no núcleo junto do score (D25) | Atende o pedido de "antecipar" do PDF da equipe sem previsão (D21); mostra tendência recente; custo ~1 h | Murilo | decidida (14/11 14:22); mantida como baseline e plano B do D35 |
| D28 | 14/11 | Escopo geográfico = **Brasil inteiro** (substitui D09). Pantanal segue como piloto de desenvolvimento à tarde; Brasil roda à noite; export em tiles (célula-pai H3 res 2). Área pronta do Pantanal = parte brasileira. Mundo = evolução futura: o pipeline aceita qualquer país do FIRMS (parâmetro de país), documentado no README | Download menor, mais biomas para calibrar; visão global sem risco no prazo | Murilo | decidida (14/11 14:40) |
| D29 | 14/11 | Acrescentar `frp_sum` = **Σ FRP de todos os pixels** (MW) à grade `grid2km_pass` (célula 0,02° × passagem) e ao `agg_monthly` (mês), DATA_DICTIONARY §2/§5 — coluna extra para a Ciência testar; a unidade principal segue a contagem | Ideia "energia por quadrado" do PDF da equipe. Medido 14/11 17:09 (Brasil 2025): S-NPP/Aqua = 1,17 somando todos os pixels × 0,76 somando só o `frp_max` de cada célula; ΣFRP varia mais entre meses que a contagem (CV 16% × 12%). Grade de 100 km do mesmo PDF não adotada (conflita com D04/D13) | Murilo | decidida (14/11 21:13; texto ajustado ao `grid.py`, que já grava a soma de todos os pixels) |
| D30 | 14/11 | Ponte Aqua→S-NPP: ajuste 2012–2019, teste 2020–2021 (era ajuste 2012–2021). Terra→Aqua segue 2003–2010 | Pantanal: S-NPP/Aqua = 5,94 em 2012–19 e 7,15 em 2020–25 (deriva de órbita do Aqua, R05); misturar os regimes infla o fator | Murilo → Melissa | proposta (motivo revisto 14/11 18:07: na grade 0,02° não há degrau em 2020 — Brasil 3,96 → 3,98; a deriva do Aqua aparece em 2024–25, fora do ajuste. A janela segue útil como teste fora do tempo; ver R05) |
| D31 | 14/11 | Contrato interno da Ciência (`docs/CONTRATO-CIENCIA.md`): meses tocados pela pane do Aqua (202008, 202009) saem inteiros do ajuste e da nota; `transform(A, months)` usa só `n` e cobre células do fit ∪ de A; λ por ponte lido do `winner` de `validation.json` | Detalhes que o Guia v2 §3.1 deixou abertos; agregação mensal não permite cortar 16/08–02/09 | Melissa | proposta |
| D32 | 14/11 | Detalhes do M1 (`claude/31-ciencia-3.2-m1.md`): ΣA e ΣB de k(c,M) só nos meses com A > 0 (o B dos meses com A = 0 vai só para o termo aditivo); prior e termo aditivo com fallback até k_global(M) / a_global(M) | O Guia v2 §3.2 não diz em quais meses entram as somas; somar todo o B conta duas vezes o B dos meses com A = 0 | Melissa | proposta (prior por bioma retirado por D33) |
| D33 | 14/11 | **Sem análise por bioma; período 2000–2025 com todos os sensores.** (1) Bioma sai de tudo: limiar de FRP por trimestre × dia/noite (Brasil); prior do M1 = k_global(M) e a_global(M) (Brasil, mês do calendário); validação sem recorte por bioma; sem RESOLVE, `cell_biome.parquet` e geopandas. (2) Série e análise = nov/2000 → dez/2025, usando todos os anos de todos os sensores: Terra 2000–2025, Aqua 2002–2025, S-NPP 2012–2025, NOAA-20 2018–2025. (3) Cada sensor é harmonizado no período inteiro e os 4 aparecem sobrepostos (prova de consistência); a série do app segue a linha do tempo Terra → Aqua → S-NPP. (4) 2026, NRT e ponte N20 para 2026 saem (D11 adiada) | Simplifica e libera ~3 h (sem shapefile, sem estratos esparsos, sem Action NRT); usa 100% dos dados já baixados e conferidos | Murilo | decidida (14/11 16:10) |
| D34 | 14/11 | Gráfico "4 satélites, 1 curva" (D33 item 3) mostra **cada sensor no período inteiro**, com as divergências destacadas e explicadas, em vez de cortá-las: Aqua 2024–2025 marcado como **"deriva de órbita do Aqua detectada"** (+15–23% acima do S-NPP); Terra depois de 2011 marcado como **"fora da janela de calibração Terra→Aqua (2003–2010)"** (+15–60%). Nota no Method: nenhum dos dois trechos entra na série do app (linha do tempo usa S-NPP a partir de fev/2012) | Prévia do M1 no Brasil (`claude/31` §6): Aqua→S-NPP ±4% em 2012–2023 e NOAA-20→S-NPP ±3% em 2018–2025; divergências reais dos sensores viram achado em vez de defeito escondido. Alternativas descartadas: cortar o gráfico (parece esconder) e recalibrar o Terra pós-2011 (1–2 h num trecho fora do produto) | Murilo | decidida (14/11 18:07) |
| D35 | 14/11 | **Análise preditiva no sistema: Fire Outlook 2026** (`docs/PREVISAO.md`). Para cada célula H3 res 4 (e, por agregação, para áreas e fazendas desenhadas) e cada mês de 2026: P(acima do normal) + focos esperados com faixa 10–90%, emitida com dados até dez/2025. Modelo global HistGradientBoosting (classificador + quantis) com features históricas da série harmonizada 2003–2025. Validação por hindcast 2021–2025 contra climatologia, D27 e persistência; **portão no CP5 (dom 10:00)**: BSS > 0 contra os dois baselines e erro em log menor que a climatologia em ≥ 3 de 5 anos; se falhar, o app mostra o D27 e o modelo vai ao Method como achado. **Entrada principal: latitude e longitude** (fazendeiro ou outra persona digita o ponto → célula H3 res 4 que o contém → outlook + calendário histórico daquele ponto); desenho de área continua. Fazenda = região da célula (~17 km na res 5, D36), dito na tela. Pergunta da persona (D20) passa a incluir "nos próximos meses". Para caber: referência do score (3.8) → Luana no JS; `consistency_4sat` → Murilo; AI1, KS, pegada, P2, V1 fora. Reverte D21 e o item "previsão → fora" do D24 | Foco do sistema definido pelo Capitão: análise preditiva de áreas e fazendas a partir de dados antigos; a série harmonizada é o que torna o treino possível (sem o salto falso de 2012) | Murilo | decidida (14/11 21:27) |
| D36 | 14/11 | **H3 res 5 (~250 km², ~17 km) é a resolução do produto**: série harmonizada exibida, entrada lat/lon (`latLngToCell(lat, lon, 5)`), área desenhada (soma das células res 5), Fire Outlook 2026 (D35), export e app. **Res 4 (~1.770 km²) fica só como escala de calibração e validação** do método (M1/M2, `validation.json`, CP3) e como plano B do app/previsão (célula-pai com poucos dados ou portão do CP5 reprovado em res 5). **Res 6 descartada.** Revisa D04 | Pedido do Capitão (22:18): previsão mais exata para a persona (fazenda, parte de cidade). Medido 21:57 (Brasil, teste 2020–21, M1 λ = 20): R² log res 4 0,64 · res 5 0,27 · res 6 −0,43; ganho sobre a taxa única −35% · −25% · −17%. Res 5 ainda ganha da taxa única; res 6 pior que a média | Murilo | decidida (14/11 22:05; revista 22:18: res 5 = resolução do produto) |
| D37 | 14/11 | Série res 5 pelo **M1 hierárquico** (`pipeline/bridges/m1_hier.py`): total de cada célula-pai res 4 vem do M1 res 4; dividido entre as 7 filhas res 5 pelo padrão do M1 res 5 (sem histórico: participação histórica da filha). Σ filhas = pai, sempre. Comando: `harmonize --hier --agg data/interim/res5/agg_monthly.parquet` | M1 direto na res 5 subestima o total em 8% (0,92); o hierárquico herda o total da res 4 (0,99) e mantém o detalhe de ~17 km | Murilo → Melissa | **não adotada (14/11 22:20)**: medido na res 5 (teste 2020–21) — M1 direto consistency 0,522 · R² 0,273 · viés −0,25 · total 1,034; hierárquico 0,556 · 0,217 · −0,34 · 1,007. O M1 direto é melhor por célula e já acerta o total (±3%; a leitura de −8% vinha de métrica que somava só células ativas). Série res 5 = M1 direto; `m1_hier.py` fica como alternativa testada no Method |
| D38 | 14/11 | **Tiles do app fora do Git até o export final.** Export 2.4 em tiles por célula-pai H3 res 2 (`app/public/data/harm_<pai>.json`, R06 acionado). Os tiles (`harm_82*.json`) entram no `.gitignore` e vão para a Luana pelo Drive (zip) a cada export provisório (CP3, CP4); só o export final de domingo (antes do CP7) é commitado, uma vez, retirando a linha do `.gitignore`. Código (`pipeline/export.py`, testes) segue no Git normalmente | Export res 5 = 128 tiles, máx 1,35 MB, **total 101 MB**; commitar cada reexport somaria ~100 MB ao histórico por vez (~300 MB até domingo). Alternativa descartada: commitar a cada export | Murilo | decidida (14/11 22:47) |
| D39 | 15/11 | ΣFRP mensal por hexágono como **variável** do modelo D35 (alvo segue `n_harm`); adotar só se o hindcast 2021–2025 melhorar BSS/erro em log contra a versão sem FRP. Custo ~1 h (Samuel) | Testar a informação de intensidade (ideia "energia por quadrado" do PDF da equipe) sem trocar o alvo validado | Murilo → Samuel | proposta (00:00; usar a série da D40) |
| D40 | 15/11 | **ΣFRP mensal harmonizado entre satélites** com a mesma ponte M1 da contagem, sem alterar o M1: `pipeline/frp_harmonize.py prep` grava `agg_monthly` com `n = frp_sum ÷ s` (s = ΣFRP ÷ Σn do S-NPP = 22,8 MW), roda-se `m1 --eval` e `harmonize --lam 20` nele e `frp_harmonize.py csv` volta para MW. Resultado: ΣFRP na escala S-NPP, linha do tempo Terra → Aqua → S-NPP, res 5. Saída: CSV `cell, lat, lon, year, month, frp` (sem coluna dia). Vale só se ganhar do bruto e da taxa única no teste 2020–21 | Pedido do Capitão: FRP "homologado entre satélites" para a análise preditiva; FRP de MODIS e VIIRS não é comparável direto (S-NPP/Aqua 1,17 em ΣFRP, D29). Alternativas: só Aqua sem harmonizar; contagem harmonizada | Murilo | decidida (15/11 00:38); **validada 00:41**: consistency 0,337 × bruto 0,388 × taxa única 0,394; R² 0,536; viés −0,09; total 1,061 (termo aditivo, limitação declarada) |
| D41 | 15/11 | **Regra "arquivos > 50 MB proibidos no repo" revogada.** Limite passa a ser o técnico do GitHub (100 MB por arquivo; acima disso, `.gz`). `data/processed/res5_frp/` versionada com `git add -f`, exceção ao princípio "processado fora do Git" para esta pasta | Pedido do Capitão: disponibilizar a série D40 e a base de treino no GitHub sem rodar o pipeline | Murilo | decidida (15/11 00:52); regra retirada desta governança (§7) — falta retirar de `GOVERNANCE.md`, `CONTRIBUTING.md` e checklist no repo |
| D42 | 15/11 | Base de treino do modelo preditivo = **todos os hexágonos H3 res 5 do Brasil** (malha IBGE `paises/BR`, centro dentro do contorno) ∪ hexágonos com fogo, × 302 meses; hexágono sem foco = 0 em todos os meses. Contorno em `data/raw/br_pais.geojson` (IBGE, API de malhas v3, baixado 15/11/2026, qualidade padrão, 65 KB). Comando: `frp_harmonize csv --brazil data/raw/br_pais.geojson --gzip` → `data/processed/res5_frp/frp_harm_brasil.csv.gz` | Pedido do Capitão: o modelo precisa ver também onde nunca queima | Murilo | decidida (15/11 01:07); executada 01:25: 31.946 hexágonos (31.393 no contorno + 553 de borda com fogo), 9.647.692 linhas, 5.667.718 zeros, Σ FRP = série D40 |
| D43 | 15/11 | Valores **diários** harmonizados (focos e ΣFRP) por hexágono res 5: mensal harmonizado repartido entre os dias na proporção das detecções do satélite da linha do tempo (Terra → Aqua → S-NPP); meses sem detecção (termo aditivo) ficam como linha mensal com dia vazio; somas diárias = mensais (conferido no script). `pipeline/daily_harm.py` → `data/processed/res5_frp/fogo_diario_harm.csv` (`cell, lat, lon, year, month, day, frp, focos`) | Pedido do Capitão: dados com dia, mês e ano já harmonizados | Murilo | decidida (15/11 02:27) |
| D44 | 15/11 | **Calendário de incêndios diário** (mudança de rota após o CP3): o calendário do app passa a ser ano × dia, com os valores diários da D43 (tiles diários por célula-pai res 2, formato esparso). Proteções de Validity: (1) Fire Anomaly Score (D25), chance (D27) e Outlook (D35) **continuam mensais** — o dia é exibição, não base de comparação; (2) tela e Method dizem "distribuição diária estimada a partir do mensal harmonizado"; (3) antes de 2012 os dias vêm só das passagens do MODIS (fogo fraco esperado fica no mês). Custo: Dados ~3 h (export diário + contrato §13) · Front ~5 h · Ciência ~0 (sem nova validação). **Sai** (a confirmar no CP4): áreas prontas SP cana (D22, fica só Pantanal) e polimento do gráfico 4 satélites (D34 fica simples) | Pedido do Capitão: o calendário do produto funcionará de forma diária | Murilo | decidida (15/11 02:31) · fere a regra de agregação ≥ 8 dias do Guia MODIS para comparação → mitigado mantendo score/chance/Outlook mensais (R24) · dados diários gerados 03:00 (D43/D45) |
| D45 | 15/11 | No calendário diário (D44) **só entram dias com detecção**, convertidos para a escala S-NPP pelo fator do M1 (o dia original é mantido); a estimativa de fogo fraco dos meses sem detecção MODIS (termo aditivo do M1, sem dia possível) sai do diário e vira **nota mensal** (`fogo_aditivo_mensal_harm.csv`). Diário + nota = mensal harmonizado | O fator muda o valor, não o dia; o termo aditivo não vem de nenhuma detecção, então não tem data (conferido: hexágono 855f0483…, jan/2001 = 0 focos Terra no original; out/2001 = 1 foco em 11/10 → dia 11 mantido). Nenhum dia inventado (Validity). Alternativas descartadas: espalhar igual pelos dias; distribuir pelo padrão diário do S-NPP | Murilo | decidida (15/11 02:45); executada 03:00: 5.869.988 dias, 0 vazios; conservação ✓ focos 18.545.865 e ΣFRP 473,1 M MW |
| D46 | 15/11 | **Front = visual e telas do Samuel (landing + mapa) em versão estática** dentro de `app/` (Vite), sem o backend Flask (`app.py`, `/api/focos`): o navegador lê os tiles `harm_<pai res 2>.json` (`app/src/data.js`). Textos **EN/PT** (padrão EN, botão). Mapa: busca (Nominatim, só Brasil), lat/lon, clique → célula H3 res 5; **período De/Até (ano + mês)** filtra calendário e mapa; harmonizado × bruto; hexágonos pelo total do período (zoom ≥ 7); paleta cividis invertida (troca o verde → vermelho, não acessível). Textos ajustados à Validity: "~17 km, não uma propriedade" (D36/R19), Outlook só após o portão do CP5 (D35/R18), dados até dez/2025 (D33). Exibição: < 0,5 detecção no mês = cinza (R22), valor no tooltip. Dia (D44) entra com o export 2.4c | Mantém D05 (nada cai na demo, GitHub Pages grátis); Flask exigiria servidor no ar e a consulta aos dados ainda não existia (~2–3 h × ~1,5 h). Pedido do Capitão: partir do front do Samuel, bilíngue, com seleção de datas | Murilo | decidida (15/11 05:48) |


## Anexo B — Riscos (`docs/RISKS.md`)

| ID | Risco | Prob. | Impacto | Sinal de alerta | Plano B | Dono |
|---|---|---|---|---|---|---|
| R01 | ~~Dados 2026 não chegam~~ | — | — | — | Encerrado por D33 (série termina em dez/2025) | Dados |
| R02 | S-NPP 2012–2024 não baixado | Baixa | Crítico | Sáb 08:00 sem arquivo | Usar NOAA-20 como referência, ponte Aqua→N20 em 2018–2021 | Dados |
| R03 | Calibração ruim (métrica não melhora vs bruto) | Média | Alto | Validação sáb 22:00 | Fator global × mês; declarar limitação | Ciência |
| R04 | AI1 atrasa o núcleo | — | — | — | Encerrado: AI1 fora (D35) | Ciência (Samuel) |
| R05 | Deriva de órbita Terra/Aqua distorce pontes | **Confirmada (Aqua 2024–25); limitada** | Baixo para a série do app · Médio para o gráfico dos 4 satélites | **Medido 14/11 18:07 (Brasil, grade 0,02°, M1):** sem degrau em 2020 (S-NPP/Aqua 3,96 em 2012–19 → 3,98 em 2020–21). Aqua harmonizado passa o S-NPP em **+15% (2024) e +23% (2025)**. Terra→Aqua diverge depois de 2011 (+15–60%) | Ajuste Aqua→S-NPP em 2012–2019 (D30); série do app usa S-NPP desde fev/2012; divergências mostradas no gráfico (D34) | Ciência (Melissa) |
| R06 | JSON do app > 5 MB | **Ocorreu (22:44), mitigado** | Médio | Arquivo único 100,5 MB | **Tiles res 2 adotados**: 128 arquivos, máx 1,35 MB, total 101 MB; fora do Git até o final (D38) | Dados |
| R07 | Integração Dados × Front trava | Média | Alto | Contrato não congelado às 15:00 (CP1) | Front com dados falsos no formato do contrato | Dados + Front |
| R08 | Demo > 30 s, sem legenda em inglês ou link privado | Baixa | Crítico (desclassifica) | Checklist | Revisão por 2 pessoas + janela anônima | Murilo + Luana |
| R09 | Chave da API vazada no repositório | Baixa | Médio | Revisão de PR | `.env` no `.gitignore`; chave só em GitHub Secrets | Todos — **ocorreu em 13/11 (commit `541c557`): gerar chave nova; ver GOVERNANCE §9** |
| R10 | Cansaço | Alta | Médio | Erros bobos à noite | Dormir ≥ 5 h em turnos (`PLANO-48H.md` §2: 01:30–07:30) | Todos |
| R11 | Murilo sobrecarregado (Dados + Capitão) | Média | Alto | Checkpoint atrasado ou export parado | Vídeo puxado pela Luana; texto do método escrito pela Ciência | Murilo |
| R12 | Melissa e Samuel editam o mesmo código | Média | Médio | Conflito de merge | Interface `Bridge` fixa; cada um em seu módulo e branch | Ciência |
| R13 | Arquivos entre Dados e Ciência fora do contrato | Média | Alto | Ciência não consegue ler o que recebe | Fixar os 3 arquivos do `DATA_DICTIONARY.md` §5 no CP1 (15:00) | Dados + Ciência |
| R14 | Tempo comprimido: construção começa sáb 19:45 (D23) | **Média** (2.3 Brasil pronta às 17:53, adiantada) | Alto | CP2 ou CP3 atrasado > 1 h | Cortes de D24; AI1 fora. O plano B "só áreas prontas" deixa de valer para a série (Brasil res 4 e res 5 já existem); segue valendo para o bootstrap (CP4) | Murilo |
| R15 | Escopo "agro/previsão" do PDF da equipe volta durante a noite | Média | Alto | Tarefa de previsão ou índice aparece no grupo | D21 e D24: só entra por nova Dxx substituindo item do núcleo | Murilo |
| R16 | Score do app diferente da referência da Ciência | Média | Médio | Casos de `tests/score_cases.json` falham | Luana + Samuel conferem no CP5; o app mostra percentil simples | Luana + Samuel |
| R17 | Juiz pergunta "e o mês atual?" (série termina em 2025) | Média | Médio | Pergunta de mentor no pitch | Responder: score funciona para qualquer mês; NOAA-20 harmonizado prova que a série continua; 2026/NRT é o próximo passo | Murilo |
| R18 | Previsão não ganha da climatologia/D27 no hindcast | Média | Alto | `forecast_skill.json` às 10:00 com `passes_gate = false` | App mostra o D27 como outlook; modelo vai ao Method como achado (D35) | Samuel + Murilo |
| R19 | Promessa de precisão "na fazenda" ou de "chuva" sem base | Média | Alto (Validity) | Texto/tela com "sua fazenda vai queimar" ou "chance de chuva" | Sempre "região (~17 km na res 5, D36)" + probabilidade de fogo + skill; revisão no checklist | Murilo + Luana |
| R20 | Previsão atrasa o núcleo (série, app) | Média | Alto | Dom 09:00 sem features da série final | Treinar na série provisória (M1 λ 20) e declarar; núcleo tem prioridade | Murilo |
| R21 | Célula res 5 com pouco histórico deixa score/outlook ruidoso | Média | Médio | Célula com < 5 anos de fogo no mês; R² log da res 5 = 0,27 (res 4 = 0,64) | Mostrar a célula-pai res 4 com aviso (sugestão no §11); `low_conf` na série | Luana + Samuel |
| R22 | Termo aditivo do M1 cria "meses com fogo" pequenos antes de 2012 (2,9 M hexágono-mês no ΣFRP) → frequência de meses ativos diferente antes/depois de 2012 | Alta (medido) | Médio (features tipo `frac_active_M`) | Total ΣFRP 1,061 no teste; 73% das linhas pré-2012 só com aditivo | Limiar `--min-mw` (ex. 11 MW) nas features de frequência; total segue correto; declarar no Method | Murilo + Samuel |
| R23 | Base de treino (D42) muito desbalanceada (59% hexágono-mês zero; 3.173 hexágonos sempre zero) | Média | Médio | Métricas do hindcast dominadas por zeros | Samuel compara hindcast com e sem os hexágonos sempre zero; reportar BSS/AUC só nos ativos também | Samuel |
| R24 | Calendário diário (D44) fere a regra "agregação ≥ 8 dias" (Guia MODIS C6 §7.1.1); juiz questiona comparação dia a dia antes × depois de 2012 | Média | Alto (Validity) | Pergunta de mentor/juiz sobre o diário | Score/chance/Outlook mensais; rótulo "distribuição diária estimada"; Method explica D43; mostrar que a soma do mês é a harmonizada | Murilo + Luana |
| R25 | Site publicado sem dados até o commit final dos tiles (D38) ou build falhar no Pages | Média | Alto (demo/link) | Link do Pages abre com "No fire detected" em todo lugar | Demo local (`npm run dev`) até o CP7; commit único dos tiles antes do CP7; `npm run build` local antes do PR; testar o link em anônimo e no celular (R08) | Murilo + Luana |


## Anexo C — Cronograma hora a hora (`docs/PLANO-48H.md`)
### 2. Cronograma das 48 h
Legenda: CP = checkpoint (15 min, cada um mostra o que **roda**).

#### Sábado 14/11
| Hora | Murilo (Capitão + Dados) | Melissa (Harmonização) | Samuel (Validação) | Luana (Front) |
|---|---|---|---|---|
| 00:00–13:30 | ✔ Fase 0, estratégia, persona | ✔ | ✔ | ✔ |
| **13:30–14:00** | **CP0 Replanejamento**: aprovar D20–D26, D16, D17; CODEOWNERS; chave FIRMS nova | idem | idem | idem |
| 14:00–15:00 | Contrato de dados final + `harm_monthly.json` **falso** → Luana | Ler §3 do Guia Técnico; ambiente; abrir notebook 2025 | Ambiente; esqueleto do validador | Revisar contrato; wireframe das 4 telas (papel/Figma) |
| **15:00** | **CP1 Contrato congelado** | | | |
| 15:00–19:00 | Baixar S-NPP 2012–24 e N20 2018–24 (Brasil) · ingest + clean do **Pantanal** · grade 2 km + H3 (Pantanal, 2000–2025, 4 sensores) | `sensors.yaml` + `Bridge` · reproduzir 5,42 → 3,45 → ≈1,0 (2025) · M1 | Métrica + split por ano + baselines (bruto, fator global) · testar com M1 | Vite + Leaflet + deploy "hello world" no GitHub Pages · leitor do JSON falso |
| 17:00 | | Mentor: método (M2, M3, M5) | Mentor (junto) | |
| **19:00** | **CP2 Fundação**: Pantanal agregado · M1 no validador · site publicado | | | |
| 19:00–19:45 | Jantar | Jantar | Jantar | Jantar |
| 19:45–23:30 | ~~Pipeline Brasil inteiro~~ ✅ (2.3 feita às 17:53; res 5 às 21:57) · 2.4 export provisório (M1 λ 20, res 5) → Luana · pendências Git | Limiar FRP por trimestre × dia/noite (D33) · **M2** | Rodar bruto × M1 × M2 por ponte → `validation.json` | **Início do app**: mapa + desenho + lat/lon → H3 → calendário (dados falsos) |
| **23:30** | **CP3 Núcleo científico**: M2 > bruto na métrica · JSON real do Pantanal no app | | | |
| 23:30–02:00 | Export do método vencedor · P1 features da previsão (série res 5) | Disparar **bootstrap C4** (roda à noite) | Pettitt + sazonalidade (raw × harm) → `pettitt.json` v0 | Toggle bruto × harmonizado · série com emendas |

#### Turnos de sono (≥ 5 h, R10)
| Pessoa | Dorme | Máquina rodando |
|---|---|---|
| Luana | 01:30–07:00 | — |
| Samuel | 02:00–07:00 | — |
| Melissa | 02:00–07:00 | Bootstrap C4 (200×) |
| Murilo | 02:30–07:30 | — (2.3 concluída; nada a rodar) |

#### Domingo 15/11
| Hora | Murilo | Melissa | Samuel | Luana |
|---|---|---|---|---|
| **07:30** | **CP4 Manhã**: série completa com `lo/hi/low_conf` chegou? | | | |
| 07:30–10:00 | Export final (Brasil) · checar tamanho (R06) · áreas prontas Pantanal + SP cana (D22) | Harmonizar os 4 sensores 2000–2025 (D33) · deriva (R05) | `analytics`: Fire Anomaly Score + probabilidade de pico (D25) → `season.json` | Score + card de pico · faixa de incerteza · CSV |
| **10:00** | **CP5 Corte final**: o que não roda sai (AI1, KS, pegada) | | | |
| 10:00–12:00 | `sensors4.json` (4 satélites) · `meta.json` · frase de impacto com fonte | `METHOD.md` com números finais | Números finais → página Method · parágrafo "how it works" (EN) | Página Method · gráfico 4 satélites · celular · acessibilidade |
| 11:00 | Mentor: pitch (com Luana) | | | Mentor: pitch |
| **12:00** | **CP6 Autoavaliação** (20 min): nota 1–5 por critério | | | |
| 12:30–15:00 | Texto da submissão (EN) · README | Revisão do método + bugs | Revisão de números no app | Polimento + bugs · roteiro do vídeo com Murilo |
| **15:00** | **CP7 Congelamento**: só `fix/<tema>` | | | |
| 15:00–19:00 | Página do projeto (formato Twisters) · `open/` · `AI_USAGE.md` | Revisa página (método) | `make all` em máquina limpa | Gravar + editar vídeo ≤ 30 s com legenda EN · prints |
| 19:00–20:30 | Checklist com Luana | Checklist (2ª pessoa) | Teste em anônimo e celular | Checklist |
| **21:00** | **CP8 Envio interno** + print do banner | | | |
| 23:59 | Prazo oficial | | | |

### 5. Passagens de bastão
| Quando | Arquivo | De → Para |
|---|---|---|
| Sáb 15:00 | `harm_monthly.json` falso | Murilo → Luana |
| Sáb 17:00 | `data/clean/` Pantanal | Murilo → Ciência |
| Sáb 19:00 | `grid2km_pass.parquet` + `agg_monthly.parquet` (Pantanal, 2000–2025) | Murilo → Melissa, Samuel |
| Sáb 22:00 | M1 e M2 do Pantanal | Melissa → Samuel |
| Sáb 23:30 | `harm_series.parquet` (Pantanal, vencedor) | Ciência → Murilo |
| Sáb 23:45 | ~~`harm_monthly.json` real Pantanal~~ → **tiles res 5 Brasil** (`harm_tiles_res5_M1prov.zip`, Drive, D38) | Murilo → Luana |
| Dom 07:30 | Série Brasil com `lo/hi/low_conf` | Melissa → Murilo → Luana |
| Dom 10:00 | `validation.json`, `pettitt.json`, `season.json` | Ciência → Murilo → Luana |
| Dom 12:00 | Números e textos do método | Ciência → Luana, Murilo |

Quem entrega avisa no grupo; quem recebe confirma que leu. Só o Murilo escreve em `app/public/data/`.

### 7. Análise preditiva no cronograma (D35)
| Quando | Murilo | Samuel | Luana |
|---|---|---|---|
| Sáb 23:30–01:30 | `forecast/features.py` na série provisória (M1 λ 20) | Pettitt v0 (como antes) | Toggle + série (como antes) · campo lat/lon → célula |
| Dom 07:30–10:00 | Features na série final + casos de teste do score | **Modelo + hindcast 2021–2025 → `forecast_skill.json`** | Score/pico/chance no JS + card Outlook com JSON falso |
| **Dom 10:00 (CP5)** | **Portão da previsão** | | |
| Dom 10:00–12:00 | `forecast_2026.json` + `sensors4` + `consistency_4sat` | Números do Method + skill | Camada de mapa P(acima do normal), linha 2026 no calendário |
Detalhes: `docs/PREVISAO.md`.


## Anexo D — Análise preditiva (`docs/PREVISAO.md`)

Reverte D21 ("sem previsão"). O D27 (chance histórica) continua no app como **baseline e plano B**.

### 1. O que o sistema prevê
| Item | Definição |
|---|---|
| Pergunta (D20 revista) | *"For this latitude/longitude, will fire activity be above normal in the coming months, and when does it usually peak?"* |
| Entrada (decidida 21:31) | **Latitude e longitude** digitadas (ou clique no mapa) → `latLngToCell(lat, lon, 5)` → calendário histórico + Outlook 2026 da célula. Desenhar área/fazenda continua como opção |
| Unidade espacial (D36) | Célula H3 **res 5** (~250 km², ~17 km de largura). **Fazenda** = polígono ou ponto → célula(s) res 5 que a contêm. A tela diz "região da fazenda (~17 km)", nunca "dentro da fazenda". Res 4 (~45 km) = calibração e plano B |
| Horizonte | Jan → dez/2026, emitida com dados até dez/2025 (série termina em 2025, D33) |
| Saída por célula × mês | (a) **P(acima do normal)** · (b) focos esperados com faixa 10–90% |
| Normal | Mediana de n_harm(c, M) nos anos anteriores ao ano previsto (sem vazamento) |
| Saída por área/fazenda | Focos esperados = soma das células (faixa = soma de q10 e q90, conservadora); P(área acima do normal) = média das P das células ponderada pelo histórico de focos (aproximação declarada) |
| Por que só funciona agora | O modelo aprende 2003–2025 numa série **harmonizada**; com a série bruta ele aprenderia o salto falso de 2012 como "tendência" |

### 1b. O que o sistema NÃO prevê
Chuva. Os dados são focos de calor (FIRMS); a saída é **probabilidade de atividade de fogo acima do normal**. Probabilidade de chuva exigiria outro dado (ex.: NASA GPM IMERG ou POWER) e uma decisão nova.

### 2. Modelo
| Item | Escolha |
|---|---|
| Linha de dados | célula × ano alvo Y × mês M (Brasil, 2004–2025; Terra-only fora por `low_conf`) — ~1 M linhas |
| Features (só dados ≤ dez/Y−1) | `clim_med` e `clim_mean_log` de (c, M) · `last_M` = n(c, M, Y−1) · `mean3_M` = média de M em Y−3..Y−1 · `anom_prev_year` = log(total Y−1 / mediana anual) · `trend10` = inclinação de Sen do log anual em 10 anos · `son_prev` = anomalia de set–dez de Y−1 · `frac_active_M` = % de anos com fogo em M · `M` · lat, lon do centro |
| Probabilidade | `HistGradientBoostingClassifier` (alvo: y > normal) |
| Quantidade | `HistGradientBoostingRegressor(loss="quantile")` em log1p(y), quantis 0,1 · 0,5 · 0,9 |
| Um modelo para o Brasil | Global (todas as células); sem bioma (D33) |
| Base de linhas (D42) | Todos os hexágonos res 5 do Brasil × meses (zeros incluídos): `frp_harm_brasil.csv.gz`, 31.946 hexágonos |
| FRP (D39, proposta) | ΣFRP harmonizado (D40) como variável extra; adotar só se o hindcast melhorar |

### 3. Validação (hindcast, origem móvel) — é o que torna a previsão defensável
| Item | Regra |
|---|---|
| Anos de teste | 2021, 2022, 2023, 2024, 2025 — cada um treinado só com anos anteriores |
| Baselines | (1) climatologia: P = fração histórica acima da mediana, q50 = mediana · (2) D27: frequência dos últimos 10 anos · (3) persistência: valor do ano anterior |
| Métricas | Brier Skill Score (BSS) vs (1) e (2) · AUC · mediana \|log((q50+1)/(y+1))\| vs (1) e (3) · cobertura da faixa 10–90% (meta ≈ 80%) |
| **Portão (CP5, dom 10:00)** | BSS > 0 contra os dois baselines **e** erro em log menor que a climatologia em ≥ 3 dos 5 anos |
| Se passar | App mostra o Outlook 2026 + "skill vs climatology: +X%" |
| Se não passar | App mostra o D27 como outlook; o modelo vai para a página Method como "testado, não superou a climatologia" (achado honesto, conta em Validity) |

### 4. Arquivos (DATA_DICTIONARY §9)
| Arquivo | Conteúdo | Escreve |
|---|---|---|
| `data/processed/forecast_features.parquet` | cell, Y, M, features, y, above | Murilo |
| `app/public/data/forecast_2026.json` | `{"months":[202601..202612], "cells":{"<h3>":{"p":[×100 int], "q10":[×10], "q50":[×10], "q90":[×10]}}}` (tiles por célula-pai res 2, como `harm_monthly`) | Murilo |
| `app/public/data/forecast_skill.json` | por ano de teste e geral: bss_clim, bss_d27, auc, log_err_model / clim / persist, coverage_80, `passes_gate` | Samuel |

### 5. Quem faz o quê
| Quando | Tarefa | Dono | Depende de |
|---|---|---|---|
| Sáb 23:30–01:30 | `pipeline/forecast/features.py` com a série provisória res 5 (M1, λ = 20) | Murilo | `data/processed/res5/harm_series.parquet` ✅ (22:22) |
| Dom 07:30–09:00 | Features na série final do Brasil | Murilo | 3.4 (série com incerteza) |
| Dom 07:30–10:00 | `pipeline/forecast/model.py`: hindcast 2021–2025, baselines, `forecast_skill.json`, previsão 2026 | Samuel | features |
| **Dom 10:00** | **Portão (CP5)** | Capitão | `forecast_skill.json` |
| Dom 10:00–11:00 | Export `forecast_2026.json` | Murilo | modelo aprovado |
| Dom 10:00–12:00 | Card "Outlook 2026", camada de mapa P(acima do normal), linha 2026 hachurada no calendário | Luana | `forecast_2026.json` (falso antes) |

### 6. O que sai para caber (regra de mudança de rota)
| Item | Antes | Agora |
|---|---|---|
| Referência Python do score/pico/chance (3.8) | Samuel | Luana implementa direto no JS; Murilo escreve os 3 casos de teste |
| `consistency_4sat.json` (3.6b) | Samuel | Murilo, junto do `sensors4.json` |
| AI1, KS, pegada, P2, V1 | Se der tempo | Fora |

### 7. Como falar na submissão
- "Seasonal fire outlook for 2026, trained on a harmonized 2003–2025 record and validated by hindcast (2021–2025) against climatology."
- Sempre com o número de skill. Nunca "prever incêndio na fazenda": é a região (~17 km na res 5, D36) e é probabilidade.


## Anexo E — Contrato de dados (`docs/DATA_DICTIONARY.md`)

Congelar no CP1 (sáb 15:00, D23). Mudanças exigem decisão registrada (Dados + Front).


### 1. `data/clean/<sensor>/<ano>.parquet` (focos limpos)
| Coluna | Tipo | Descrição |
|---|---|---|
| sensor | str | TERRA, AQUA, SNPP, N20, N21 |
| ts | timestamp UTC | `acq_date` + `acq_time` (HHMM com zfill(4)) |
| latitude, longitude | float64 | graus |
| frp | float32 | Fire Radiative Power (MW) |
| daynight | str | D / N |
| pixel_area | float32 | scan × track (km²) |
Mapeamentos: MODIS `satellite` Terra/Aqua → TERRA/AQUA; VIIRS `N` → SNPP, `N20` → N20.
Filtros já aplicados: `type = 0`, MODIS conf ≥ 30, VIIRS conf ∈ {n, h}, ts ≥ 2000-11-01. Piloto: mesma estrutura em `data/clean_pantanal/`. Arquivos auxiliares (nota 14/11, sem mudança de schema): `filter_log.csv` (file, sensor, year, step, rows_in, rows_out, removed, pct_removed, versions) e `manifest.csv`.

### 2. `data/interim/agg_monthly.parquet`
| Coluna | Tipo | Descrição |
|---|---|---|
| sensor | str | — |
| cell | str | H3 res 4 (`data/interim/`) ou res 5 (`data/interim/res5/`, D36) |
| ym | int | AAAAMM |
| n | int | focos (após grade comum ~2 km por passagem) |
| frp_mean, frp_p90 | float | FRP médio e percentil 90 |
| night_frac | float | fração noturna |
| pix_area | float | área média do pixel (km²) |
| frp_sum | float | Σ FRP de todos os pixels no mês (MW) — coluna extra para teste (D29, texto pendente) |

### 3. `app/public/data/harm_monthly.json` (consumido pelo Front)
```json
{
  "months": [200011, 200012, "..."],
  "cells": { "<h3>": [12, 0, 35, "... n_harm × 10, inteiro"] },
  "raw":   { "<h3>": ["... n bruto"] },
  "lo":    { "<h3>": ["... limite inferior × 10"] },
  "hi":    { "<h3>": ["... limite superior × 10"] },
  "low_conf": { "<h3>": [0, 1, "..."] },
  "src": ["TERRA", "AQUA", "...", "SNPP", "N20"]
}
```
Regras: vetores alinhados com `months`; valores multiplicados por 10 e arredondados; células sem fogo omitidas.

### 4. Outros arquivos do app
| Arquivo | Conteúdo |
|---|---|
| `season.json` | `{ "<h3>": { "onset": doy, "peak": doy, "end": doy, "trend_d_decade": float, "p": float } }` |
| `validation.json` | por ponte e método: consistency, r2_log, bias, n_test, vencedor |
| `pettitt.json` | por ponte: % células com quebra (raw, harm) + lista de células |
| `nrt_last7.json` | ~~focos NOAA-20 dos últimos 7 dias~~ — fora por D33 |
| `sensors4.json` | Brasil e áreas prontas: série anual harmonizada de cada sensor (TERRA, AQUA, SNPP, N20) 2000–2025, × 10 inteiro — gráfico "4 satélites, 1 curva" (D33) |
| `consistency_4sat.json` | razão harmonizado/harmonizado por par de sensores e ano (Samuel, D33) |
| `meta.json` | fontes, versões, datas de download, commit do pipeline |

### 5. Arquivos entre Dados e Ciência (proposta — aprovar na revisão das 10:00, R13)
| Arquivo | Colunas mínimas | Escreve | Lê |
|---|---|---|---|
| `data/interim/grid2km_pass.parquet` | sensor, ts, daynight, gy, gx (`floor(lat/0,02)`, `floor(lon/0,02)`), cell (H3 res 4), ym, `frp_max`, `frp_sum` (Σ FRP dos pixels da célula), n_pix, pix_area · passagem = sensor + ts + daynight · o M2 lê `sensor, cell, ym, daynight, frp_max` (`base.passes_reader`) | Murilo | Melissa |
| `data/processed/harm_series.parquet` (res 4) · `data/processed/res5/harm_series.parquet` (res 5, produto) | cell, ym, n_harm, n_raw, lo, hi, low_conf, src · provisória (M1 λ 20, `harmonize.py`): `lo = hi = n_harm`, `low_conf` só no trecho Terra até a 3.4 | Melissa (provisória: Murilo) | Murilo |
Resumo do FRP dentro da célula de 2 km: **máximo** (D26, proposta). Unidade de `n_harm`: detecções por célula de 0,02° por passagem, escala S-NPP (D03). Contrato interno Melissa × Samuel: `docs/CONTRATO-CIENCIA.md`.

### 6. Arquivos novos do app (v2)
| Arquivo | Conteúdo | Escreve |
|---|---|---|
| `areas.json` | `[{ "id", "name", "polygon": [[lat, lng], ...], "story" }]` — Pantanal e SP canavieira (D22) | Murilo |
| `harm_<parent>.json` (só se R06 acionar) | Mesmo formato da §3, um arquivo por célula-pai H3 res 2 | Murilo |
| `tests/score_cases.json` | 3 áreas × mês: entrada (vetor da área) e saída esperada (score, razão, pico) | Samuel |

### 7. CSV baixado pelo usuário
`year,month,harmonized,lo,hi,raw,low_conf` — valores já divididos por 10; uma linha por mês da área selecionada.

### 8. Fonte do valor por mês (`src`)
TERRA 200011–200206 (low_conf) · AQUA 200207–201201 · SNPP 201202–202512 (D10, D33). Período fechado: nov/2000 → dez/2025

### 9. Previsão (D35)
| Arquivo | Conteúdo | Escreve |
|---|---|---|
| `data/processed/forecast_features.parquet` | cell, Y, M, features (PREVISAO §2), y, above | Murilo |
| `forecast_2026.json` | `{"months":[202601..202612], "cells":{"<h3>":{"p":[×100], "q10":[×10], "q50":[×10], "q90":[×10]}}}`; tiles por célula-pai res 2 | Murilo |
| `forecast_skill.json` | por ano de teste e geral: bss_clim, bss_d27, auc, log_err_model/clim/persist, coverage_80, passes_gate | Samuel |

### 10. Resoluções e caminhos (D36)
| Resolução | `agg_monthly` | Série harmonizada | Uso |
|---|---|---|---|
| res 4 (~1.770 km²) | `data/interim/agg_monthly.parquet` | `data/processed/harm_series.parquet` | Calibração/validação (CP3), plano B |
| **res 5 (~250 km²)** | `data/interim/res5/agg_monthly.parquet` | `data/processed/res5/harm_series.parquet` | **Produto**: app, lat/lon, previsão, export |
| Pantanal res 4 | `data/interim/pantanal/agg_monthly.parquet` | `data/processed/pantanal/harm_series.parquet` | Piloto / export do CP3 |
Gerar: `python -m pipeline.grid --area brasil [--res 5]` · `python -m pipeline.bridges.harmonize --lam 20 [--agg …/res5/agg_monthly.parquet --out …/res5/harm_series.parquet]`. `data/processed/` fica fora do Git (exceção `res5_frp/`, D41).

### 11. Export do app (2.4, D38)
| Arquivo | Conteúdo | Escreve |
|---|---|---|
| `app/public/data/harm_<pai>.json` | Formato §3 (`months`, `src`, `cells`, `raw`, `lo`, `hi`, `low_conf`), uma célula-pai H3 **res 2** por arquivo; células res 5; × 10 exceto `low_conf`; `raw` também × 10 | Murilo (`python -m pipeline.export`) |
| Leitura no app | ponto/polígono → células res 5 → `cellToParent(cell, 2)` → `fetch(harm_<pai>.json)`; 404 = pai sem fogo | Luana |
| Git | `harm_82*.json` no `.gitignore` até o export final | D38 |

### 12. FRP e base de treino (D29, D40, D42)
| Arquivo | Conteúdo | Gera |
|---|---|---|
| `data/processed/res5/frp_monthly.parquet` | cell, lat, lon, ym, year, month, n_harm, n_raw, low_conf, src, `frp_sum_<S>` e `n_<S>` dos 4 satélites (não harmonizados), `frp_sum_src` — 8.689.446 linhas | `export_frp_monthly` |
| `data/interim/res5_frp/agg_monthly.parquet` + `scale.json` | agg com `n = frp_sum ÷ s` (s = 22,8 MW) para o M1 | `frp_harmonize prep` |
| `data/processed/res5_frp/harm_series.parquet` | ΣFRP harmonizado (em unidades de s), mesmas colunas do §5 | `harmonize --agg …res5_frp…` |
| `data/processed/res5_frp/frp_harm_nonzero.csv` | `cell, lat, lon, year, month, frp` (MW, escala S-NPP), só FRP > 0 — 3.979.974 linhas | `frp_harmonize csv` |
| `data/processed/res5_frp/frp_harm_brasil.csv.gz` | Mesmas 6 colunas, **todos os hexágonos do Brasil × 302 meses, zeros incluídos** — 9.647.692 linhas (base de treino) | `frp_harmonize csv --brazil … --gzip` |
| `data/processed/res5/audit_*` | Auditoria diário × mensal (`audit_daily`) | `audit_daily` |

### 13. Diário harmonizado e calendário diário (D43–D45)
| Arquivo | Conteúdo | Gera |
|---|---|---|
| `data/processed/res5_frp/fogo_diario_harm.csv` | `cell, lat, lon, year, month, day, frp, focos` — só dias com detecção do satélite da época, convertidos (escala S-NPP); **day sempre preenchido**; 5.869.988 linhas, 28.053 hexágonos, ~322 MB | `python -m pipeline.daily_harm` |
| `data/processed/res5_frp/fogo_aditivo_mensal_harm.csv` | `cell, lat, lon, year, month, frp, focos` — fogo fraco estimado sem detecção (termo aditivo), só antes de 2012; 2.034.079 linhas | idem |
| Regra | Σ dias + aditivo = mensal harmonizado (conservação no script) · dia ausente no diário = 0 | — |
| `app/public/data/harm_daily_<pai>.json` (a fazer, 2.4c) | Tiles res 2, formato esparso: só dias com fogo por célula res 5 (índice do dia, focos × 10, frp × 10) + aditivo mensal | Murilo → Luana |

### 14. Leitura no app (D46, `app/src/data.js`)
| Regra | Implementação |
|---|---|
| Ponto → tile | `latLngToCell(lat, lon, 5)` → `cellToParent(…, 2)` → `fetch(harm_<pai>.json)`; 404 = pai sem fogo |
| Validação | `validateTile`: `months` crescente, `src` alinhado, vetores do tamanho de `months`, inteiros; tile fora do contrato gera erro na tela |
| Valores | ÷ 10; célula ausente = 0; `lo`/`hi` ausentes = próprio valor (série provisória); `low_conf` da área = 1 se alguma célula com fogo no mês tiver 1 |
| Período | `periodIndex`/`slicePeriod` (De/Até inclusivos); `cellTotals` para as cores do mapa |
| Conferido | 128 tiles: 0 fora do contrato, 28.769 células, 302 meses, Σ harm 18.529.552 |


## Anexo F — Fontes e qualidade (`docs/DATA_GOVERNANCE.md`)

### Princípios
1. **Bruto é imutável.** Arquivos baixados não são editados; ficam em `data/raw/` no Drive da equipe, fora do Git.
2. **Processado é sempre gerado por script.** Nada em `data/processed/` é editado à mão; `make all` recria tudo; `data/processed/` está no `.gitignore` — exceção D41: `data/processed/res5_frp/` versionada com `git add -f`.
3. **Toda fonte tem versão e data de download** registradas na tabela abaixo e em `meta.json` do export.
4. **Segredos fora do código.** `MAP_KEY` só em `.env` local e em GitHub Secrets.
5. **Sem dados pessoais.** O projeto usa apenas dados de satélite públicos.

### Fontes
| Fonte | Produto | Período | Origem | Versão (campo `version`) | Baixado em | Por |
|---|---|---|---|---|---|---|
| MODIS Terra/Aqua | FIRMS resumo anual por país (C6.1) | 2000–2025 | firms.modaps.eosdis.nasa.gov/country | 6.2 (2000) · 61.03 (2024–25) [confirmar significado] | 13/11/2026 | Dados |
| VIIRS S-NPP 375 m | FIRMS resumo anual (`viirs-snpp`) | 2012–2025 | idem | 2 | ZIPs `all_countries` 2012–2025 ✅ (até 14/11/2026) | Dados |
| VIIRS NOAA-20 375 m | FIRMS resumo anual (`viirs-jpss1`) | 2018–2025 | idem | 2 | ZIPs `all_countries` 2018–2025 ✅ (até 14/11/2026) | Dados |
| ~~2026, NRT, RESOLVE~~ | fora por D33 | — | — | — | — | — |
| Contorno do Brasil (D42) | IBGE, API de malhas v3, `paises/BR`, GeoJSON (qualidade padrão, 65 KB) | — | servicodados.ibge.gov.br | — | 15/11/2026 | Dados |
| Escopo geográfico | Brasil inteiro (D28); mundo como evolução | — | — | — | — | — |
| Referência externa | INPE BDQueimadas (V1) | mensal | INPE | — | — | Capitão |

### Fluxo (linhagem)
`data/raw` (ZIP/CSV) → `data/clean` (Parquet, schema único, filtros) → `data/interim` (agregados) → `data/processed` (série harmonizada, validação) → `app/public/data` (JSON) e `open/` (dataset aberto).

### Regras de qualidade aplicadas
| Regra | Fonte da regra |
|---|---|
| Manter só `type = 0` (vegetação presumida) | Guia MODIS C6 §5.5 |
| MODIS `confidence ≥ 30`; VIIRS `confidence ∈ {n, h}` | Guia MODIS C6 Tab. 10 e §8.4.2 |
| Série a partir de nov/2000 | Guia MODIS C6 §7.2.1 |
| Excluir 16/08–02/09/2020 das métricas das pontes com Aqua | Guia MODIS C6 §7.2.4 |
| Agregação temporal ≥ 8 dias | Guia MODIS C6 §7.1.1 |
| Teste de conservação: soma de focos agregados = linhas filtradas | Interno |

### Resultado dos filtros (2.1, sáb 14/11)
| Recorte | parse | date | type ≠ 0 | conf baixa | Mantido |
|---|---|---|---|---|---|
| Brasil 2025 · MODIS | 0% | 0% | 1,7–2,6% | 4,0–4,6% | ~94% |
| Brasil 2025 · VIIRS | 0% | 0% | ~1,9% | 9,8–10,7% | ~88–89% |
| Pantanal 2000–25 · MODIS | 0% | 0% | 0,07–0,13% | 5,5–6,2% | ~94% |
| Pantanal 2000–25 · VIIRS | 0% | 0% | 0,5–0,7% | 8,5–8,7% | ~91% |
Conferência: Brasil 2025 reproduz `08-fatos-dados` com 0,00% de diferença. Teste de conservação Parquet = log ✅. Log completo: `data/clean*/filter_log.csv`.

### Limitações declaradas
- Arquivos de focos não informam nuvem nem falta de observação.
- FRP de sensores diferentes não é diretamente comparável; o limiar é um indicador calibrado. ΣFRP só é comparado entre satélites depois da ponte M1 (D40); ΣFRP é índice de intensidade (soma de potências instantâneas), não energia queimada.
- Termo aditivo do M1 coloca FRP/contagem pequenos esperados em meses pré-2012 sem detecção MODIS (R22).
- Contorno IBGE simplificado (65 KB): hexágonos de borda podem variar; os 553 de borda com fogo são mantidos.
- Calendário diário (D44/D45): dias vêm das passagens do satélite de cada época; antes de 2012 o fogo fraco que o MODIS não via (8,6% dos focos harmonizados) não tem dia e aparece só como nota mensal. Comparações (score, chance, Outlook) são mensais por causa da regra de agregação ≥ 8 dias do Guia MODIS (R24).
- CSV de focos individuais só para áreas prontas e últimos 7 dias (volume).

### Uso e citação
Dados NASA FIRMS sob a política de dados abertos da NASA. Citar: "NASA FIRMS, MODIS Collection 6.1 and VIIRS 375 m active fire products". Dataset harmonizado publicado em `open/` sob MIT para o código e com a mesma citação para os dados.


## Anexo G — Contrato interno da Ciência (`docs/CONTRATO-CIENCIA.md`)

Fonte da verdade: `config/sensors.yaml` + `pipeline/bridges/base.py` (regras R1–R7 no topo do arquivo). Teste: `pytest tests/test_bridge_contract.py`. Mudança = decisão nova (Dxx).

### 1. Quem mexe em quê (R12)
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

### 2. Interface `Bridge`
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

### 3. `validation.json` (Samuel → Melissa, Luana)
```json
{"aqua_snpp": {
   "split": "LOYO no fit + teste 2020–2021",
   "results": [{"method": "M1", "lam": 20, "consistency": 0.31, "r2_log": 0.74, "bias": -0.02, "n_test": 1234}],
   "winner": {"method": "M1", "lam": 20}, "beats_raw": true, "beats_global": true}}
```
Melissa lê `winner` por ponte; ninguém edita λ à mão. Regra do CP3: `beats_raw` e `beats_global` verdadeiros.

### 4. Entregas
| Quando | O quê | De → para |
|---|---|---|
| Sáb 15:00 | Este contrato no `main` | Melissa → Samuel |
| Sáb 15:00–19:00 | M1 Pantanal (§3.2) · Samuel monta `validate/run.py` com Identity e GlobalFactor | — |
| Sáb 22:00 | M1 + M2 do Pantanal | Melissa → Samuel |
| Sáb 22:00–23:30 | `validation.json` Pantanal; λ vencedor (CP3) | Samuel → Melissa |
| Sáb 23:30 → noite | C4 (bootstrap) com o vencedor | Melissa |
| Dom 07:30–10:00 | `harm_series.parquet` Brasil · Pettitt raw × harm | Melissa → Murilo · Samuel |

### 5. Pendente de aprovação do Capitão
| ID | Ponto |
|---|---|
| D30 | Ajuste Aqua→S-NPP 2012–2019 e teste 2020–2021 (o Guia v2 §3.1 ainda traz 2012–2021) |
| D31 | Meses tocados pela pane do Aqua (202008, 202009) saem inteiros; `transform` recebe `months`; λ vem de `validation.json` |

### 6. D33 (sem bioma, 2000–2025)
| Item | Como fica |
|---|---|
| `Context` | sem `cell_biome` (removido no YAML v3); o M1 usa direto k_global(M) e a_global(M) |
| Estratos do limiar (M2) | trimestre × dia/noite, Brasil inteiro (8 estratos) |
| `validation.json` | sem `by_biome`; acrescentar `by_season` (opcional) |
| Nova saída Samuel | `consistency_4sat.json`: para cada par de sensores na sobreposição, razão harmonizado/harmonizado por ano (esperado ≈ 1) |

### 7. Ferramentas da 3.2 (sáb 22:22)
| Ferramenta | Uso |
|---|---|
| `python -m pipeline.bridges.m1 --eval [--fast] [--hier] --agg <agg>` | Conferência bruto × taxa única × M1 (teste 2020–21 e LOYO); `total_ratio` = Σpred/ΣB em todas as célula-mês (`sum_ratio` só nas ativas). Nota oficial = `validation.json` |
| `python -m pipeline.bridges.harmonize --lam 20 --agg <agg> --out <saída>` | Série harmonizada provisória (linha do tempo do YAML); consome o mesmo `Bridge` |
| `pipeline/bridges/m1_hier.py` | M1 hierárquico (total do pai res 4); testado na res 5 e não adotado (D37) |
| `check_method.py`, `check_extra.py`, `m1_preview.py` | Conferência 5,42 → 3,45 → 1,0 e ΣFRP; fogos extras do VIIRS; série dos 4 satélites (D34) |

### 8. Ferramentas da 3.3 (dom 04:21)
| Ferramenta | Uso |
|---|---|
| `python -m pipeline.bridges.m2 --bridge aqua_snpp --lam 20` | τ por trimestre × dia/noite (`m2_tau_aqua_snpp.csv`), parâmetros (`m2_params_*.parquet`), conservação passagens × agg |
| `python -m pipeline.bridges.m2 --bridge aqua_snpp --eval` | Bruto × taxa única × M1 × M2 em célula-mês ativas + `total_ratio`; independente das funções internas do `m1.py` |
| `M2(lam, ctx, bridge="aqua_snpp")` | Precisa de `ctx.passes = base.passes_reader(cfg)`; passagens na mesma resolução do `agg_monthly` (res 4) |


## Anexo H — Uso de IA (`docs/AI_USAGE.md`)

Exigência do Space Apps: declarar onde e como a IA foi usada; imagem/vídeo gerado por IA com marca d'água visível; código e dados gerados por IA reconhecidos no texto e nos metadados; nenhuma marca NASA gerada ou alterada por IA.

| Data | Ferramenta | Onde | Para quê | Revisado por |
|---|---|---|---|---|
| 13/11 | Claude (Anthropic) | Planejamento | Pesquisa de vencedores anteriores, plano de ação, estratégia | Murilo |
| 13/11 | Claude (Anthropic) | Dados | Checagem de cobertura temporal do FIRMS; identificação do fim do S-NPP | Murilo |
| 13/11 | Claude (Anthropic) | Repositório | Estrutura inicial, script `pipeline/extrair_paises.py` | Murilo |
| 13/11 | Claude (Anthropic) | Método | Análise exploratória 2025 (razões entre sensores, decomposição do degrau), proposta de métodos e testes | Murilo |
| 13/11 | Claude (Anthropic) | Governança | Rascunho dos documentos de governança | Murilo |
| 13/11 | Claude (Anthropic) | Repositório | Organização de pastas, ajuste da governança à equipe de 4 (D16), roadmap a partir do Guia 48h | Murilo |
| 13/11 | Claude (Anthropic) | Governança | Processo de mudança de rota e banco de perguntas para mentores (`MENTORS.md`); unificação dos documentos repo × Projeto | Murilo |
| 14/11 | Claude (Anthropic) | Governança | Avaliação das Global Offers (`RESOURCES.md`, D17) | Murilo |
| 14/11 | Claude (Anthropic) | Estratégia | Comparação com o vencedor Twisters (2025) e revisão do PDF da equipe | Murilo |
| 14/11 | Claude (Anthropic) | Governança | Cronograma v2 (`PLANO-48H.md`), guia técnico com esqueletos de código (`GUIA-TECNICO.md`), propostas D18–D26, PDF v2 | Murilo |
| 14/11 | Claude (Anthropic) | Dados 2.1 | Rascunho de `pipeline/ingest.py`, `pipeline/clean.py` e `tests/test_clean.py`; leitura dos resultados (conferência 2025, piloto Pantanal, deriva MODIS); resumo `DADOS-2.1-INGEST-CLEAN.md`. Código rodado e conferido por Murilo nos dados reais | Murilo |
| 14/11 | Claude (Anthropic) | Ciência 3.1 | Rascunho de `config/sensors.yaml`, `pipeline/bridges/base.py`, `tests/test_bridge_contract.py` e `docs/CONTRATO-CIENCIA.md`; proposta D31 | Murilo |
| 14/11 | Claude (Anthropic) | Governança | D33 (sem bioma, 2000–2025 com 4 sensores): atualização de YAML, contratos, método, guia, plano e PDF v2.4 | Murilo |
| 14/11 | Claude (Anthropic) | Método/Governança | Desenho da análise preditiva D35 (`PREVISAO.md`: entrada lat/lon, modelo, features, hindcast, portão) e governança v2.8 | Murilo |
| 14/11 | Claude (Anthropic) | Ciência 3.1 | Fechamento do contrato: remoção do bioma (D33), `winner()`, `passes_reader()`, `check_config()` e novos testes | Murilo |
| 14/11 | Claude (Anthropic) | Ciência 3.2 | Rascunho de `bridges/m1.py` (M1, `--eval`, `--fast`, `total_ratio`), `check_method.py`, `m1_preview.py`, `check_extra.py`, `harmonize.py`, `m1_hier.py` e testes; leitura dos resultados (Brasil, res 4/5/6); D34, D36 (revista) e D37 propostas; revisão de R05/D30 | Murilo |
| 14/11 | Claude (Anthropic) | Dados 2.2/2.3 | Rascunho de `pipeline/grid.py` (`--res`) e `tests/test_grid.py`; leitura dos resultados Brasil 2000–2025 | Murilo |
| 14/11 | Claude (Anthropic) | Governança | Pacote v2.6 e governança consolidada v2.9 (unificação da 3.2 com D35/D36) | Murilo |
| 14/11 | Claude (Anthropic) | Governança | v2.10: fechamento da Dados 2.3 (caminho crítico, cronograma, R14, pendências) | Murilo |
| 14/11 | Claude (Anthropic) | Dados 2.4 | Rascunho de `pipeline/export.py` e `tests/test_export.py` (tiles res 2, validação do contrato, conservação); registro D38 | Murilo |
| 15/11 | Claude (Anthropic) | Dados | Rascunho dos exports (`export_csv`, `export_points`, `export_frp_monthly`, `export_frp_csv`) e da validação (`audit_daily`, `spot_check`) | Murilo |
| 15/11 | Claude (Anthropic) | Ciência/Dados | D40 `frp_harmonize.py` (ΣFRP harmonizado via M1) e D42 (`--brazil`, base de treino com contorno IBGE); propostas D39–D42 | Murilo |
| 15/11 | Claude (Anthropic) | Governança | v2.11: fechamento da Dados 2.4, D38–D42, R06/R22/R23, contrato §11–§12 | Murilo |
| 15/11 | Claude (Anthropic) | Dados | `pipeline/daily_harm.py` (diário harmonizado, D43/D45) e explicação do termo aditivo; governança v2.12–v2.13 (D43–D45, R24, contrato §13) | Murilo |
| 15/11 | Claude (Anthropic) | Ciência 3.3 | Rascunho de `pipeline/bridges/m2.py` (limiar de FRP, M2, `--eval`), `tests/test_m2.py` e `docs/CIENCIA-3.3-M2.md`; prova M2 = M1 em λ = 0 e λ → ∞; correção do `--eval` (só célula-mês ativas); governança v2.14 | Murilo |
| 15/11 | Claude (Anthropic) | Front 4.1 / D46 | Port do front do Samuel para `app/` estático: i18n EN/PT, mapa com período e hexágonos, calendário (Plot), leitor de tiles + 11 testes, `pages.yml`; correção do import do Leaflet; teste em navegador com bibliotecas e tiles reais; resumo `docs/FRONT-SISTEMA-WEB.md`; governança v2.15 | Murilo |
<!-- Se alguém usar GitHub Copilot ou outra IA, adicionar uma linha aqui. -->

### Texto para o formulário (rascunho)
We used Claude (Anthropic) as a pair-programmer and reviewer: planning, exploratory analysis of FIRMS data, drafting code that every team member ran and reviewed on real data, and drafting documentation. All scientific decisions were made and validated by the team. No AI-generated images, video or audio were used [update if this changes]. No NASA branding was generated or modified by AI.

## Anexo I — Ciência 3.2 concluída (`docs/CIENCIA-3.2-M1.md`, resumo · sáb 22:22)
| Item | Resultado |
|---|---|
| Conferência do método (Brasil 2025) | 5,42 → 3,58 (0,01°) → 3,45 (0,02°) → 1,00 com τ = 9,4 MW ✅ (`check_method`) |
| Grade + H3 | Brasil 2000–2025: ingest ~1 min, grade 19 s (res 4) · 21 s (res 5) · 32 s (res 6); conservação OK |
| M1 res 4 (teste 2020–21 / LOYO) | consistency 0,448 / 0,418 × taxa única 0,693 × bruto 1,099; R² 0,64; total 0,99; λ 5 ≈ 20 |
| Resoluções (teste 2020–21) | res 4: 0,448 · R² 0,64 · res 5: 0,522 · R² 0,273 · total 1,034 · res 6: 0,575 · R² −0,43 (descartada) |
| Res 5: M1 × hierárquico | M1 0,522 / 0,273 / viés −0,25 / total 1,034 × hierárquico 0,556 / 0,217 / −0,34 / 1,007 → M1 direto (D37 não adotada) |
| 4 satélites (res 4) | Aqua→S-NPP ±4% (2012–23) · N20→S-NPP ±3% · Aqua 2024–25 +15–23% · Terra pós-2011 +15–60% (D34) |
| Fogos extras do VIIRS (mês) | 35% ≤ 2 km · 30% 2–10 km · 26% 10–50 km · 9% > 50 km (1,6 MW, 77% noite) |
| ΣFRP | 1,17 (todos os pixels) · 0,76 (Σ máx.); CV entre meses 16% × 12% da contagem → contagem segue unidade (D03, D29) |
| Séries provisórias | res 4 Brasil (4.679 células) · **res 5 Brasil (28.773 células × 302 meses = 8,69 M linhas)** · res 4 Pantanal (201) |
| Emenda 2011→2012 (res 5) | harmonizado 570.750 → 720.804 (1,26×) × bruto 133.485 → 710.188 (5,3×) · fogo real Aqua×Aqua 1,37× |
| Limitação | Nov–dez/2000 (Terra) inflado pelo termo aditivo (12× o bruto) — `low_conf`, fora da previsão (começa em 2003) |
| Código (PR `ciencia/m1`) | `grid.py`, `bridges/{m1,m1_hier,harmonize,check_method,check_extra,m1_preview}.py`; testes `test_m1`, `test_m1_hier`, `test_harmonize`, `test_grid`, contrato — 32+ passando |
| Próximo | P1 features (Murilo, série res 5) · 3.3 M2 (Melissa, res 4) · `validation.json` (Samuel, CP3 23:30) |

## Anexo J — Dados 2.3 concluída (`docs/DADOS-2.2-2.3-GRADE-H3.md`, resumo · sáb 22:35)
| Item | Resultado |
|---|---|
| Escopo (D28, D33) | Brasil inteiro · nov/2000–dez/2025 · Terra, Aqua, S-NPP, NOAA-20 |
| Comandos | `python -m pipeline.ingest --area brasil` (48 arquivos, ~40 M linhas, ~1 min) · `python -m pipeline.grid --area brasil [--res 5]` |
| Tempo | Grade res 4: 19 s · res 5: 21 s · res 6: 32 s (descartada, D36) |
| Conferência | Brasil 2025 = `08-fatos` (0,00% nos 4 sensores) · conservação Σ `n_pix` = focos limpos e Σ `n` = linhas da grade, por sensor × ano ✅ |
| Filtros removem | Terra 7,6% · Aqua 5,4% · S-NPP 10,0% · N20 10,3% |
| Focos limpos → células-passagem | Terra 3,52 M → 2,81 M · Aqua 5,84 M → 4,60 M · S-NPP 17,30 M → 8,55 M · N20 9,71 M → 4,80 M |
| Células H3 | res 4: ~3.700–4.200 com fogo por ano (4.679 na série) · res 5: 28.773 na série |
| S-NPP/Aqua na grade | 2012–19 3,96 · 2020–21 3,98 · 2022–25 3,58 · 2025 3,45 (= `check_method`) |
| Saídas (fora do Git) | `data/interim/{grid2km_pass,agg_monthly}.parquet` (res 4) · `data/interim/res5/agg_monthly.parquet` · `grid_log.csv` |
| Código | `pipeline/ingest.py`, `pipeline/clean.py`, `pipeline/grid.py` (`--res`), `tests/test_clean.py`, `tests/test_grid.py` (PR `ciencia/m1`) |
| Plano B (R14) | Não acionado |
| Pendente | Makefile `AREA`/`RES` · merge do PR `ciencia/m1` · `agg_monthly` para Samuel/Melissa |
| Próximo (Dados) | 2.4 export provisório → Luana · P1 features (série res 5) |

## Anexo K — Dados 2.4 concluída + FRP (D38–D42) (resumo · dom 15/11 02:00)
| Item | Resultado |
|---|---|
| 2.4 export | `pipeline/export.py` (tiles res 2 / arquivo único) + `tests/test_export.py` 7/7 · commits `df9f89a` (código), `47a497b` (docs) na branch `dados/export` |
| Entrada | `data/processed/res5/harm_series.parquet` (M1 λ 20, provisória, `lo = hi`) |
| Saída | 28.769 células (4 sem fogo omitidas) × 302 meses · arquivo único seria 100,5 MB → **128 tiles**, mediana 0,94 MB, máx 1,35 MB, total 101 MB |
| Conservação | `raw` idêntica · `cells/lo/hi` −0,09% (arredondamento × 10 de célula-mês < 0,05) |
| Entrega | `harm_tiles_res5_M1prov.zip` no Drive (pasta Nasa Space Challenge) → Luana · tiles fora do Git (D38) |
| Falta (2.4b) | Reexport com vencedor (CP3) e incerteza (CP4) · commit único dos tiles antes do CP7 |
| FRP mensal | `frp_monthly.parquet` 8.689.446 linhas; ΣFRP por satélite = agg (Terra 136,3 M · Aqua 354,7 M · S-NPP 194,7 M · N20 110,4 M MW) |
| Auditoria | Diário (11.334.791 linhas) × mensal: **0 divergências** nos 4 satélites · `spot_check` 5/5 e sanidade 7/7 |
| D40 ΣFRP harmonizado | s = 22,8 MW · teste 2020–21: M1 0,337 × bruto 0,388 × taxa única 0,394 · `frp_harm_nonzero.csv` 3.979.974 linhas (2.913.080 só termo aditivo, R22) |
| D42 base de treino | `frp_harm_brasil.csv.gz` · 31.946 hexágonos × 302 = 9.647.692 linhas · 5.667.718 zeros · Σ FRP 473.146.056 MW |
| Código | `pipeline/{export,export_csv,export_points,export_frp_monthly,export_frp_csv,audit_daily,spot_check,frp_harmonize}.py` (branches `dados/export`, `dados/frp-d40`) |
| Diário (D43/D45) | `fogo_diario_harm.csv` 5.869.988 dias, 0 vazios, 28.053 hexágonos · aditivo 2.034.079 hexágono-mês (Σ focos 1.593.040; ΣFRP 20,7 M MW) · diário = 91,4% dos focos e 95,6% do ΣFRP |
| Próximo (Dados) | 2.4b reexport mensal · **2.4c export diário** (`harm_daily_<pai>.json`) · P1 features (série res 5 + D42) · PRs |

## Anexo L — Ciência 3.3 concluída (`docs/CIENCIA-3.3-M2.md`, resumo · dom 15/11 04:21)
| Estrato | Aqua | S-NPP | Razão | τ (MW) |
|---|---|---|---|---|
| DJF D / N | 99.477 / 10.834 | 396.675 / 111.647 | 3,99 / 10,31 | 11,76 / 4,46 |
| MAM D / N | 50.634 / 6.009 | 161.961 / 62.598 | 3,20 / 10,42 | 8,65 / 5,03 |
| JJA D / N | 343.383 / 32.975 | 975.530 / 371.447 | 2,84 / 11,26 | 10,42 / 5,27 |
| SON D / N | 614.958 / 73.773 | 2.030.632 / 766.382 | 3,30 / 10,39 | 13,15 / 4,96 |

| Item | Resultado |
|---|---|
| Ajuste | Brasil res 4, Aqua→S-NPP 2012–2019 (D30), 8 estratos (D33); razão após τ = 1,00 em todos |
| Conservação passagens × agg | 0,0000% ✅ |
| Σpred/ΣB (λ 20) | ajuste 1,002 · teste 2020–21 1,006 |
| kf_global(M) | 0,92–1,06 em ago–dez; 0,69–0,88 nos meses chuvosos (fortes em célula-mês com A = 0 vão ao termo aditivo, D32) |
| τ 2012–19 × prévia 2025 | SON dia 13,2 × 10,7 MW: em 2025 o Aqua vê mais (deriva, R05) → reforça D30 |
| Conferência (teste 2020–21 / LOYO, ativas, n 59.148 / 257.826) | bruto 1,099 · taxa única 0,693 · M1 λ5 0,447 / 0,419 · M1 λ20 0,448 / 0,418 · M2 λ5 0,447 / 0,419 · M2 λ20 0,449 / 0,418 · M2 λ0 0,463 / 0,437 |
| Conclusão | M2 = M1 (identidade k_f·(1+r) = k) → empate técnico → **série segue com M1**; nenhuma decisão nova. M2 no Method como explicação física |
| Correção | 1ª rodada do `--eval` pontuou célula-mês com A = 0 e B = 0 (n 100.518) e favoreceu a taxa única; corrigido (`test_eval_scores_only_active_cell_months`) |
| Código | `pipeline/bridges/m2.py`, `tests/test_m2.py` (14 + contrato, 37 passando) · branch `ciencia/m2` (commit pela Melissa) |
| Próximo | `validation.json` com M1 e M2 (Samuel) · 3.4 bootstrap com M1 (Melissa) · τ no Method (Luana/Ciência) |

## Anexo M — Front 4.1 concluída (`docs/FRONT-SISTEMA-WEB.md`, resumo · dom 15/11 06:00)
| Item | Resultado |
|---|---|
| Decisão | D46: visual do Samuel, estático (sem Flask), EN/PT, período De/Até |
| Páginas | `index.html` (landing) · `mapa.html` (mapa + painel + calendário) |
| Mapa | Busca de cidade (Nominatim, só Brasil) · lat/lon · clique → hexágono res 5 · harmonizado × bruto · hexágonos do período (zoom ≥ 7, até 12 tiles, escala até o p98) |
| Painel | Região/célula · período · detecções harmonizadas e brutas · mês com mais fogo + satélite · meses de baixa confiança · calendário ano × mês (cividis, ○ baixa confiança, < 0,5 = cinza) |
| Abas | Timeline (4.4) e Outlook (após CP5) com mensagem de próxima etapa |
| Testes | 11/11 (`npm test`) · 128 tiles reais validados · navegador com Leaflet/h3/Plot reais: Pantanal (-18,5 / -57) 528 harm × 304 brutas, pico set/2004 (Aqua), 0 erro no console · celular 375 px ok |
| Correções na revisão | Leaflet 1.9 sem `export default` → `import * as L` · paleta verde→vermelho → cividis · ano até 2026 → até 2025 · `mapa_cores.js` inexistente removido · textos de precisão e de previsão ajustados |
| Arquivos | `app/{index,mapa}.html` · `app/src/{main,mapa,data,calendar,i18n}.js` · `app/src/{style,mapa}.css` · `app/test/data.test.js` · `app/vite.config.js` · `.github/workflows/pages.yml` · `docs/FRONT-SISTEMA-WEB.md` |
| Falta para fechar | `npm run build` · commit `front/setup` + PR com revisão · Pages ligado (R25) |
| Próximo (Luana) | Desenho de área · score D25 + chance D27 + pico típico · CSV · Timeline · Method · Outlook (após CP5) · calendário diário (após 2.4c) |

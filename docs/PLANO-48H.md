# Plano 48 h v2 — Fire Almanac (replanejado sáb 14/11 13:30)

> **Andamento (sáb 19:31):** Dados 2.1–2.3 (inclusive Brasil inteiro) e Ciência 3.1–3.2 (M1) concluídos — CP2 adiantado. Próximos passos de cada um: `docs/BRIEFING-PROXIMOS-PASSOS.md`. Decisões novas: D34 (decidida 18:07).

Substitui o cronograma do Guia v1 (`docs/guia-execucao-48h-v1.pdf`), que previa início sáb 08:00. Decisões novas: **D20–D33** (D21, D27, D28, D33 decididas) em `DECISIONS.md`.

## 0. Resumo em 5 linhas
| Item | Valor |
|---|---|
| Janela | Sáb 14/11 00:00 → dom 15/11 23:59 (prazo oficial) |
| Já usado | Sáb 00:00–13:30: Fase 0 + estratégia (persona, Twisters, PDF da equipe) |
| Construção | Sáb 14:00 fundação · **sáb 19:45 começa o app** · dom 15:00 congela · **dom 21:00 envio interno** (D23) |
| Pergunta do produto | *"Is fire in my area unusual right now, and when does it usually peak?"* (D20) |
| Regra de ouro | Histórico harmonizado + probabilidade histórica. **Sem previsão** (D21) |

## 1. Equipe
| Frente | Pessoa | Entrega final | Pastas | Branch |
|---|---|---|---|---|
| Capitão + Dados | **Murilo** | Focos limpos 2000–2025, grade 2 km, H3, export JSON, `sensors4.json`, áreas prontas, texto da submissão, envio | `pipeline/` (ingest, clean, grid, export, nrt), `app/public/data/`, `open/` | `dados/<tema>` |
| Ciência — dupla | **Melissa** (harmonização) | `sensors.yaml`, `Bridge`, limiar FRP, M2, incerteza, ponte N20→S-NPP | `config/`, `pipeline/bridges/` | `ciencia/<tema>` |
| Ciência — dupla | **Samuel** (validação) | Métrica, validação fora da amostra, testes de homogeneidade, score e pico (analytics) | `pipeline/validate/`, `pipeline/analytics/` | `ciencia/<tema>` |
| Front + Demo | **Luana** | App no ar, calendário, toggle, score, incerteza, CSV, Method, edição do vídeo, prints | `app/` | `front/<tema>` |

Dupla Ciência: trabalham **lado a lado**, em módulos separados (R12). Ponto de contato = interface `Bridge` (Melissa escreve, Samuel consome). Revisam o PR um do outro.

## 2. Cronograma das 48 h
Legenda: CP = checkpoint (15 min, cada um mostra o que **roda**).

### Sábado 14/11
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
| 19:45–23:30 | Pipeline **Brasil inteiro** rodando em 2º plano · export real do Pantanal (bruto + M1) | Limiar FRP por trimestre × dia/noite (D33) · **M2** | Rodar bruto × M1 × M2 por ponte → `validation.json` | **Início do app**: mapa + desenho + lat/lon → H3 → calendário (dados falsos) |
| **23:30** | **CP3 Núcleo científico**: M2 > bruto na métrica · JSON real do Pantanal no app | | | |
| 23:30–02:00 | Export do método vencedor (Pantanal) · conferir pipeline BR | Disparar **bootstrap C4** (roda à noite) | Pettitt + sazonalidade (raw × harm) → `pettitt.json` v0 | Toggle bruto × harmonizado · série com emendas |

### Turnos de sono (≥ 5 h, R10)
| Pessoa | Dorme | Máquina rodando |
|---|---|---|
| Luana | 01:30–07:00 | — |
| Samuel | 02:00–07:00 | — |
| Melissa | 02:00–07:00 | Bootstrap C4 (200×) |
| Murilo | 02:30–07:30 | Pipeline Brasil inteiro |

### Domingo 15/11
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

## 3. Checkpoints
| # | Quando | Critério para seguir | Se falhar |
|---|---|---|---|
| CP0 | Sáb 13:30 | D20–D26 decididas; todos com ambiente | Capitão decide sozinho às 14:00 |
| CP1 | Sáb 15:00 | Contrato congelado; JSON falso com a Luana | Luana segue com o falso (R07) |
| CP2 | Sáb 19:00 | Pantanal agregado · M1 no validador · site publicado | Cortar Terra e N20 do piloto |
| CP3 | Sáb 23:30 | M2 (ou M1) melhor que bruto · Pantanal real no app | Ficar com M1 e declarar limitação (R03) |
| CP4 | Dom 07:30 | Série Brasil com incerteza | App só com áreas prontas (R14) |
| CP5 | Dom 10:00 | Corte final de escopo | Item sai |
| CP6 | Dom 12:00 | Autoavaliação 1–5 | Horas no critério mais fraco |
| CP7 | Dom 15:00 | Congelamento | — |
| CP8 | Dom 21:00 | `SUBMISSION_CHECKLIST.md` 100% | Prazo 23:59 |

## 4. Escopo (D24)
| Faixa | Itens |
|---|---|
| Núcleo | Harmonização M2 (grade 2 km + limiar FRP + resíduo) · validação vs bruto · incerteza C4 · Pettitt + sazonalidade · mapa/seleção · calendário · toggle · Fire Anomaly Score · probabilidade de pico · chance acima do normal (D27) · CSV · Method · 2 áreas prontas |
| Se der tempo (ordem) | KS no FRP · pegada espacial · AI1 (ML) · P2 boletim · V1 INPE |
| Futuro (pós-evento) | Mundo inteiro: mesmo pipeline com outro país/bbox do FIRMS; pontes recalibradas por região; 2026 + NRT com NOAA-20/21 (D28, D33) |
| Fora | Previsão de focos · índice agricultores (D19) · globo 3D · chatbot |

## 5. Passagens de bastão
| Quando | Arquivo | De → Para |
|---|---|---|
| Sáb 15:00 | `harm_monthly.json` falso | Murilo → Luana |
| Sáb 17:00 | `data/clean/` Pantanal | Murilo → Ciência |
| Sáb 19:00 | `grid2km_pass.parquet` + `agg_monthly.parquet` (Pantanal, 2000–2025) | Murilo → Melissa, Samuel |
| Sáb 22:00 | M1 e M2 do Pantanal | Melissa → Samuel |
| Sáb 23:30 | `harm_series.parquet` (Pantanal, vencedor) | Ciência → Murilo |
| Sáb 23:45 | `harm_monthly.json` real Pantanal | Murilo → Luana |
| Dom 07:30 | Série Brasil com `lo/hi/low_conf` | Melissa → Murilo → Luana |
| Dom 10:00 | `validation.json`, `pettitt.json`, `season.json` | Ciência → Murilo → Luana |
| Dom 12:00 | Números e textos do método | Ciência → Luana, Murilo |

Quem entrega avisa no grupo; quem recebe confirma que leu. Só o Murilo escreve em `app/public/data/`.

## 6. O que mudou em relação ao PDF da equipe (Document 5)
| PDF da equipe | Agora | Decisão |
|---|---|---|
| "Previsões de futuras queimadas" / IA preditiva | "Chance histórica de este mês ficar acima do normal" + pico típico + score | D21, D27 |
| Persona "entidades governamentais" | Coordenador(a) de brigada/Defesa Civil protegendo produtores rurais | D20 |
| Agro (pecuária, cana SP) | Áreas prontas Pantanal + SP canavieira; frase de impacto com fonte | D22 |
| "IA preditiva – Murilo e Luana" | Murilo Dados, Luana Front (D16) | D16 |
| "Harmonização – TODOS" | Melissa harmoniza, Samuel valida | D16 |
| "Análise ao longo do mundo" | Brasil inteiro agora; pipeline parametrizado por país para escalar ao mundo | D28 |
| "Baixar Analytics (gráficos?)" | CSV do calendário + PNG do calendário | D24 |

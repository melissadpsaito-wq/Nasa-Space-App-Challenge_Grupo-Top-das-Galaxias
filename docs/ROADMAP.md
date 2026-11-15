# Roadmap — 48 h (v2, replanejado sáb 14/11 13:30 · D23)

Fonte: `docs/PLANO-48H.md` (cronograma) e `docs/GUIA-TECNICO.md` (como fazer). Versão anterior: `docs/guia-execucao-48h-v1.pdf`.
Legenda: [ ] a fazer · [x] feito. Marcar no próprio arquivo via commit.

## Fase 0 · até sáb 13:30
| Tarefa | Dono | Feito |
|---|---|---|
| Inscrição, equipe, Local Lead, papéis e canal | Todos | [x] |
| MAP_KEY FIRMS + Earthdata · MODIS 2000–2025 · S-NPP e NOAA-20 2025 (Brasil) | Murilo | [x] |
| Repo organizado (estrutura de pastas + governança) | Murilo | [x] |
| Estratégia: persona, padrão Twisters, revisão do PDF da equipe | Murilo + equipe | [x] |
| Chave FIRMS nova (incidente `541c557`) no `.env` de cada um e nos Secrets | Murilo / Melissa | [ ] |
| S-NPP 2012–2024 e NOAA-20 2018–2024, Brasil inteiro (D28) | Murilo | [x] |
| ~~Dados 2026~~ e ~~RESOLVE~~ — fora por D33 | — | — |

## Checkpoints (D23)
| # | Quando | Critério | Se falhar |
|---|---|---|---|
| CP0 | Sáb 13:30 | D20–D26 decididas; CODEOWNERS; ambiente de todos | Capitão decide às 14:00 |
| CP1 | Sáb 15:00 | Contrato congelado; JSON falso com a Luana | Front segue com falsos |
| CP2 | Sáb 19:00 | Pantanal agregado · M1 no validador · site publicado | Cortar Terra e N20 do piloto |
| CP3 | Sáb 23:30 | Vencedor > bruto · Pantanal real no app | Ficar com M1 |
| CP4 | Dom 07:30 | Série Brasil com `lo/hi/low_conf` | Só áreas prontas (R14) |
| CP5 | Dom 10:00 | Corte final de escopo | Item sai |
| CP6 | Dom 12:00 | Autoavaliação 1–5 | Horas no critério mais fraco |
| CP7 | Dom 15:00 | Congelamento: só `fix/<tema>` | — |
| CP8 | Dom 21:00 | `SUBMISSION_CHECKLIST.md` 100% | Prazo oficial 23:59 |

## Murilo · Capitão + Dados (`pipeline/`, `data/`, branch `dados/<tema>`)
- [ ] Sáb 13:30 · Conduzir CP0; registrar decisões
- [ ] Sáb 14–15 · Contrato final + `harm_monthly.json` falso → Luana (CP1)
- [x] Sáb 15–17 · Download faltante + ingest + clean Pantanal + `filter_log.csv` → Ciência 17:00
- [x] Sáb 17–19 · Grade 0,02° por passagem + H3 res 4 (Pantanal 2000–2025, 4 sensores); teste de conservação → Ciência 19:00
- [x] Sáb 19:45 → madrugada · Pipeline Brasil inteiro em 2º plano (feito às 17:53: ingest ~1 min + grade 19 s)
- [ ] Sáb 23:30–02:00 · Export real do Pantanal (método vencedor) → Luana
- [ ] Dom 07:30–10:00 · Export final; tamanho (R06/tiles); `areas.json` (Pantanal, SP cana)
- [ ] Dom 10–12 · `sensors4.json` (D33); `meta.json`; frase de impacto com fonte
- [ ] Dom 12:30–15 · Texto da submissão (EN) + README
- [ ] Dom 15–19 · Página do projeto (formato Twisters), `open/`, `AI_USAGE.md`
- [ ] Dom 19–21 · Checklist com Luana; envio 21:00

## Melissa · Harmonização (`config/`, `pipeline/bridges/`, branch `ciencia/<tema>`)
- [x] Sáb 15–19 · `sensors.yaml`, interface `Bridge`, reproduzir 5,42 → 3,45 → ≈1,0; M1 (PR `ciencia/m1`)
- [ ] Sáb 17:00 · Mentor (método) com Samuel
- [ ] Sáb 19:45–23:30 · Limiar FRP por trimestre × dia/noite (D26, D33); M2; M1 e M2 → Samuel 22:00
- [ ] Sáb 23:30 · Disparar bootstrap C4 (200×) antes de dormir; `low_conf`; Terra 2000–2002
- [ ] Dom 07:30–10 · Harmonizar Terra, Aqua, S-NPP e N20 em todos os anos 2000–2025 (D33); deriva (R05)
- [ ] Dom 10–12 · `METHOD.md` final; registrar λ e τ em `DECISIONS.md`

## Samuel · Validação (`pipeline/validate/`, `pipeline/analytics/`, branch `ciencia/<tema>`)
- [ ] Sáb 15–19 · Métrica, leave-one-year-out, baselines (bruto, fator global); testar com M1
- [ ] Sáb 19:45–23:30 · Bruto × M1 × M2 por ponte → `validation.json`
- [ ] Dom 07:30–10 · `consistency_4sat.json` (razão entre sensores harmonizados, D33)
- [ ] Sáb 23:30–02:00 · Pettitt + sazonalidade (bruto × harm) → `pettitt.json` v0
- [ ] Dom 07:30–10 · Score + probabilidade de pico (D25) + chance acima do normal (D27): referência Python + `tests/score_cases.json`
- [ ] Dom 10–12 · Números finais do Method; parágrafo "how it works" (EN) → Murilo
- [ ] Dom 15–19 · `make all` do zero em máquina limpa

## Luana · Front + Demo (`app/`, branch `front/<tema>`)
- [ ] Sáb 14–15 · Revisar contrato; wireframe das 4 telas
- [ ] Sáb 15–19 · Vite + Leaflet; deploy "hello world" no Pages; leitor do JSON falso
- [ ] Sáb 19:45–23:30 · **Início do app**: mapa + desenho + lat/lon → H3 → calendário cividis
- [ ] Sáb 23:30–01:30 · Toggle bruto × harm; série com emendas
- [ ] Dom 07:30–10 · Score, card de chance (D27), card de pico, faixa de incerteza, CSV, áreas prontas
- [ ] Dom 10–12 · Página Method, gráfico 4 satélites, celular, acessibilidade; mentor do pitch 11:00
- [ ] Dom 12:30–15 · Polimento; roteiro do vídeo com Murilo
- [ ] Dom 15–19 · Gravar e editar vídeo ≤ 30 s com legenda EN; prints

## Se der tempo (ordem, D24)
KS no FRP · pegada espacial · AI1 (ML) · P2 boletim · V1 INPE. Fora: previsão, índice de agricultores, globo 3D, chatbot.

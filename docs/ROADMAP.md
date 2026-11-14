# Roadmap — 48 h

Fonte: Guia de Execução 48h (`docs/guia-execucao-48h.pdf`). Legenda: [ ] a fazer · [x] feito. Marcar no próprio arquivo via commit.

## Fase 0 · Sexta 13/11 (preparação)
| Tarefa | Dono | Feito |
|---|---|---|
| Inscrição, equipe, Local Lead, papéis e canal | Todos | [x] |
| MAP_KEY FIRMS + Earthdata · MODIS 2000–2025 · S-NPP e NOAA-20 2025 (Brasil) | Murilo | [x] |
| Repo organizado (estrutura de pastas + governança) | Murilo | [x] |
| `.env` local a partir de `.env.example` | Todos | [ ] |
| S-NPP 2012–2024 (`viirs-snpp`) e NOAA-20 2018–2024 (`viirs-jpss1`), Brasil + vizinhos (D09) | Murilo | [ ] |
| Dados 2026 (Archive Download ou API); senão plano B R01 às 10:00 | Murilo | [ ] |
| Shapefile RESOLVE Ecoregions 2017 | Murilo | [ ] |
| Tudo em `data/raw/` no Drive + tabela de fontes em `DATA_GOVERNANCE.md` | Murilo | [ ] |
| `FIRMS_MAP_KEY` nos GitHub Secrets | Murilo / Melissa (dona do repo) | [ ] |
| C0: ler `METHOD.md` + guia MODIS C6; ambiente Python; reproduzir 5,42 → 3,45 → ≈ 1,0 | Melissa, Samuel | [ ] |
| F0: app Vite em `app/`, deploy "hello world", testado em anônimo e celular | Luana | [ ] |

## Checkpoints
| # | Quando | Checkpoint | Critério | Se falhar |
|---|---|---|---|---|
| 1 | Sáb 10:00 | Contrato de dados | `DATA_DICTIONARY.md` aprovado; JSON falso no app | Front segue com falsos |
| 2 | Sáb 14:00 | Fundação | Pantanal agregado · M1 + validador · mapa publicado | Cortar Terra e NOAA-20 |
| 3 | Sáb 22:00 | Núcleo científico | Harmonização > bruto na métrica · JSON real Pantanal no app | Ficar com M1 |
| 4 | Dom 10:00 | Corte do ML | AI1 validado | AI1 sai do núcleo |
| 5 | Dom 12:00 | Autoavaliação | Nota 1–5 por critério | Horas no critério mais fraco |
| 6 | Dom 13:00 | Congelamento | Só `fix/<tema>` | — |
| 7 | Dom 20:00 | Envio | `SUBMISSION_CHECKLIST.md` 100% | Prazo oficial 23:59 |

## Dados · Murilo (`pipeline/`, `data/`, branch `dados/<tema>`)
- [ ] D1 · Sáb 08–10 · Contrato fixado; propor os 3 arquivos do §5; `harm_monthly.json` falso → Luana
- [ ] D2 · Sáb 08–12 · ingest + clean → `data/clean/<sensor>/<ano>.parquet` + log de filtros
- [ ] D3 · Sáb 10–14 · Grade 0,02° por passagem + H3 res 4 + célula → bioma (Pantanal); teste de conservação
- [ ] D4 · Sáb 14–24 · Brasil + vizinhos; entregar à Ciência ~20:00
- [ ] D5 · Sáb 22 → dom 12 · Export `harm_monthly.json`, `meta.json`; checar < 5 MB (R06)
- [ ] D6 · Dom 08–12 · GitHub Action NRT → `nrt_last7.json`; 2026 na série
- [ ] D7 · Dom 12–18 · `open/`, README (inglês), `DATA_DICTIONARY`, `AI_USAGE`; `make all` em máquina limpa
- [ ] Capitão · cada checkpoint → `STATUS.md`; sáb noite rascunho da submissão; dom 13–20 vídeo, página, envio

## Ciência · Melissa — harmonização (`config/`, `pipeline/bridges/`, branch `ciencia/<tema>`)
- [ ] C1 · Sáb 08–14 · `config/sensors.yaml`, interface `Bridge`, M1 (razão com encolhimento)
- [ ] C2 · Sáb 14–22 · Limiar FRP por bioma × estação × dia/noite; M2; entregar M1 e M2 ao Samuel ~20:00
- [ ] C3 · Sáb 22 → dom 06 · C4 bootstrap por blocos de ano (200×), `low_conf`, Terra 2000–2002 baixa confiança
- [ ] C4 · Dom 08–12 · Ponte NOAA-20 → S-NPP (D11); deriva de órbita (R05)
- [ ] C5 · Dom 10–13 · `METHOD.md` final; registrar λ, estação, resumo do FRP em `DECISIONS.md`

## Ciência · Samuel — validação (`pipeline/validate/`, `pipeline/analytics/`, branch `ciencia/<tema>`)
- [ ] C1 · Sáb 08–14 · Métrica (mediana |log((pred+1)/(real+1))|, R² log, viés por bioma); split por ano; baselines bruto e fator global
- [ ] C2 · Sáb 14–22 · Bruto × M1 × M2 por ponte; AI1 (HGB Poisson); `validation.json`
- [ ] C4 · Dom 08–12 · Bateria C1 (Pettitt, KS, pegada, sazonalidade) em 2002/2012/2018/2026 → `pettitt.json`
- [ ] C5 · Dom 10–13 · Números finais do Method; parágrafo "how it works" (inglês) → Murilo

## Front · Luana (`app/`, branch `front/<tema>`)
- [ ] F1 · Sáb 08–10 · Revisar §3–4 do contrato; leitor do JSON (÷ 10)
- [ ] F2 · Sáb 08–14 · Mapa + polígono + lat/lon → `polygonToCells` (res 4) → calendário cividis; publicar
- [ ] F3 · Sáb 14–24 · Dados reais; KPIs; toggle bruto × harmonizado; série com emendas; incerteza; Fire Anomaly Score
- [ ] F4 · Dom 08–13 · Página Method, CSV, pontos NRT, acessibilidade, celular
- [ ] F5 · Dom 13–20 · Telas do vídeo com Murilo, prints, teste do link final

## Se der tempo (ordem)
C3 · C5 · P2 · AI3 · P1 · AI2 · V1. Bônus: P3 · P4 · V2 · V3.

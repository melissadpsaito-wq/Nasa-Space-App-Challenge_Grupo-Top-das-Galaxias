# Governança do projeto

Como a equipe decide, trabalha e entrega durante o NASA Space Apps 2026 (14–15/11).

## 1. Papéis
Divisão em 4 pessoas conforme **D16** — Melissa e Samuel trabalham em dupla na Ciência, em módulos separados (R12). Confirmar no CP0 (sáb 13:30).

| Papel | Pessoa | Responde por | Decide sozinho |
|---|---|---|---|
| Capitão + Dados | Murilo | Escopo, checkpoints, decisões, texto da submissão, vídeo, envio · ingest, clean, grade, export, README técnico | Cortes de escopo, desempates, horário de envio; detalhes internos do pipeline que não mudam o contrato |
| Ciência · Harmonização | Melissa | `sensors.yaml`, interface `Bridge`, M1, C2 (limiar FRP), M2, C4 (incerteza), ponte NOAA-20 → S-NPP | Detalhes internos das pontes que não mudam a interface `Bridge` |
| Ciência · Validação | Samuel | Métrica comum, validação fora da amostra, C1 (Pettitt + sazonalidade), Fire Anomaly Score e pico (referência, D25), AI1 se der tempo | Detalhes internos do validador |
| Front + Demo | Luana | App web, visualizações, deploy, prints, gravação e edição do vídeo (R11) | Detalhes visuais e de código do app |
| Claude (IA) | — | Gera código, revisa método, rascunha textos | Nada: propõe, a equipe decide |

Dono do repositório: Melissa. Revisor obrigatório de PR: qualquer outro membro (ver `CONTRIBUTING.md`).

## 2. Como decidimos
| Tipo de decisão | Quem | Registro |
|---|---|---|
| Muda escopo, método, dados ou prazo | Capitão, após ouvir a equipe (máx. 10 min) | `docs/DECISIONS.md` (ID Dxx) |
| Muda o contrato de dados (`docs/DATA_DICTIONARY.md`) | Dados + Front juntos | `docs/DECISIONS.md` |
| Interna a uma área | Dono da área | Mensagem de commit |
| Desempate | Capitão | `docs/DECISIONS.md` |

Regra: decisão não registrada não existe. Mudanças de rota durante o evento seguem `docs/MENTORS.md` §1. Proposta de Claude entra como `proposta` e só vira `decidida` com o Capitão.

## 3. Ritmo (checkpoints) — v2, D23
| Quando | Checkpoint | Critério para seguir | Se falhar |
|---|---|---|---|
| Sáb 13:30 | CP0 Replanejamento | D20–D26 decididas; ambiente de todos | Capitão decide às 14:00 |
| Sáb 15:00 | CP1 Contrato | `DATA_DICTIONARY.md` congelado; JSON falso com a Luana | Front segue com dados falsos |
| Sáb 19:00 | CP2 Fundação | Pantanal agregado · M1 no validador · site publicado | Cortar Terra e NOAA-20 do piloto |
| Sáb 23:30 | CP3 Núcleo científico | Vencedor melhor que bruto · Pantanal real no app | Ficar com M1 (razão) |
| Dom 07:30 | CP4 Manhã | Série Brasil com incerteza | Só áreas prontas (R14) |
| Dom 10:00 | CP5 Corte final | O que não roda sai | — |
| Dom 12:00 | CP6 Autoavaliação | Nota 1–5 por critério de julgamento | Horas vão para o critério mais fraco |
| Dom 15:00 | CP7 Congelamento | Só correção de bug a partir daqui | — |
| Dom 21:00 | CP8 Envio interno | `docs/SUBMISSION_CHECKLIST.md` 100% | — |
| Dom 23:59 | Prazo oficial | — | — |

Formato de cada checkpoint: cada um mostra **o que roda** (não o que "quase roda"), 3 min por pessoa; Capitão registra em `docs/STATUS.md`. Cronograma completo hora a hora: `docs/PLANO-48H.md`.

## 4. Escopo vigente (D24, revisa D15)
| Faixa | Itens |
|---|---|
| Núcleo | Harmonização M2 (grade 2 km + limiar FRP + resíduo) · validação vs bruto · C4 incerteza · C1 (Pettitt + sazonalidade) · mapa/seleção · calendário · toggle · Fire Anomaly Score · probabilidade de pico · CSV · Method · áreas prontas Pantanal e SP cana |
| Se der tempo | KS no FRP · pegada espacial · AI1 (ML) · P2 · V1 |
| Período e sensores (D33) | nov/2000 → dez/2025 · Terra, Aqua, S-NPP, NOAA-20 em todos os anos · sem bioma · sem 2026/NRT |
| Futuro | Mundo inteiro com o mesmo pipeline (D28) |
| Fora | Previsão de focos (D21) · índice de agricultores (D19) · globo 3D · chatbot |
Nada entra no núcleo depois do CP3 (sáb 23:30) sem decisão registrada.

## 5. Comunicação
| Canal | Uso |
|---|---|
| Grupo da equipe | Avisos, bloqueios, checkpoints |
| GitHub (issues/PR) | Tarefas e código |
| Projeto no Claude | Contexto, decisões, conversas por frente (Dados, Front, Ciência) |
Bloqueado há mais de 30 min → avisar no grupo.

## 6. Documentos de governança
| Arquivo | Conteúdo |
|---|---|
| `docs/DECISIONS.md` | Registro de decisões |
| `docs/ROADMAP.md` | Plano das 48 h e tarefas por pessoa |
| `docs/STATUS.md` | Diário dos checkpoints |
| `docs/RISKS.md` | Riscos e planos B |
| `docs/DATA_GOVERNANCE.md` | Regras de dados, fontes, versões |
| `docs/DATA_DICTIONARY.md` | Contrato de dados (schemas) |
| `docs/METHOD.md` | Método científico e referências |
| `docs/AI_USAGE.md` | Uso de IA (campo obrigatório da submissão) |
| `docs/SUBMISSION_CHECKLIST.md` | Checklist de envio |
| `docs/RESOURCES.md` | Stack, Global Offers avaliadas e canais de apoio do evento |
| `docs/MENTORS.md` | Mudança de rota, banco de perguntas e registro das conversas com mentores |
| `docs/PLANO-48H.md` | Cronograma v2 hora a hora, divisão da equipe, passagens de bastão |
| `docs/GUIA-TECNICO.md` | Passo a passo técnico por frente, com esqueletos de código |
| `docs/guia-execucao-48h-v2.pdf` | PDF do plano v2 + guia técnico + governança (para ler no celular) |
| `docs/guia-execucao-48h-v1.pdf` | Guia v1 (início sáb 08:00) — histórico |
| `CONTRIBUTING.md` | Git, revisão, definição de pronto |

## 7. Organização do repositório
Repo: `melissadpsaito-wq/Nasa-Space-App-Challenge_Grupo-Top-das-Galaxias` (público).
| Pasta | Dono | No Git? |
|---|---|---|
| `pipeline/` (ingest, clean, grid, export, nrt) | Murilo | sim |
| `pipeline/bridges/`, `config/` | Melissa | sim |
| `pipeline/validate/`, `pipeline/analytics/` | Samuel | sim |
| `app/` | Luana | sim |
| `app/public/data/`, `open/` | só Murilo escreve | sim |
| `data/raw`, `data/clean`, `data/interim` | Murilo | não (Drive) |
| `data/processed/` | Melissa (série) · Samuel (validação) | sim, se < 50 MB |
Pipeline: `make all` = ingest → grid → bridges → validate → analytics → export.

## 8. Fonte da verdade
| O quê | Onde manda | Espelho |
|---|---|---|
| Código e `docs/` | Este repositório (`main`) | Projeto no Claude (`claude/*.md`) |
| Contexto para o Claude | Projeto no Claude | — |
Regra: muda primeiro no repositório; depois do checkpoint, o Capitão pede ao Claude para espelhar no Projeto.

## 9. Incidentes
| Data | Incidente | Ação | Status |
|---|---|---|---|
| 13/11 | Chave FIRMS commitada em `.env.example` (commit `541c557`); continua no histórico do Git | Gerar chave nova no FIRMS, usar só no `.env` local e em GitHub Secrets; tratar a antiga como exposta | aberto — fechar no CP0 |

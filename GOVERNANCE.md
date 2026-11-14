# Governança do projeto

Como a equipe decide, trabalha e entrega durante o NASA Space Apps 2026 (14–15/11).

## 1. Papéis
Divisão em 4 pessoas conforme **D16 (proposta)** — confirmar no kickoff.

| Papel | Pessoa | Responde por | Decide sozinho |
|---|---|---|---|
| Capitão + Dados | Murilo | Escopo, checkpoints, decisões, texto da submissão, vídeo, envio · ingest, clean, grade, export, NRT, README técnico | Cortes de escopo, desempates, horário de envio; detalhes internos do pipeline que não mudam o contrato |
| Ciência · Harmonização | Melissa | `sensors.yaml`, interface `Bridge`, M1, C2 (limiar FRP), M2, C4 (incerteza), ponte NOAA-20 → S-NPP | Detalhes internos das pontes que não mudam a interface `Bridge` |
| Ciência · Validação | Samuel | Métrica comum, validação fora da amostra, AI1 (M3), C1 (bateria de testes) | Detalhes internos do validador |
| Front | Luana | App web, visualizações, deploy, prints, telas do vídeo | Detalhes visuais e de código do app |
| Claude (IA) | — | Gera código, revisa método, rascunha textos | Nada: propõe, a equipe decide |

Dono do repositório: Melissa. Revisor obrigatório de PR: qualquer outro membro (ver `CONTRIBUTING.md`).

## 2. Como decidimos
| Tipo de decisão | Quem | Registro |
|---|---|---|
| Muda escopo, método, dados ou prazo | Capitão, após ouvir a equipe (máx. 10 min) | `docs/DECISIONS.md` (ID Dxx) |
| Muda o contrato de dados (`docs/DATA_DICTIONARY.md`) | Dados + Front juntos | `docs/DECISIONS.md` |
| Interna a uma área | Dono da área | Mensagem de commit |
| Desempate | Capitão | `docs/DECISIONS.md` |

Regra: decisão não registrada não existe. Proposta de Claude entra como `proposta` e só vira `decidida` com o Capitão.

## 3. Ritmo (checkpoints)
| Quando | Checkpoint | Critério para seguir | Se falhar |
|---|---|---|---|
| Sáb 08:00 | Kickoff (15 min) | Todos com ambiente rodando | Par de quem travou |
| Sáb 10:00 | Contrato de dados fixado | `DATA_DICTIONARY.md` aprovado | Front segue com dados falsos |
| Sáb 14:00 | Fundação | Pantanal agregado + mapa publicado | Cortar Terra e NOAA-20 |
| Sáb 22:00 | Núcleo científico | Harmonização melhor que bruto na métrica | Ficar com M1 (razão) |
| Dom 10:00 | Corte do ML | AI1 validado | AI1 sai do núcleo |
| Dom 12:00 | Autoavaliação | Nota 1–5 por critério de julgamento | Horas vão para o critério mais fraco |
| Dom 13:00 | Congelamento | Só correção de bug a partir daqui | — |
| Dom 20:00 | Envio | `docs/SUBMISSION_CHECKLIST.md` 100% | — |
| Dom 23:59 | Prazo oficial | — | — |

Formato de cada checkpoint: cada um mostra **o que roda** (não o que "quase roda"), 3 min por pessoa; Capitão registra em `docs/STATUS.md`.

## 4. Escopo vigente (D15)
| Faixa | Itens |
|---|---|
| Núcleo | C1 bateria de testes · C2 harmonização física · C4 incerteza · AI1 ML · mapa/seleção · calendário · Fire Anomaly Score · toggle · CSV |
| Se der tempo | C3 · C5 · AI2 · AI3 · P1 · P2 · V1 |
| Bônus | P3 · P4 · V2 · V3 |
Nada entra no núcleo depois do checkpoint de sáb 22:00 sem decisão registrada.

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
| `CONTRIBUTING.md` | Git, revisão, definição de pronto |

# Changelog da governança

## v2.6 · sáb 14/11 19:40
- Incorpora o PR `ciencia/m1`: `pipeline/grid.py` (2.2/2.3), `pipeline/bridges/{m1,check_method,m1_preview,check_extra}.py`, `tests/{test_m1,test_grid}.py`, M1 no `test_bridge_contract.py`.
- Base de código = `main` (`e43f564`, contrato 3.1 final YAML v3) + `ciencia/m1`; documentos de governança da v2.4/v2.5 mantidos.
- Novos docs: `CIENCIA-3.2-M1.md`, `DADOS-2.2-2.3-GRADE-H3.md`, `BRIEFING-PROXIMOS-PASSOS.md`. `DADOS-2.1` com revisão da §6 (deriva).
- DECISIONS: **D34** decidida (gráfico dos 4 satélites com divergências destacadas); notas em D29 (frp_sum = soma de todos os pixels) e D30 (motivo revisto). RISKS: R05 atualizado (deriva do Aqua em 2024–25, não em 2020).
- METHOD: τ medido (9,4 MW), janelas de ajuste corrigidas (Aqua→S-NPP 2012–2019), resultados do M1, ΣFRP, fogos extras do VIIRS, limites declarados.
- DATA_DICTIONARY: `frp_sum` em §2 e §5. Makefile: `grid --area $(AREA)`. ROADMAP, GUIA-TECNICO, PLANO-48H, pipeline/README: status. STATUS = espelho do Projeto (`claude/03`). AI_USAGE: linhas de 14/11.
- PDF do Guia segue v2.4 (sem regenerar); os .md são a versão viva.

## v2.5 · sáb 14/11 16:30
- Ciência 3.1 final (YAML v3): `Context` sem `cell_biome` (D33); `base.winner()` lê λ/método de `validation.json` (D31); `base.passes_reader()` para o M2; `check_config()` valida o YAML no load.
- `tests/test_bridge_contract.py`: 9 testes (timeline contínua, fit fora da sobreposição, sem bioma, `winner`, `passes_reader`).
- `DATA_DICTIONARY` §5: colunas de `grid2km_pass` alinhadas ao Guia §2.2 (`frp_max`).

## v2.4 · sáb 14/11 16:10
- D33 decidida: sem bioma; período nov/2000 → dez/2025 com Terra, Aqua, S-NPP e NOAA-20 em todos os anos; 2026/NRT fora (D11 adiada). D32 registrada (espelho do Projeto).
- Ciência 3.1 (patch) incorporado: `config/sensors.yaml` (v2), `pipeline/bridges/base.py`, `tests/test_bridge_contract.py`, `docs/CONTRATO-CIENCIA.md`.
- Atualizados: DECISIONS, sensors.yaml, CONTRATO-CIENCIA, DATA_DICTIONARY (`sensors4.json`, `consistency_4sat.json`), METHOD, GUIA-TECNICO, PLANO, ROADMAP, GOVERNANCE, RISKS (R01 encerrado, R17), DATA_GOVERNANCE, MENTORS, CHECKLIST, README, requirements (sem geopandas), STATUS, AI_USAGE.

## v2.3 · sáb 14/11 15:20
- Dados 2.1 concluído: `pipeline/ingest.py`, `pipeline/clean.py`, `pipeline/__init__.py`, `tests/test_clean.py` (commit `2e66d2e`).
- Novo: `docs/DADOS-2.1-INGEST-CLEAN.md` (passo a passo, resultados, problemas e correções).
- `DECISIONS.md`: D29 (`frp_sum`) e D30 (janela Aqua→S-NPP 2012–2019), propostas.
- `RISKS.md`: R05 com evidência da deriva MODIS.
- `DATA_GOVERNANCE.md`: fontes baixadas, resultados dos filtros.
- `DATA_DICTIONARY.md` §1: pasta do piloto e arquivos de log (sem mudança de schema).
- `GUIA-TECNICO.md` §2.1: status e como rodar. `STATUS.md`, `AI_USAGE.md`, `Makefile` (`AREA`), `.gitignore` (`data/clean_*/`), `pipeline/README.md`.

## v2.2 · sáb 14/11 14:40
- D28 decidida: Brasil inteiro; D09 marcada "revertida por D28" (regra: decisões não são apagadas). Mundo como evolução futura.

## v2.1 · sáb 14/11 14:22
- D21 decidida; D27 decidida: indicador "chance histórica de ficar acima do normal" (METHOD, GUIA-TECNICO, ROADMAP, PLANO).

## v2 · sáb 14/11 13:30
- Novo: `docs/PLANO-48H.md` (cronograma hora a hora, CP0–CP8, turnos de sono, bastões) e `docs/GUIA-TECNICO.md` (passo a passo técnico por frente).
- Novo: `docs/guia-execucao-48h-v2.pdf`; v1 renomeado para `guia-execucao-48h-v1.pdf`.
- `DECISIONS.md`: D18–D26 (propostas).
- `GOVERNANCE.md`: §1 papéis (Luana edita o vídeo; Samuel faz score), §3 checkpoints v2, §4 escopo D24, §6 documentos.
- `ROADMAP.md`: reescrito no novo horário.
- `RISKS.md`: R14 tempo, R15 escopo do PDF da equipe, R16 score.
- `DATA_DICTIONARY.md`: congelamento 15:00, FRP = máximo, `areas.json`, tiles, CSV, `src`.
- `METHOD.md`: escolhas D26, fórmula do score e do pico (D25).
- `MENTORS.md`, `SUBMISSION_CHECKLIST.md`, `STATUS.md`, `AI_USAGE.md`: horários e itens v2.

## v1 · sex 13/11 – sáb 14/11 manhã
Governança unificada, Guia de Execução 48h v1 (início sáb 08:00), D01–D17.

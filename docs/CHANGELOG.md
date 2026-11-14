# Changelog da governança

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

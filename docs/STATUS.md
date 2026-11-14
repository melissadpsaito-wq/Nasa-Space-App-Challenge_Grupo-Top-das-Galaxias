# Status dos checkpoints

Preencher em cada checkpoint (Capitão). Uma seção por checkpoint.

## Modelo
### <dia hh:mm> · <nome do checkpoint>
| Pessoa | O que roda (demonstrado) | Bloqueio | Próximo |
|---|---|---|---|
| Murilo (Capitão + Dados) | | | |
| Melissa (Harmonização) | | | |
| Samuel (Validação) | | | |
| Luana (Front) | | | |
Decisões tomadas: Dxx, Dyy · Riscos novos: Rxx

---
## Sex 13/11 · Fase 0
| Item | Situação |
|---|---|
| Inscrição, equipe, Local Lead | ✅ |
| MAP_KEY + Earthdata | ✅ (falta `.env` local) |
| MODIS 2000–2025 | ✅ |
| S-NPP / NOAA-20 | 2025 ✅; demais anos pendentes |
| Dados 2026 | pendente |
| Repo | organizado (estrutura + governança); falta deploy "hello world" |
| Equipe | 4 pessoas (D16, proposta: confirmar no kickoff) |
| Incidente | chave FIRMS no histórico do Git (R09) — gerar chave nova |
Achados: S-NPP/Aqua = 5,42× (2025); com grade comum de ~2 km cai para 3,45×; N20/S-NPP = 0,98×.

---
## Sáb 14/11 13:30 · CP0 Replanejamento (preencher na reunião)
| Item | Situação |
|---|---|
| Manhã | Estratégia: persona (D18/D19), padrão Twisters, PDF da equipe (Document 5) revisado |
| Construção | Ainda não iniciada; app começa sáb 19:45 (D23) |
| Decisões a votar | D20 persona · D21 sem previsão · D22 áreas prontas · D23 cronograma v2 · D24 corte de escopo · D25 score · D26 escolhas de método · confirmar D16, D17 |
| Pendências da Fase 0 | Chave FIRMS nova · S-NPP 2012–24 · N20 2018–24 · 2026 · RESOLVE |
| Equipe | Murilo (Capitão + Dados) · Melissa + Samuel (dupla Ciência) · Luana (Front + Demo) |
Decisões tomadas: ___ · Riscos novos: R14, R15

### Sáb 14:40 · Decisões
D21, D27 (14:22) e D28 (14:40) decididas. Escopo geográfico: Brasil inteiro; downloads S-NPP 2012–24 e NOAA-20 2018–24 só do Brasil.

---
## Sáb 14/11 15:13 · Dados 2.1 Ingest + clean concluído
| Item | Situação |
|---|---|
| Código | `pipeline/ingest.py`, `pipeline/clean.py`, `tests/test_clean.py` · commit `2e66d2e` (branch `dados/ingest-clean`) · PR pendente |
| Conferência Brasil 2025 | 0,00% de diferença vs `08-fatos-dados` nos 4 sensores |
| Piloto Pantanal 2000–2025 | 2.028.235 focos limpos (Terra 200.914 · Aqua 251.978 · S-NPP 913.045 · N20 662.298) em `data/clean_pantanal/` |
| Filtros | parse 0% · date 0% · type 0,1–2,6% · conf MODIS 4–6% / VIIRS 9–11% |
| Testes | 4/4 (conservação + schema §1) |
| Dados FIRMS | ZIPs `all_countries`: MODIS 2000–2025, S-NPP 2012–2025, N20 2018–2025 ✅ · 2026 pendente |
| Achado | Deriva MODIS: S-NPP/Aqua 5,94 (2012–19) → 7,15 (2020–25) no Pantanal → D30 |
Detalhes: `docs/DADOS-2.1-INGEST-CLEAN.md` · Decisões propostas: D29, D30 · Riscos atualizados: R05

### Sáb 16:10 · D33 decidida
Sem bioma; análise nov/2000 → dez/2025 com Terra, Aqua, S-NPP e NOAA-20 em todos os anos. Saem: RESOLVE, `cell_biome`, geopandas, 2026, NRT. Dados 2.1 já cobre isso (ZIPs 2000–2025 conferidos). Próximo: Dados 2.2 grade + H3.

### Sáb 16:30 · Ciência 3.1 contrato final
| Item | Situação |
|---|---|
| Arquivos | `config/sensors.yaml` v3 · `pipeline/bridges/base.py` · `tests/test_bridge_contract.py` · `docs/CONTRATO-CIENCIA.md` |
| Testes | 9/9 (passes_reader exige pyarrow) |
| Mudou | sem `cell_biome` (D33) · `winner()` (D31) · `passes_reader()` (M2) · `check_config()` |
| Pendente Capitão | D30 (fit Aqua→S-NPP 2012–2019) · D31 · D32 |
| Próximo | Melissa: M1 (§3.2) · Samuel: `validate/run.py` com Identity e GlobalFactor |

# Status dos checkpoints (atualizado 14/11 19:31 · espelho no Projeto: `claude/03-status.md`)


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
| Código | `pipeline/ingest.py`, `pipeline/clean.py`, `tests/test_clean.py` · commit `2e66d2e` · no `main` ✅ |
| Conferência Brasil 2025 | 0,00% de diferença vs `08-fatos-dados` nos 4 sensores |
| Piloto Pantanal 2000–2025 | 2.028.235 focos limpos (Terra 200.914 · Aqua 251.978 · S-NPP 913.045 · N20 662.298) em `data/clean_pantanal/` |
| Filtros | parse 0% · date 0% · type 0,1–2,6% · conf MODIS 4–6% / VIIRS 9–11% |
| Testes | 4/4 (conservação + schema §1) |
| Dados FIRMS | ZIPs `all_countries`: MODIS 2000–2025, S-NPP 2012–2025, N20 2018–2025 ✅ · 2026 pendente |
| Achado | Deriva MODIS: S-NPP/Aqua 5,94 (2012–19) → 7,15 (2020–25) no Pantanal → D30 |
Detalhes: `docs/DADOS-2.1-INGEST-CLEAN.md` · Decisões propostas: D29, D30 · Riscos atualizados: R05

### Sáb 16:10 · D33 decidida
Sem bioma; análise nov/2000 → dez/2025 com Terra, Aqua, S-NPP e NOAA-20 em todos os anos. Saem: RESOLVE, `cell_biome`, geopandas, 2026, NRT.

---
## Sáb 14/11 16:30 · Ciência 3.1 contrato no `main`
| Item | Situação |
|---|---|
| Merge | PR #2 → `main` (`e43f564`; commit `5c22053`) ✅ |
| Arquivos | `config/sensors.yaml` v3 · `pipeline/bridges/base.py` · `tests/test_bridge_contract.py` · `docs/CONTRATO-CIENCIA.md` · `requirements.txt` (+pyyaml, pyarrow) |
| Testes | 9/9 na máquina do Murilo |
| Dados 2.1 | `2e66d2e` também já está no `main` |
| Pendente | Pacote de governança v2.4 fora do `main` (DECISIONS sem D17–D33, ROADMAP/STATUS antigos, sem PLANO-48H/GUIA-TECNICO) · Capitão decidir D30, D31, D32 |
| Próximo | Melissa: M1 (§3.2) · Samuel: `validate/run.py` (Identity, GlobalFactor) · Murilo: Dados 2.2 grade + H3 |

---
## Sáb 14/11 17:53 · Dados 2.2 + 2.3 e Ciência 3.2 (M1) concluídos — CP2 adiantado
| Item | Situação |
|---|---|
| Código | PR `ciencia/m1` aberto (commits `ea41bc5` … `f30b43d`): `pipeline/grid.py` · `pipeline/bridges/{m1,check_method,m1_preview,check_extra}.py` · testes `test_m1` (12), `test_grid` (3+1), M1 no contrato (λ 0/5/20/50) — todos passam na máquina do Murilo |
| `check_method` (Brasil 2025) | 5,42 → 3,58 (0,01°) → 3,45 (0,02°) → 1,00 com τ = 9,4 MW ✅ igual ao METHOD.md; 08-fatos corrigido (dizia 3,45 / 2,77) |
| ΣFRP | S-NPP/Aqua 1,17 (bruto) · 0,76 (Σ frp_max) · varia mais entre meses que a contagem (CV 16% × 12%) → unidade principal segue contagem; D29: somar todos os pixels |
| 2.2 Pantanal | 1 s · conservação OK · 199 células H3 |
| 2.3 Brasil 2000–2025 | ingest ~1 min (2025 = 0,00%) · grade 19 s · conservação OK · ~4.200 células · S-NPP/Aqua na grade 3,96 (2012–19) → 3,98 (2020–21) |
| M1 conferência (Brasil) | consistency teste 2020–21: bruto 1,10 · taxa única 0,69 · **M1 0,45** (LOYO 0,42); Σpred/ΣB 0,99; λ 5 ≈ 20 |
| Prévia 4 satélites | Aqua→S-NPP ±4% (2012–23) · N20→S-NPP ±3% · Aqua 2024–25 +15–23% (deriva) · Terra pós-2011 +15–60% |
Detalhes: `claude/31-ciencia-3.2-m1.md`, `claude/32-dados-2.2-2.3-grade-h3.md` · Decisões: **D34 decidida (18:07)** · Riscos: **R05 atualizado** · D30 com motivo revisto

### Sáb 19:26 · Achado: de onde vêm os fogos extras do VIIRS (`check_extra`, Brasil 2025)
No mês: 65% a ≤ 10 km de um fogo MODIS · 26% a 10–50 km · **9% invisíveis ao MODIS** (1,6 MW, 77% noturnos; pesam 0,30 dos 3,45). No mesmo dia só 44,5% dos fogos diurnos do Aqua têm par no S-NPP (faixa/horário) → comparar por mês, como o M1 faz.

### Sáb 19:31 · Próximo (ver `claude/33-briefing-proximos-passos.md`)
| Pessoa | Próximo |
|---|---|
| Murilo | Merge PR `ciencia/m1` + governança v2.4 · 2.4 export `harm_monthly.json` Pantanal (M1 provisório) → Luana 23:45 · `sensors4.json` · decidir D29 (texto), D30–D32 |
| Melissa | 3.3 M2 (`pipeline/bridges/m2.py`): τ por trimestre × dia/noite em 2012–2019; meta bater M1 (0,447 / 0,418) |
| Samuel | `validate/run.py` → `validation.json` (bruto × global × M1 × M2) com o `agg_monthly` Brasil |
| Luana | App com JSON falso → real às 23:45; unidade "escala S-NPP"; gráfico D34 |

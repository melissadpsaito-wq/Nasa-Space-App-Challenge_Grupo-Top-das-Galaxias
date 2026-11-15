# Uso de IA

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
| 15/11 | Claude (Anthropic) | Front 4.2 | Rascunho de `app/src/analytics.js` (Fire Anomaly Score e pico típico D25, chance histórica D27, CSV §7) + `test/analytics.test.js` (9 testes); desenho de área por cliques (`polygonToCells` res 5) e painel com indicadores e botão CSV em `mapa.js`; textos EN/PT | Murilo |
<!-- Se alguém usar GitHub Copilot ou outra IA, adicionar uma linha aqui. -->

### Texto para o formulário (rascunho)
We used Claude (Anthropic) as a pair-programmer and reviewer: planning, exploratory analysis of FIRMS data, drafting code that every team member ran and reviewed on real data, and drafting documentation. All scientific decisions were made and validated by the team. No AI-generated images, video or audio were used [update if this changes]. No NASA branding was generated or modified by AI.

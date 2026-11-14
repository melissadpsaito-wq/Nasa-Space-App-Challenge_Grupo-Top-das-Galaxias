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
| 14/11 | Claude (Anthropic) | Ciência 3.1 | Fechamento do contrato: remoção do bioma (D33), `winner()`, `passes_reader()`, `check_config()` e novos testes | Murilo |
<!-- Se alguém usar GitHub Copilot ou outra IA, adicionar uma linha aqui. -->

## Texto para o formulário (rascunho)
We used Claude (Anthropic) as a pair-programmer and reviewer: planning, exploratory analysis of FIRMS data, drafting code that every team member ran and reviewed on real data, and drafting documentation. All scientific decisions were made and validated by the team. No AI-generated images, video or audio were used [update if this changes]. No NASA branding was generated or modified by AI.

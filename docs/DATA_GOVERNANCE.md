# Governança de dados

## Princípios
1. **Bruto é imutável.** Arquivos baixados não são editados; ficam em `data/raw/` no Drive da equipe, fora do Git.
2. **Processado é sempre gerado por script.** Nada em `data/processed/` é editado à mão; `make all` recria tudo.
3. **Toda fonte tem versão e data de download** registradas na tabela abaixo e em `meta.json` do export.
4. **Segredos fora do código.** `MAP_KEY` só em `.env` local e em GitHub Secrets.
5. **Sem dados pessoais.** O projeto usa apenas dados de satélite públicos.

## Fontes
| Fonte | Produto | Período | Origem | Versão (campo `version`) | Baixado em | Por |
|---|---|---|---|---|---|---|
| MODIS Terra/Aqua | FIRMS resumo anual por país (C6.1) | 2000–2025 | firms.modaps.eosdis.nasa.gov/country | 6.2 (2000) · 61.03 (2024–25) [confirmar significado] | 13/11/2026 | Dados |
| VIIRS S-NPP 375 m | FIRMS resumo anual (`viirs-snpp`) | 2012–2025 | idem | 2 | 2025: 13/11/2026 | Dados |
| VIIRS NOAA-20 375 m | FIRMS resumo anual (`viirs-jpss1`) | 2018–2025 | idem | 2 | 2025: 13/11/2026 | Dados |
| VIIRS S-NPP / NOAA-20 2026 | Archive Download ou API | jan–nov/2026 | FIRMS | — | — | Capitão |
| NRT NOAA-20 | API FIRMS area/csv | últimos 7 dias | FIRMS API (GitHub Action) | NRT | contínuo | Dados |
| Ecorregiões | RESOLVE Ecoregions 2017 | — | — | — | — | Dados |
| Referência externa | INPE BDQueimadas (V1) | mensal | INPE | — | — | Capitão |

## Fluxo (linhagem)
`data/raw` (ZIP/CSV) → `data/clean` (Parquet, schema único, filtros) → `data/interim` (agregados) → `data/processed` (série harmonizada, validação) → `app/public/data` (JSON) e `open/` (dataset aberto).

## Regras de qualidade aplicadas
| Regra | Fonte da regra |
|---|---|
| Manter só `type = 0` (vegetação presumida) | Guia MODIS C6 §5.5 |
| MODIS `confidence ≥ 30`; VIIRS `confidence ∈ {n, h}` | Guia MODIS C6 Tab. 10 e §8.4.2 |
| Série a partir de nov/2000 | Guia MODIS C6 §7.2.1 |
| Excluir 16/08–02/09/2020 das métricas das pontes com Aqua | Guia MODIS C6 §7.2.4 |
| Agregação temporal ≥ 8 dias | Guia MODIS C6 §7.1.1 |
| Teste de conservação: soma de focos agregados = linhas filtradas | Interno |

## Limitações declaradas
- Arquivos de focos não informam nuvem nem falta de observação.
- FRP de sensores diferentes não é diretamente comparável; o limiar é um indicador calibrado.
- CSV de focos individuais só para áreas prontas e últimos 7 dias (volume).

## Uso e citação
Dados NASA FIRMS sob a política de dados abertos da NASA. Citar: "NASA FIRMS, MODIS Collection 6.1 and VIIRS 375 m active fire products". Dataset harmonizado publicado em `open/` sob MIT para o código e com a mesma citação para os dados.

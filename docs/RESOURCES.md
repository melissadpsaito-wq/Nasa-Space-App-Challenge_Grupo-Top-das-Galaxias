# Recursos e ferramentas

Atualizado em 14/11 com as Global Offers do Space Apps. Decisão: **D17 (proposta)**.
Princípio: só adotar o que reduz risco ou melhora a nota sem criar backend, chave nova no navegador ou dependência de cartão de crédito no caminho crítico.

## Stack confirmada (sem mudança)
| Camada | Ferramenta | Custo |
|---|---|---|
| Dados | NASA FIRMS (resumo anual, Archive Download, API) | grátis |
| Processamento | Python 3.11, pandas, DuckDB, h3, scikit-learn, scipy | grátis |
| App | Vite + JS, Leaflet + Leaflet.draw (tiles OpenStreetMap), h3-js, Observable Plot | grátis |
| Hospedagem | GitHub Pages + GitHub Actions (NRT, chave em Secrets) | grátis |
| IA | Claude (Anthropic) | — |

## Global Offers avaliadas
| Oferta | O que dá | Uso no projeto | Decisão proposta |
|---|---|---|---|
| **GoDaddy** | Domínio + 1 ano de hospedagem | Só o **domínio**, apontado para o GitHub Pages (link curto no vídeo e na submissão). Hospedagem continua no GitHub | ✅ Adotar (se não exigir pagamento) · Luana |
| **Microsoft · GitHub Copilot** | Assistente de código no editor | Opcional para quem quiser; **declarar em `AI_USAGE.md`** | 🟡 Livre, com registro |
| **Microsoft · Planetary Computer** | Catálogo STAC com MODIS 14A1 (fogo diário gridado, com máscara de nuvem/sem dado) | Responder à limitação "nuvem não aparece nos focos": medir fração de observações válidas por célula × mês | 🟡 Bônus (V4), só com muito tempo · Samuel |
| **Google Cloud** (Firebase, Maps API, Earth Engine) | Nuvem, hospedagem, mapas | Não precisamos de backend; Leaflet + OSM substitui Maps API (sem chave no navegador) | ❌ Não adotar |
| **Meteomatics** | API de clima | Contexto meteorológico das anomalias; fora do escopo D15 e exige chave/backend | ❌ Não adotar (ideia pós-hackathon) |
| **Microsoft · Azure / Teams** | Nuvem / comunicação | Sem backend; grupo da equipe já resolve | ❌ Não adotar |
| **Miro** | Quadro colaborativo + templates Space Apps | Kickoff de 15 min e diagrama do pipeline, se a equipe quiser | 🟡 Opcional |

## Canais de apoio do evento
| Canal | Para quê |
|---|---|
| **Space Apps Connect** | Perguntas a Local Leads, Navigators e especialistas (SMEs); usar o banco de perguntas de `MENTORS.md` |
| Participant Guides (Submission, Judging & Awards) | Regras de envio e elegibilidade; conferir antes do checklist final |
| Navigating the Hackathon (vídeos) | Passo a passo do formulário de submissão |

## Regras ao usar qualquer oferta
- Nada que peça cartão no caminho crítico: se o domínio exigir pagamento, seguimos com o endereço do GitHub Pages.
- Toda ferramenta de IA usada (Copilot, Claude etc.) entra em `AI_USAGE.md`.
- Listar ferramentas e dados externos no campo "Space Agency Partner & Other Data" da submissão.
- O link publicado precisa continuar no ar até o anúncio dos vencedores (jan/2027).

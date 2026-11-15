# Fire Almanac — Sistema web (resumo unificado · 4.1 concluída)

**dom 15/11/2026 06:00** · decisões D05, D36, D38, D44, D46 · branch `front/setup` · donos: Samuel (visual), Luana (front), Murilo (dados em `public/data/`)

## 1. O que é
| Item | Definição |
|---|---|
| Produto | Site estático com 2 páginas: **landing** (`index.html`) e **mapa** (`mapa.html`) |
| Pergunta da persona | *"For this location, how unusual is fire, and when does it peak?"* (D20/D35) |
| Arquitetura | Sem servidor (D05, D46): o navegador lê os tiles `harm_<pai res 2>.json` e soma no próprio navegador |
| Stack | Vite 5 · Leaflet 1.9 · h3-js 4.5 · Observable Plot 0.6 · JS puro · CSS próprio |
| Visual | Telas e estilo do Samuel (landing + mapa); paleta **cividis invertida** (acessível a daltonismo) |
| Idioma | **EN/PT** com botão; padrão EN (juízes); `?lang=pt` força PT |
| Hospedagem | GitHub Pages via `.github/workflows/pages.yml` (build + testes + deploy a cada push em `main` que toque `app/`) |

## 2. Fluxo de dados
`pipeline/export.py` (2.4) → `app/public/data/harm_<pai>.json` (128 tiles, res 5 dentro de pai res 2, × 10) → `TileStore` (fetch + cache; 404 = pai sem fogo) → `areaSeries` (soma células, ÷ 10) → `slicePeriod` (período De/Até) → painel + calendário · `cellTotals` → cores do mapa

| Regra do contrato (§3, §11) | Onde no código |
|---|---|
| Vetores alinhados com `months`, inteiros × 10 | `validateTile` (recusa tile fora do contrato) |
| Célula ausente no tile = sem fogo; pai 404 = sem fogo | `areaSeries` |
| `lo`/`hi` ausentes → usa o próprio valor (série provisória, `lo = hi`) | `areaSeries` |
| `low_conf` da área = 1 se alguma célula com fogo no mês tiver 1 | `areaSeries` |
| Ponto → `latLngToCell(lat, lon, 5)` → `cellToParent(…, 2)` → tile | `mapa.js` |

## 3. Telas e funções
| Tela | Funções | Estado |
|---|---|---|
| Landing | Hero, "por que importa", 3 funcionalidades, CTA, citação NASA FIRMS | ✅ |
| Mapa · local | Busca de cidade (Nominatim, só Brasil) · lat/lon · clique → hexágono ~17 km destacado | ✅ |
| Mapa · período | **De (ano + mês) / Até (ano + mês)**, nov/2000–dez/2025; erro se "De" > "Até" | ✅ |
| Mapa · valores | Harmonizado × Bruto (mesma escala; o salto falso de 2012 aparece no bruto) | ✅ |
| Mapa · camada | Hexágonos coloridos pelo total do período, zoom ≥ 7, até 12 tiles por vista, escala até o p98 | ✅ |
| Painel | Região e célula · período · detecções harmonizadas e brutas · mês com mais fogo + satélite · meses de baixa confiança · nota "provisória, ~17 km, não propriedade" | ✅ |
| Calendário | Ano × mês do período, cividis, tooltip com harm/bruto/satélite, ○ = baixa confiança, < 0,5 detecção = cinza (R22) | ✅ |
| Aba Timeline | Mensagem "próxima etapa" | ⏳ 4.4 |
| Aba Outlook | Mensagem "após o portão do CP5" | ⏳ D35 |

## 4. Arquivos (`app/`)
| Arquivo | Papel |
|---|---|
| `index.html` · `src/main.js` · `src/style.css` | Landing |
| `mapa.html` · `src/mapa.js` · `src/mapa.css` | Mapa, filtros, painel |
| `src/data.js` | Leitor de tiles (`TileStore`, `validateTile`, `areaSeries`, `periodIndex`, `slicePeriod`, `cellTotals`, `summarize`) |
| `src/calendar.js` | Calendário (Plot) |
| `src/i18n.js` | Textos EN/PT |
| `test/data.test.js` | 11 testes do leitor (`npm test`, sem rede) |
| `vite.config.js` | 2 páginas; `base` do Pages só no build |
| `public/data/harm_82*.json` | Tiles — fora do Git até o export final (D38) |
Referência (não publicado): `app.py`, `templates/`, `static/` do Samuel; `index.html`, `js/`, `static/` da Luana na raiz.

## 5. Conferências feitas
| Teste | Resultado |
|---|---|
| 128 tiles reais × `validateTile` | 0 fora do contrato · 28.769 células · 302 meses · Σ harm 18.529.552 (−0,09% de arredondamento) |
| Testes do leitor | 11/11 (container e máquina do Murilo) |
| Navegador com Leaflet/h3/Plot reais e tiles do Pantanal | -18,5 / -57: 528 harm × 304 brutas; pico set/2004 (Aqua); período 2010–2015 recorta; troca EN/PT; 0 erro no console |
| Celular 375 px | Layout empilhado ok |
| `npm install` + `npm test` + `npm run dev` (Windows) | ✅ |
| `npm run build` | ⏳ não rodado (aviso do esbuild no npm 11) |

## 6. Decisões e riscos ligados ao front
| ID | Ponto |
|---|---|
| D05 / D46 | Estático, sem Flask; visual do Samuel; EN/PT; período De/Até |
| D36 | Resolução do produto res 5 (~17 km); tela diz "não é uma propriedade" (R19) |
| D38 | Tiles fora do Git até antes do CP7 → **site publicado fica sem dados até lá**; demo local com `npm run dev` |
| D44 / 2.4c | Calendário diário entra quando sair `harm_daily_<pai>.json` |
| D35 / R18 | Outlook só aparece se o portão do CP5 aprovar; senão D27 |
| R22 | Termo aditivo pinta meses minúsculos antes de 2012 → exibição com corte em 0,5 detecção |
| R24 | Comparações seguem mensais; o dia é só exibição |

## 7. Pendências (ordem sugerida)
| # | Item | Dono | Quando |
|---|---|---|---|
| 1 | `npm run build` ok (se falhar: `npm install-scripts approve esbuild`) | Murilo | Agora |
| 2 | Commit em `front/setup`: `git add app/ .github/workflows/pages.yml` (nunca `git add .`) · PR → `main` com revisão | Murilo | Antes do CP4 |
| 3 | Pages: Settings → Source = GitHub Actions | Melissa | Após o merge |
| 4 | D46 em `docs/DECISIONS.md` + linha em `AI_USAGE.md` | Murilo | Com o commit |
| 5 | Score D25 + chance D27 + pico típico no painel; CSV | Luana | 07:30–10:00 |
| 6 | Desenho de área (`polygonToCells(…, 5)` → `areaSeries`) | Luana | 07:30–10:00 |
| 7 | Aba Timeline (série com emendas 2002/2012) e página Method | Luana + Ciência | 10:00–12:00 |
| 8 | Aba Outlook com `forecast_2026.json` ou D27 | Luana | Após CP5 |
| 9 | Calendário diário (2.4c) | Murilo → Luana | Após 2.4c |
| 10 | 2.4b reexport (vencedor + `lo/hi`) e commit único dos tiles | Murilo | Antes do CP7 |

## 8. Rodar
```cmd
cd app
npm install
npm test
npm run dev      :: http://localhost:5173  e  /mapa.html
npm run build
```

## 9. Uso de IA
| Data | Ferramenta | Onde | Para quê | Revisado por |
|---|---|---|---|---|
| 15/11 | Claude (Anthropic) | Front 4.1 / D46 | Port do front do Samuel para `app/` estático: i18n EN/PT, mapa com período e hexágonos, calendário, leitor de tiles + 11 testes, `pages.yml`; correção do import do Leaflet; teste em navegador com bibliotecas e tiles reais | Murilo |

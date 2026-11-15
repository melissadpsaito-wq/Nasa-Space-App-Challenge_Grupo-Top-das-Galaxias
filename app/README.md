# app/ — Fire Almanac (front estático, D05 + D46)
Visual e telas do Samuel (landing + mapa), sem backend: o navegador lê os tiles `public/data/harm_<pai res 2>.json`.
Vite + Leaflet + h3-js + Observable Plot, EN/PT. Só o Murilo escreve em `public/data/` (contrato: `docs/DATA_DICTIONARY.md` §3, §11).

## Rodar
```bash
cd app
npm install        # gera package-lock.json (commitar: o deploy usa npm ci)
npm test           # 11 testes do leitor (sem rede)
npm run dev        # http://localhost:5173  e  /mapa.html
npm run build      # dist/ com base do GitHub Pages
```
Dados locais: tiles do export 2.4 em `app/public/data/` (fora do Git até o export final, D38).

## Páginas e arquivos
| Arquivo | Papel |
|---|---|
| `index.html` + `src/main.js` + `src/style.css` | Landing (textos EN/PT) |
| `mapa.html` + `src/mapa.js` + `src/mapa.css` | Busca (Nominatim), lat/lon, clique → célula H3 res 5; período De/Até; Harmonizado × Bruto; hexágonos no mapa (zoom ≥ 7); painel com KPIs e calendário |
| `src/calendar.js` | Calendário ano × mês (cividis, mesmo domínio bruto × harmonizado; < 0,5 detecção = cinza, valor no tooltip) |
| `src/data.js` | `TileStore`, `validateTile`, `areaSeries`, `periodIndex`, `slicePeriod`, `cellTotals`, `summarize` |
| `src/i18n.js` | Textos EN/PT; padrão EN; `?lang=pt` |
| `test/data.test.js` | Testes do leitor |

## Pendente
Aba Timeline (série com emendas, 4.4) · aba Outlook (após o portão do CP5, D35) · calendário diário (export 2.4c, D44) · desenho de área (`polygonToCells(…, 5)` → `areaSeries`).

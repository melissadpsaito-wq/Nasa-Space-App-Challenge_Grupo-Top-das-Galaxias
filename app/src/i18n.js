// Textos EN/PT (D46). Padrão: inglês (juízes); escolha guardada no navegador; ?lang=pt força.
// Marcação: data-i18n (texto), data-i18n-html (HTML), data-i18n-ph (placeholder), data-i18n-aria (aria-label).

const DICT = {
  en: {
    'nav.map': 'Open map', 'nav.home': 'Home', 'lang.switch': 'PT',
    'hero.title': 'Fire leaves a trail. We turned 25 years of it into one consistent record.',
    'hero.text': 'Fire Almanac harmonizes NASA MODIS and VIIRS satellite fire detections (2000–2025) into a single series, so you can see where and when fire usually happens around any point in Brazil.',
    'hero.cta': 'Open the map',
    'hero.aria': 'Hexagon grid colored by fire activity',
    'why.title': 'When fire is spotted, it is already late',
    'why.p1': 'A fire that gets out of control destroys in hours what nature took decades to build. Cerrado, Pantanal and Amazon lose species, springs and soil. Communities breathe smoke for weeks, and farmers watch crops and pastures turn to ash.',
    'why.p2': 'Knowing <strong>where and when</strong> fire usually shows up changes the game. Brigades position crews before the peak, authorities prioritize inspection, and farmers adjust management and firebreaks. Every hour of lead time saves water, fuel, money and lives.',
    'feat.title': 'What you can do with Fire Almanac',
    'feat.hist.t': 'One record, four satellites',
    'feat.hist.p': 'Terra, Aqua, S-NPP and NOAA-20 see fire differently. We put them on the same scale, so the 2012 jump from switching satellites disappears and real trends remain.',
    'feat.place.t': 'Your place, your period',
    'feat.place.p': 'Search a city, type coordinates or click the map, then pick any period from 2000 to 2025 to see the fire calendar for that region.',
    'feat.outlook.t': 'Fire Forecast 2026',
    'feat.outlook.p': 'Chance of above-normal fire for each month of 2026. Shown only after it beats climatology on 2021–2025 tests.',
    'cta.title': 'Explore fire in your region',
    'foot.data': 'Data: NASA FIRMS, MODIS Collection 6.1 and VIIRS 375 m active fire products. Maps © OpenStreetMap contributors. · Top das Galáxias - 2026',

    'tab.aria': 'View mode', 'tab.history': 'History', 'tab.timeline': 'Timeline', 'tab.outlook': 'Fire Forecast',
    'search.ph': 'Search a city or region…', 'search.aria': 'Search a city or region', 'search.none': 'Place not found.',
    'loc.lat': 'Latitude', 'loc.lon': 'Longitude', 'loc.go': 'Go',
    'f.from': 'From', 'f.to': 'To', 'f.year': 'Year', 'f.month': 'Month', 'f.apply': 'Apply',
    'f.mode': 'Values', 'f.harm': 'Harmonized', 'f.raw': 'Raw',
    'f.range': 'Data cover Nov 2000 – Dec 2025.',
    'f.err.order': '“From” must be before “To”.',
    'map.aria': 'Map of Brazil: click to choose a location',
    'map.zoom': 'Zoom in to see fire by hexagon.',
    'map.loading': 'Loading fire data…',
    'map.legend': 'Detections in the period',
    'map.many': 'Area too large: zoom in a bit more.',
    'panel.empty': 'Choose a place: search, type coordinates or click the map.',
    'panel.loading': 'Loading fire record…',
    'panel.nofire': 'No fire detected in this region during 2000–2025.',
    'panel.error': 'Could not load data:',
    'panel.outscope': 'Could not load data outside the scope.',
    'panel.area': 'Region · lat, lon', 'panel.sum': 'Period summary',
    'panel.period': 'Period', 'panel.harm': 'Harmonized detections', 'panel.raw': 'Raw detections',
    'panel.harm.u': '(S-NPP scale)', 'panel.raw.u': '(each satellite’s own count)',
    'panel.peak': 'Busiest month', 'panel.lowconf': 'Low-confidence months',
    'cal.title': 'Fire calendar', 'cal.year': 'Year', 'cal.legend': 'Detections per month',
    'draw.start': 'Draw area', 'draw.finish': 'Finish area', 'draw.cancel': 'Cancel',
    'draw.hint': 'Click the map to add corners (at least 3).',
    'draw.hint2': 'Double-click, press Enter or “Finish area” to close. Esc cancels.',
    'draw.big': 'Area too large for the browser (more than ~16 data tiles). Draw a smaller area, e.g. a municipality or part of a state.',
    'panel.drawn': 'Drawn area', 'panel.cells': 'hexagons',
    'score.title': 'Fire Anomaly Score', 'score.median': 'median', 'score.none': 'No fire in this month nor in earlier years.',
    'band.extreme': 'Extreme', 'band.high': 'Well above normal', 'band.above': 'Above normal', 'band.normal': 'Within normal',
    'chance.of': 'of', 'chance.strip': 'Historical chance of above-normal fire, by month (last 10 years)',
    'chance.leg': 'Years above normal, out of 10:', 'chance.leg.na': 'fewer than 5 years with fire',
    'peak.title': 'Typical peak', 'peak.then': 'then',
    'ind.years': 'years', 'ind.insufficient': 'Not enough data (fewer than 5 years with fire).',
    'ind.how.title': 'How to read these indicators',
    'ind.how.harm': 'sum of detections in the period, converted to the S-NPP scale: comparable across satellites and years.',
    'ind.how.raw': 'sum of what each satellite counted, with no adjustment: the switch to S-NPP in 2012 inflates the count.',
    'ind.how.busiest': 'month of the period with the most harmonized detections; below, its value and satellite.',
    'ind.how.score': 'how unusual the “To” month is versus the same month in earlier years: percentile 0–100 (≥ 60 above normal · ≥ 85 well above · ≥ 95 extreme); “× median” compares it with the typical value; “n years” = years compared.',
    'ind.how.peak': 'month that was most often the strongest of the year (complete years); “k of n years” = how often; “then” = runner-up.',
    'ind.how.base': 'Score and Typical peak use the full harmonized record, not only the chosen period.',
    'help.aria': 'What does this chart show?',
    'help.cal': '<ul><li><b>Rows</b> = years; <b>columns</b> = months of the chosen period.</li><li><b>Color</b> = detections in the month: light blue (few) → yellow (many); gray = no fire.</li><li><b>○</b> = low confidence (Nov 2000 – Jun 2002, Terra only).</li><li>Hover a cell to see harmonized, raw and satellite.</li><li>Switch Harmonized ↔ Raw: the false 2012 jump appears and disappears.</li></ul>',
    'help.chance': '<ul><li><b>Big number</b> = in how many of the last 10 complete years{range} the month was above normal.</li><li><b>Normal</b> = that month’s median over every year of the record.</li><li>Historical frequency, not a forecast.</li></ul>',
    'help.tl': '<ul><li><b>Line</b> = detections per month in the area, Nov 2000 – Dec 2025 (Harmonized or Raw, as in the filter).</li><li><b>Shaded bands</b> = satellite behind each stretch: Terra → Aqua → S‑NPP. The seams are the satellite switches.</li><li><b>Blue line + yellow dot</b> = month shown; the map paints the area’s hexagons for that month.</li><li>Click or drag on the chart to jump to a month.</li></ul>',
    'help.clim': '<ul><li><b>Each box</b> = a month of 2026.</li><li><b>Number and bar</b> = share of years (2016–2025) with at least one fire detection in that month.</li><li>Hover a month for the exact value. Drawn area = average of its hexagons.</li></ul>',
    'csv.btn': 'Download CSV (period)',
    'soon.timeline': 'Monthly series with the satellite seams (Terra → Aqua → S-NPP) — coming next.',
    'tl.cursor': 'Date cursor (year and month)', 'tl.btn.prev': 'Previous month', 'tl.btn.next': 'Next month', 'tl.btn.play': 'Play', 'tl.btn.pause': 'Pause',
    'tl.edit': 'Change region', 'tl.edit.done': 'Back to locked region',
    'tl.edit.hint': 'Click the map, draw an area or search a place. The Timeline reloads with the new region.',
    'tl.date': 'Month shown', 'tl.sum': 'Detections in the area',
    'tl.chart': 'Monthly series · satellite seams',
    'tl.legend': 'Detections per hexagon in the month', 'tl.legend.fixed': 'fixed scale, same for every month',
    'clim.title': 'Climatological forecast 2026',
    'clim.avg': 'Average of',
    'clim.top': 'Highest chance of the year', 'clim.none': 'no month with fire',
    'clim.high': 'Months at 70% or more', 'clim.high.none': 'no month reaches 70%', 'clim.month': 'month', 'clim.months': 'months',
    'clim.leg': 'Share of years with fire:',
    'clim.how.title': 'How to read the forecast',
    'clim.how.top': 'highest percentage among the 12 months of 2026, and the month(s) where it occurs.',
    'clim.how.high': 'months with fire in at least 7 of every 10 years: the most likely fire season; below, how many months.',
    'clim.how.value.t': 'Each month', 'clim.how.value': 'share of years (2016–2025) with at least one fire detection in that month inside the hexagon, applied to 2026.',
    'clim.how.limits.t': 'Limits', 'clim.how.limits': 'a historical frequency: it does not use the Random Forest model and says nothing about how large a fire will be.',
    'soon.outlook': 'Fire Forecast 2026 appears here after its validation gate (hindcast 2021–2025 vs climatology). Until then the app shows history only.',
  },
  pt: {
    'nav.map': 'Abrir mapa', 'nav.home': 'Início', 'lang.switch': 'EN',
    'hero.title': 'O fogo deixa rastros. Transformamos 25 anos deles em um registro consistente.',
    'hero.text': 'O Fire Almanac harmoniza as detecções de fogo dos satélites MODIS e VIIRS da NASA (2000–2025) numa série única, para você ver onde e quando o fogo costuma aparecer perto de qualquer ponto do Brasil.',
    'hero.cta': 'Acessar o mapa',
    'hero.aria': 'Grade de hexágonos colorida pela atividade de fogo',
    'why.title': 'Quando o fogo é visto, já é tarde',
    'why.p1': 'Uma queimada que sai do controle destrói em horas o que a natureza levou décadas para formar. Cerrado, Pantanal e Amazônia perdem espécies, nascentes e solo. Comunidades respiram fumaça por semanas, e produtores veem safras e pastagens virarem cinza.',
    'why.p2': 'Saber <strong>onde e quando</strong> o fogo costuma aparecer muda o jogo. Brigadas posicionam equipes antes do pico, o poder público prioriza a fiscalização e quem planta e cria ajusta manejo e aceiros. Cada hora de antecedência economiza água, combustível, dinheiro e vidas.',
    'feat.title': 'O que você faz no Fire Almanac',
    'feat.hist.t': 'Um registro, quatro satélites',
    'feat.hist.p': 'Terra, Aqua, S-NPP e NOAA-20 enxergam o fogo de jeitos diferentes. Colocamos todos na mesma escala: o salto falso de 2012, da troca de satélite, some e as tendências reais ficam.',
    'feat.place.t': 'Seu lugar, seu período',
    'feat.place.p': 'Busque uma cidade, digite coordenadas ou clique no mapa e escolha qualquer período de 2000 a 2025 para ver o calendário de fogo da região.',
    'feat.outlook.t': 'Fire Forecast 2026',
    'feat.outlook.p': 'Chance de fogo acima do normal em cada mês de 2026. Só aparece depois de vencer a climatologia nos testes de 2021–2025.',
    'cta.title': 'Explore o fogo na sua região',
    'foot.data': 'Dados: NASA FIRMS, produtos de focos ativos MODIS Coleção 6.1 e VIIRS 375 m. Mapas © colaboradores do OpenStreetMap. · Top das Galáxias - 2026',

    'tab.aria': 'Modo de visualização', 'tab.history': 'Histórico', 'tab.timeline': 'Linha do tempo', 'tab.outlook': 'Previsão',
    'search.ph': 'Buscar cidade ou região…', 'search.aria': 'Buscar cidade ou região', 'search.none': 'Lugar não encontrado.',
    'loc.lat': 'Latitude', 'loc.lon': 'Longitude', 'loc.go': 'Ir',
    'f.from': 'De', 'f.to': 'Até', 'f.year': 'Ano', 'f.month': 'Mês', 'f.apply': 'Aplicar',
    'f.mode': 'Valores', 'f.harm': 'Harmonizado', 'f.raw': 'Bruto',
    'f.range': 'Dados de nov/2000 a dez/2025.',
    'f.err.order': '“De” precisa vir antes de “Até”.',
    'map.aria': 'Mapa do Brasil: clique para escolher um local',
    'map.zoom': 'Aproxime o mapa para ver o fogo por hexágono.',
    'map.loading': 'Carregando dados de fogo…',
    'map.legend': 'Detecções no período',
    'map.many': 'Área grande demais: aproxime um pouco mais.',
    'panel.empty': 'Escolha um local: busque, digite coordenadas ou clique no mapa.',
    'panel.loading': 'Carregando o histórico…',
    'panel.nofire': 'Nenhum foco detectado nesta região em 2000–2025.',
    'panel.error': 'Não foi possível carregar os dados:',
    'panel.outscope': 'Não foi possível carregar os dados fora do escopo.',
    'panel.area': 'Região · lat, lon', 'panel.sum': 'Resumo do período',
    'panel.period': 'Período', 'panel.harm': 'Detecções harmonizadas', 'panel.raw': 'Detecções brutas',
    'panel.harm.u': '(escala S-NPP)', 'panel.raw.u': '(contagem de cada satélite)',
    'panel.peak': 'Mês com mais fogo', 'panel.lowconf': 'Meses de baixa confiança',
    'cal.title': 'Calendário de fogo', 'cal.year': 'Ano', 'cal.legend': 'Detecções por mês',
    'draw.start': 'Desenhar área', 'draw.finish': 'Fechar área', 'draw.cancel': 'Cancelar',
    'draw.hint': 'Clique no mapa para marcar os cantos (pelo menos 3).',
    'draw.hint2': 'Duplo clique, Enter ou “Fechar área” para terminar. Esc cancela.',
    'draw.big': 'Área grande demais para o navegador (mais de ~16 blocos de dados). Desenhe uma área menor, como um município ou parte de um estado.',
    'panel.drawn': 'Área desenhada', 'panel.cells': 'hexágonos',
    'score.title': 'Fire Anomaly Score', 'score.median': 'a mediana', 'score.none': 'Sem fogo neste mês nem nos anos anteriores.',
    'band.extreme': 'Extremo', 'band.high': 'Muito acima do normal', 'band.above': 'Acima do normal', 'band.normal': 'Dentro do normal',
    'chance.of': 'de', 'chance.strip': 'Chance histórica de fogo acima do normal, por mês (últimos 10 anos)',
    'chance.leg': 'Anos acima do normal, de 10:', 'chance.leg.na': 'menos de 5 anos com fogo',
    'peak.title': 'Pico típico', 'peak.then': 'depois',
    'ind.years': 'anos', 'ind.insufficient': 'Dados insuficientes (menos de 5 anos com fogo).',
    'ind.how.title': 'Como ler os indicadores',
    'ind.how.harm': 'soma das detecções do período, convertidas para a escala do S-NPP: comparável entre satélites e anos.',
    'ind.how.raw': 'soma do que cada satélite contou, sem ajuste: a troca para o S-NPP em 2012 infla a contagem.',
    'ind.how.busiest': 'mês do período com mais detecções harmonizadas; abaixo, o valor e o satélite.',
    'ind.how.score': 'quão incomum foi o mês “Até” frente ao mesmo mês dos anos anteriores: percentil 0–100 (≥ 60 acima do normal · ≥ 85 muito acima · ≥ 95 extremo); “× a mediana” compara com o valor típico; “n anos” = anos comparados.',
    'ind.how.peak': 'mês que mais vezes foi o mais forte do ano (anos completos); “k de n anos” = quantas vezes; “depois” = 2º colocado.',
    'ind.how.base': 'Score e Pico típico usam a série harmonizada completa, não só o período escolhido.',
    'help.aria': 'O que este gráfico mostra?',
    'help.cal': '<ul><li><b>Linhas</b> = anos; <b>colunas</b> = meses do período escolhido.</li><li><b>Cor</b> = detecções no mês: azul-claro (pouco) → amarelo (muito); cinza = sem fogo.</li><li><b>○</b> = baixa confiança (nov/2000–jun/2002, só Terra).</li><li>Passe o mouse numa célula para ver harmonizado, bruto e satélite.</li><li>Alterne Harmonizado ↔ Bruto: o salto falso de 2012 aparece e some.</li></ul>',
    'help.chance': '<ul><li><b>Número grande</b> = em quantos dos últimos 10 anos completos{range} o mês ficou acima do normal.</li><li><b>Normal</b> = mediana daquele mês em todos os anos da série.</li><li>Frequência histórica, não previsão.</li></ul>',
    'help.tl': '<ul><li><b>Linha</b> = detecções por mês na área, de nov/2000 a dez/2025 (Harmonizado ou Bruto, conforme o filtro).</li><li><b>Faixas coloridas</b> = satélite de cada trecho: Terra → Aqua → S‑NPP. As emendas são as trocas de satélite.</li><li><b>Linha azul + ponto amarelo</b> = mês exibido; o mapa pinta os hexágonos da área nesse mês.</li><li>Clique ou arraste no gráfico para ir a um mês.</li></ul>',
    'help.clim': '<ul><li><b>Cada quadro</b> = um mês de 2026.</li><li><b>Número e barra</b> = fração dos anos (2016–2025) com pelo menos uma detecção de fogo naquele mês.</li><li>Passe o mouse num mês para ver o valor exato. Área desenhada = média dos seus hexágonos.</li></ul>',
    'csv.btn': 'Baixar CSV (período)',
    'soon.timeline': 'Série mensal com as emendas dos satélites (Terra → Aqua → S-NPP) — na próxima etapa.',
    'tl.cursor': 'Cursor de data (ano e mês)', 'tl.btn.prev': 'Mês anterior', 'tl.btn.next': 'Próximo mês', 'tl.btn.play': 'Reproduzir', 'tl.btn.pause': 'Pausar',
    'tl.edit': 'Alterar região', 'tl.edit.done': 'Voltar à região fixada',
    'tl.edit.hint': 'Clique no mapa, desenhe uma área ou busque um local. A Timeline recarrega com a nova região.',
    'tl.date': 'Mês exibido', 'tl.sum': 'Detecções na área',
    'tl.chart': 'Série mensal · emendas dos satélites',
    'tl.legend': 'Detecções por hexágono no mês', 'tl.legend.fixed': 'escala fixa, igual para todos os meses',
    'clim.title': 'Previsão climatológica 2026',
    'clim.avg': 'Média de',
    'clim.top': 'Maior chance no ano', 'clim.none': 'nenhum mês com fogo',
    'clim.high': 'Meses com 70% ou mais', 'clim.high.none': 'nenhum mês chega a 70%', 'clim.month': 'mês', 'clim.months': 'meses',
    'clim.leg': 'Fração dos anos com fogo:',
    'clim.how.title': 'Como ler a previsão',
    'clim.how.top': 'o maior percentual entre os 12 meses de 2026 e em que mês(es) ele ocorre.',
    'clim.how.high': 'meses com fogo em pelo menos 7 de cada 10 anos: a temporada de fogo mais provável; abaixo, quantos meses.',
    'clim.how.value.t': 'Cada mês', 'clim.how.value': 'fração dos anos (2016–2025) com pelo menos uma detecção de fogo naquele mês dentro do hexágono, aplicada a 2026.',
    'clim.how.limits.t': 'Limites', 'clim.how.limits': 'é uma frequência histórica: não usa o Random Forest e não diz o tamanho do fogo.',
    'soon.outlook': 'O Fire Forecast 2026 aparece aqui depois do portão de validação (hindcast 2021–2025 × climatologia). Até lá o app mostra só o histórico.',
  },
};

export const MONTHS = {
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  pt: ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'],
};

const KEY = 'fa-lang';
let current = pick();
const listeners = [];

function pick() {
  const q = new URLSearchParams(location.search).get('lang');
  if (q === 'pt' || q === 'en') return q;
  try { const s = localStorage.getItem(KEY); if (s === 'pt' || s === 'en') return s; } catch { /* sem storage */ }
  return 'en';
}

export const lang = () => current;
export const t = (k) => DICT[current][k] ?? DICT.en[k] ?? k;
export const monthName = (m) => MONTHS[current][m - 1];
export const ymLabel = (ym) => `${monthName(ym % 100)} ${Math.floor(ym / 100)}`;
export const fmt = (v) => v.toLocaleString(current === 'pt' ? 'pt-BR' : 'en-US', { maximumFractionDigits: v < 10 ? 1 : 0 });
export const onLang = (fn) => listeners.push(fn);

export function apply(root = document) {
  document.documentElement.lang = current === 'pt' ? 'pt-BR' : 'en';
  root.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll('[data-i18n-html]').forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  root.querySelectorAll('[data-i18n-ph]').forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
  root.querySelectorAll('[data-i18n-aria]').forEach((el) => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
}

export function setLang(l) {
  current = l;
  try { localStorage.setItem(KEY, l); } catch { /* sem storage */ }
  apply();
  listeners.forEach((fn) => fn(l));
}

/** Liga o botão de idioma (id="lang-toggle") e aplica os textos. */
export function initI18n() {
  apply();
  const b = document.getElementById('lang-toggle');
  if (b) b.addEventListener('click', () => setLang(current === 'en' ? 'pt' : 'en'));
}
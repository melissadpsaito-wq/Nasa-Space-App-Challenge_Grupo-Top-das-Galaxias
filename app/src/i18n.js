// Textos EN/PT (D46). Padrão: inglês (juízes); escolha guardada no navegador; ?lang=pt força.
// Marcação: data-i18n (texto), data-i18n-html (HTML), data-i18n-ph (placeholder), data-i18n-aria (aria-label).

const DICT = {
  en: {
    'nav.map': 'Open map', 'nav.home': 'Home', 'lang.switch': 'PT',
    'hero.title': 'Fire leaves a trail. We turned 25 years of it into one consistent record.',
    'hero.text': 'Fire Almanac harmonizes NASA MODIS and VIIRS satellite fire detections (2000–2025) into a single series, so you can see where and when fire usually happens around any point in Brazil — in hexagons about 17 km wide.',
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
    'feat.outlook.t': 'Fire Outlook 2026',
    'feat.outlook.p': 'Chance of above-normal fire for each month of 2026. Shown only after it beats climatology on 2021–2025 tests.',
    'cta.title': 'Explore fire in your region',
    'foot.data': 'Data: NASA FIRMS, MODIS Collection 6.1 and VIIRS 375 m active fire products. Maps © OpenStreetMap contributors.',

    'tab.aria': 'View mode', 'tab.history': 'History', 'tab.timeline': 'Timeline', 'tab.outlook': 'Outlook',
    'search.ph': 'Search a city or region…', 'search.aria': 'Search a city or region', 'search.none': 'Place not found.',
    'loc.lat': 'Latitude', 'loc.lon': 'Longitude', 'loc.go': 'Go',
    'f.from': 'From', 'f.to': 'To', 'f.year': 'Year', 'f.month': 'Month', 'f.apply': 'Apply',
    'f.mode': 'Values', 'f.harm': 'Harmonized', 'f.raw': 'Raw',
    'f.range': 'Data cover Nov 2000 – Dec 2025.',
    'f.err.order': '“From” must be before “To”.',
    'map.aria': 'Map of Brazil: click to choose a location',
    'map.zoom': 'Zoom in to see fire by hexagon (~17 km).',
    'map.loading': 'Loading fire data…',
    'map.legend': 'Detections in the period',
    'map.many': 'Area too large: zoom in a bit more.',
    'panel.empty': 'Choose a place: search, type coordinates or click the map.',
    'panel.loading': 'Loading fire record…',
    'panel.nofire': 'No fire detected in this region during 2000–2025.',
    'panel.error': 'Could not load data:',
    'panel.area': 'Region', 'panel.cell': 'H3 cell (~17 km)',
    'panel.period': 'Period', 'panel.harm': 'Harmonized detections', 'panel.raw': 'Raw detections',
    'panel.harm.u': '(S-NPP scale)', 'panel.raw.u': '(each satellite’s own count)',
    'panel.peak': 'Busiest month', 'panel.lowconf': 'Low-confidence months',
    'panel.note': 'Provisional harmonized series (M1, λ = 20); uncertainty bands come next. Values cover the whole ~17 km cell, not a single property.',
    'cal.title': 'Fire calendar', 'cal.year': 'Year', 'cal.legend': 'Detections per month',
    'cal.lowconf': '○ = low confidence', 'cal.toggle': 'Switch Harmonized ↔ Raw to see the false 2012 jump appear and disappear.',
    'soon.timeline': 'Monthly series with the satellite seams (Terra → Aqua → S-NPP) — coming next.',
    'soon.outlook': 'Fire Outlook 2026 appears here after its validation gate (hindcast 2021–2025 vs climatology). Until then the app shows history only.',
  },
  pt: {
    'nav.map': 'Abrir mapa', 'nav.home': 'Início', 'lang.switch': 'EN',
    'hero.title': 'O fogo deixa rastros. Transformamos 25 anos deles em um registro consistente.',
    'hero.text': 'O Fire Almanac harmoniza as detecções de fogo dos satélites MODIS e VIIRS da NASA (2000–2025) numa série única, para você ver onde e quando o fogo costuma aparecer perto de qualquer ponto do Brasil — em hexágonos de cerca de 17 km.',
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
    'feat.outlook.t': 'Fire Outlook 2026',
    'feat.outlook.p': 'Chance de fogo acima do normal em cada mês de 2026. Só aparece depois de vencer a climatologia nos testes de 2021–2025.',
    'cta.title': 'Explore o fogo na sua região',
    'foot.data': 'Dados: NASA FIRMS, produtos de focos ativos MODIS Coleção 6.1 e VIIRS 375 m. Mapas © colaboradores do OpenStreetMap.',

    'tab.aria': 'Modo de visualização', 'tab.history': 'Histórico', 'tab.timeline': 'Linha do tempo', 'tab.outlook': 'Previsão',
    'search.ph': 'Buscar cidade ou região…', 'search.aria': 'Buscar cidade ou região', 'search.none': 'Lugar não encontrado.',
    'loc.lat': 'Latitude', 'loc.lon': 'Longitude', 'loc.go': 'Ir',
    'f.from': 'De', 'f.to': 'Até', 'f.year': 'Ano', 'f.month': 'Mês', 'f.apply': 'Aplicar',
    'f.mode': 'Valores', 'f.harm': 'Harmonizado', 'f.raw': 'Bruto',
    'f.range': 'Dados de nov/2000 a dez/2025.',
    'f.err.order': '“De” precisa vir antes de “Até”.',
    'map.aria': 'Mapa do Brasil: clique para escolher um local',
    'map.zoom': 'Aproxime o mapa para ver o fogo por hexágono (~17 km).',
    'map.loading': 'Carregando dados de fogo…',
    'map.legend': 'Detecções no período',
    'map.many': 'Área grande demais: aproxime um pouco mais.',
    'panel.empty': 'Escolha um local: busque, digite coordenadas ou clique no mapa.',
    'panel.loading': 'Carregando o histórico…',
    'panel.nofire': 'Nenhum foco detectado nesta região em 2000–2025.',
    'panel.error': 'Não foi possível carregar os dados:',
    'panel.area': 'Região', 'panel.cell': 'célula H3 (~17 km)',
    'panel.period': 'Período', 'panel.harm': 'Detecções harmonizadas', 'panel.raw': 'Detecções brutas',
    'panel.harm.u': '(escala S-NPP)', 'panel.raw.u': '(contagem de cada satélite)',
    'panel.peak': 'Mês com mais fogo', 'panel.lowconf': 'Meses de baixa confiança',
    'panel.note': 'Série harmonizada provisória (M1, λ = 20); faixas de incerteza na próxima versão. Os valores valem para a célula de ~17 km, não para uma propriedade.',
    'cal.title': 'Calendário de fogo', 'cal.year': 'Ano', 'cal.legend': 'Detecções por mês',
    'cal.lowconf': '○ = baixa confiança', 'cal.toggle': 'Alterne Harmonizado ↔ Bruto para ver o salto falso de 2012 aparecer e sumir.',
    'soon.timeline': 'Série mensal com as emendas dos satélites (Terra → Aqua → S-NPP) — na próxima etapa.',
    'soon.outlook': 'O Fire Outlook 2026 aparece aqui depois do portão de validação (hindcast 2021–2025 × climatologia). Até lá o app mostra só o histórico.',
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

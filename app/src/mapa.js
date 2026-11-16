// Página do mapa (D46): visual do Samuel, sem backend. Lê os tiles harm_<pai res 2>.json direto no navegador.
import 'leaflet/dist/leaflet.css';
import './mapa.css';
import * as L from 'leaflet';
import * as Plot from '@observablehq/plot';
import { latLngToCell, cellToParent, cellToBoundary, polygonToCells, cellsToMultiPolygon, cellArea } from 'h3-js';
import { RES_PRODUCT, RES_TILE, TileStore, areaSeries, slicePeriod, periodIndex, cellTotals, summarize } from './data.js';
import { ClimaStore, areaClimatologia } from './climatologia.js';
import { initI18n, onLang, t, monthName, ymLabel, fmt } from './i18n.js';
import { renderCalendar, COLOR, MIN_SHOW } from './calendar.js';
import { fireScore, typicalPeak, chanceAllMonths, toCSV } from './analytics.js';
import {
  loadTimelineArea, freezeArea, describeMonth, indexFor, stepIndex, peakIndex, parseHash, formatHash, satLabel, scaleMax,
  satelliteSeams, timelineSeries, ymAtDate,
} from './timeline.js';

const FIRST = 200011, LAST = 202512;   // série nov/2000–dez/2025 (D33)
const MIN_ZOOM_HEX = 7;                // abaixo disso não desenha hexágonos (peso dos tiles)
const MAX_PARENTS = 12;                // ~12 tiles × ~1 MB no máximo por vista
const MAX_PARENTS_AREA = 16;           // área desenhada: até ~16 tiles (~um estado médio)
const store = new TileStore(import.meta.env.BASE_URL);
const climaStore = new ClimaStore(import.meta.env.BASE_URL);
const $ = (id) => document.getElementById(id);

// sel = { kind: 'point', lat, lon, cells: [cell] } | { kind: 'area', ring, cells }
const state = { from: FIRST, to: LAST, mode: 'harm', tab: 'history', sel: null, series: null, error: null, timeline: null, cursorYM: parseHash(location.hash) };

initI18n();

// ---------- filtros de período ----------
function fillSelects() {
  for (const id of ['from-year', 'to-year']) {
    const sel = $(id); const keep = sel.value; sel.replaceChildren();
    for (let y = 2000; y <= 2025; y++) sel.add(new Option(y, y));
    sel.value = keep || (id === 'from-year' ? '2000' : '2025');
  }
  for (const id of ['from-month', 'to-month']) {
    const sel = $(id); const keep = sel.value; sel.replaceChildren();
    for (let m = 1; m <= 12; m++) sel.add(new Option(monthName(m), m));
    sel.value = keep || (id === 'from-month' ? '11' : '12');
  }
}
fillSelects();

function readPeriod() {
  const from = Number($('from-year').value) * 100 + Number($('from-month').value);
  const to = Number($('to-year').value) * 100 + Number($('to-month').value);
  if (from > to) return { error: t('f.err.order') };
  return { from: Math.max(from, FIRST), to: Math.min(to, LAST) };
}

$('form-filtros').addEventListener('submit', (e) => {
  e.preventDefault();
  const p = readPeriod();
  const st = $('filtro-status');
  if (p.error) { st.textContent = p.error; st.className = 'erro'; return; }
  st.textContent = ''; st.className = '';
  Object.assign(state, p);
  refreshMap();
  renderPanel();
});

document.querySelectorAll('input[name="mode"]').forEach((r) => r.addEventListener('change', () => {
  state.mode = document.querySelector('input[name="mode"]:checked').value;
  refreshMap();
  renderPanel();
}));

// ---------- abas ----------
document.querySelectorAll('.btn-tab').forEach((b) => b.addEventListener('click', () => {
  document.querySelectorAll('.btn-tab').forEach((x) => { x.classList.toggle('active', x === b); x.setAttribute('aria-selected', x === b); });
  state.tab = b.dataset.modo;
  if (state.tab !== 'timeline' && parseHash(location.hash) != null) history.replaceState(null, '', location.pathname + location.search);
  renderPanel();
}));

// ---------- mapa ----------
// Vista presa ao Brasil: abre com o país inteiro centralizado, não deixa arrastar para fora e o zoom mínimo é o que mostra o Brasil todo.
const BR_BOUNDS = L.latLngBounds([[-34.0, -74.2], [5.6, -32.0]]);
const map = L.map('map', { zoomControl: false, preferCanvas: true, zoomSnap: 0.25, maxBounds: BR_BOUNDS.pad(0.06), maxBoundsViscosity: 1.0 })
  .setView([-14.2, -51.9], 4);
let brFitted = false;
function fitBrazil() {
  const sz = map.getSize();
  if (!sz.x || !sz.y) return;
  map.invalidateSize({ animate: false });
  map.setMinZoom(map.getBoundsZoom(BR_BOUNDS));
  if (!brFitted || map.getZoom() < map.getMinZoom()) { map.fitBounds(BR_BOUNDS, { animate: false }); brFitted = true; }
}
new ResizeObserver(fitBrazil).observe($('map'));
fitBrazil();
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 12, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);
const hexLayer = L.layerGroup().addTo(map);
let selLayer = null;
L.control.zoom({ position: 'bottomright' }).addTo(map);
const legendCtl = L.control({ position: 'bottomleft' });
legendCtl.onAdd = () => { const d = L.DomUtil.create('div', 'map-legend'); L.DomEvent.disableClickPropagation(d); return d; };
legendCtl.addTo(map);

let mapSeq = 0;
async function refreshMap() {
  if (timelineMapActive()) return; // na Timeline o mapa é pintado pelo cursor (syncTimelineMap)
  const my = ++mapSeq;
  const leg = document.querySelector('.map-legend');
  if (map.getZoom() < MIN_ZOOM_HEX) { hexLayer.clearLayers(); leg.textContent = t('map.zoom'); return; }
  const b = map.getBounds().pad(0.3);
  const ring = [[b.getSouth(), b.getWest()], [b.getSouth(), b.getEast()], [b.getNorth(), b.getEast()], [b.getNorth(), b.getWest()]];
  const parents = new Set(polygonToCells(ring, RES_TILE));
  ring.concat([[map.getCenter().lat, map.getCenter().lng]]).forEach(([a, c]) => parents.add(latLngToCell(a, c, RES_TILE)));
  if (parents.size > MAX_PARENTS) { hexLayer.clearLayers(); leg.textContent = t('map.many'); return; }
  leg.textContent = t('map.loading');
  let tiles;
  try { tiles = await Promise.all([...parents].map((p) => store.get(p))); } catch (err) { leg.textContent = `${t('panel.error')} ${err.message}`; return; }
  if (my !== mapSeq) return;

  const totals = new Map();
  for (const tile of tiles) {
    if (!tile) continue;
    const r = periodIndex(tile.months, state.from, state.to);
    if (!r) continue;
    for (const [c, v] of cellTotals(tile, r[0], r[1], state.mode === 'raw' ? 'raw' : 'cells')) if (v >= MIN_SHOW) totals.set(c, v);
  }
  const vals = [...totals.values()].sort((x, y) => x - y);
  const vmax = Math.max(1, vals[Math.floor(vals.length * 0.98)] ?? 1); // p98: um extremo não apaga o resto
  const scale = Plot.scale({ color: { ...COLOR, domain: [0, vmax], clamp: true } });

  hexLayer.clearLayers();
  for (const [c, v] of totals) {
    L.polygon(cellToBoundary(c), { stroke: false, fillColor: scale.apply(v), fillOpacity: 0.72, interactive: false }).addTo(hexLayer);
  }
  leg.replaceChildren();
  const cap = document.createElement('div');
  cap.textContent = `${t('map.legend')} (${state.mode === 'raw' ? t('f.raw') : t('f.harm')}) · ${ymLabel(state.from)} – ${ymLabel(state.to)}`;
  leg.append(cap, Plot.legend({ color: { ...COLOR, domain: [0, vmax] }, width: 220, ticks: 4, tickFormat: (d) => fmt(d) }));
}
map.on('moveend', refreshMap);

// ---------- seleção: ponto ou área (4.2) ----------
const wrapLon = (lng) => ((lng + 540) % 360) - 180;
let selSeq = 0;
async function loadSelection(sel, highlight) {
  const my = ++selSeq;
  Object.assign(state, { sel, series: null, error: null, timeline: null });
  if (selLayer) selLayer.remove();
  selLayer = L.layerGroup(highlight).addTo(map);
  renderPanel('loading');
  try {
    const s = await areaSeries(store, sel.cells, cellToParent);
    if (my !== selSeq) return;
    state.series = s;
  } catch (err) {
    if (my !== selSeq) return;
    state.error = err.message;
  }
  renderPanel();
}

function select(lat, lon) {
  const cell = latLngToCell(lat, lon, RES_PRODUCT);
  $('lat').value = lat.toFixed(4); $('lon').value = lon.toFixed(4);
  if (map.getZoom() < MIN_ZOOM_HEX) map.setView([lat, lon], 8); else map.panTo([lat, lon]);
  loadSelection({ kind: 'point', lat, lon, cells: [cell] }, [
    L.polygon(cellToBoundary(cell), { color: '#0b2540', weight: 3, fill: false }),
    L.circleMarker([lat, lon], { radius: 5, color: '#1769b5', weight: 2, fillColor: '#fff', fillOpacity: 1 }),
  ]);
}

/** ring = [[lat, lon], …] desenhado pelo usuário → células res 5 com centro dentro (área pequena: célula do centro). */
function selectArea(ring) {
  let cells = polygonToCells(ring, RES_PRODUCT);
  if (!cells.length) {
    const c = ring.reduce(([a, b], [x, y]) => [a + x / ring.length, b + y / ring.length], [0, 0]);
    cells = [latLngToCell(c[0], c[1], RES_PRODUCT)];
  }
  const parents = new Set(cells.map((c) => cellToParent(c, RES_TILE)));
  const shape = L.polygon(ring, { color: '#1769b5', weight: 2, dashArray: '5 4', fill: false });
  if (parents.size > MAX_PARENTS_AREA) {
    ++selSeq;
    Object.assign(state, { sel: null, series: null, error: null, timeline: null });
    if (selLayer) selLayer.remove();
    selLayer = L.layerGroup([shape]).addTo(map);
    $('panel').innerHTML = `<p class="panel-msg">${t('draw.big')}</p>`;
    return;
  }
  const km2 = cells.reduce((a, c) => a + cellArea(c, 'km2'), 0);
  map.fitBounds(shape.getBounds(), { maxZoom: 9, padding: [20, 20] });
  loadSelection({ kind: 'area', ring, cells, km2 }, [
    L.polygon(cellsToMultiPolygon(cells), { color: '#1769b5', weight: 2, fillOpacity: 0.05 }),
    shape,
  ]);
}

// ---------- desenho de área (cliques no mapa; sem leaflet-draw) ----------
const draw = { on: false, pts: [], layer: L.layerGroup().addTo(map) };
function drawRender() {
  draw.layer.clearLayers();
  if (draw.pts.length > 1) L.polyline(draw.pts.length > 2 ? [...draw.pts, draw.pts[0]] : draw.pts, { color: '#1769b5', weight: 2, dashArray: '5 4' }).addTo(draw.layer);
  draw.pts.forEach((p) => L.circleMarker(p, { radius: 4, color: '#1769b5', weight: 2, fillColor: '#fff', fillOpacity: 1, interactive: false }).addTo(draw.layer));
  $('draw-finish').disabled = draw.pts.length < 3;
  $('draw-hint').textContent = draw.on ? t(draw.pts.length < 3 ? 'draw.hint' : 'draw.hint2') : '';
}
function drawMode(on) {
  if (on && tlLocked()) setTlEdit(true); // desenhar na Timeline libera o mapa
  draw.on = on; draw.pts = [];
  map.getContainer().classList.toggle('drawing', on);
  if (on) map.doubleClickZoom.disable(); else if (!tlLocked()) map.doubleClickZoom.enable();
  $('draw-start').hidden = on; $('draw-finish').hidden = !on; $('draw-cancel').hidden = !on;
  drawRender();
}
function drawFinish() {
  if (draw.pts.length < 3) return;
  const ring = draw.pts.map((p) => [p.lat, wrapLon(p.lng)]);
  drawMode(false);
  selectArea(ring);
}
$('draw-start').addEventListener('click', () => drawMode(true));
$('draw-cancel').addEventListener('click', () => drawMode(false));
$('draw-finish').addEventListener('click', drawFinish);
document.addEventListener('keydown', (e) => {
  if (!draw.on) return;
  if (e.key === 'Escape') drawMode(false);
  if (e.key === 'Enter') { e.preventDefault(); drawFinish(); }
  if (e.key === 'Backspace' && document.activeElement === document.body) { draw.pts.pop(); drawRender(); }
});

map.on('click', (e) => {
  if (tlLocked()) return; // área fixada: clicar no mapa não troca a seleção (use "Alterar região")
  if (!draw.on) return select(e.latlng.lat, wrapLon(e.latlng.lng));
  const last = draw.pts.at(-1);
  if (last && map.latLngToContainerPoint(last).distanceTo(e.containerPoint) < 4) return; // 2º clique do duplo clique
  draw.pts.push(e.latlng);
  drawRender();
});
map.on('dblclick', () => { if (draw.on) drawFinish(); });

$('form-loc').addEventListener('submit', (e) => {
  e.preventDefault();
  const lat = Number(String($('lat').value).replace(',', '.'));
  const lon = Number(String($('lon').value).replace(',', '.'));
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) { $('lat').focus(); return; }
  select(lat, lon);
});

// ---------- busca (Nominatim, do Samuel) ----------
const input = $('search-input'), lista = $('autocomplete-list');
let debounce;
const buscar = (q) => fetch(`https://nominatim.openstreetmap.org/search?format=json&countrycodes=br&limit=8&accept-language=${document.documentElement.lang}&q=${encodeURIComponent(q)}`)
  .then((r) => r.json());
function sugestoes(lugares) {
  lista.replaceChildren();
  lugares.slice(0, 5).forEach((l) => {
    const li = document.createElement('li');
    li.textContent = l.display_name;
    li.tabIndex = 0;
    const go = () => { lista.style.display = 'none'; input.value = l.display_name; select(Number(l.lat), Number(l.lon)); };
    li.addEventListener('click', go);
    li.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    lista.append(li);
  });
  lista.style.display = lugares.length ? 'block' : 'none';
}
input.addEventListener('input', () => {
  clearTimeout(debounce);
  if (input.value.length < 3) { lista.style.display = 'none'; return; }
  debounce = setTimeout(() => buscar(input.value).then(sugestoes).catch(() => {}), 600);
});
input.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter') return;
  e.preventDefault(); lista.style.display = 'none';
  if (!input.value.trim()) return;
  buscar(input.value).then((r) => (r.length ? select(Number(r[0].lat), Number(r[0].lon)) : alert(t('search.none')))).catch(() => {});
});
document.addEventListener('click', (e) => { if (!input.contains(e.target) && !lista.contains(e.target)) lista.style.display = 'none'; });

// ---------- painel ----------
// "?" ao lado do título de cada gráfico (15/11 22:00): a explicação fica escondida até o clique (menos texto visível).
// Abre por cima do cartão; fecha no próprio "?", com Esc ou clicando fora. Um aberto por vez.
function chartHead(title, id, help) {
  return `<div class="chart-head"><h3 class="cal-title">${title}</h3>
    <button type="button" class="help-btn" aria-expanded="false" aria-controls="help-${id}" aria-label="${t('help.aria')}" title="${t('help.aria')}">?</button>
    <div id="help-${id}" class="help-pop" role="note" hidden>${help}</div></div>`;
}

function closeHelp(keep) {
  document.querySelectorAll('.help-btn[aria-expanded="true"]').forEach((b) => {
    if (b === keep) return;
    b.setAttribute('aria-expanded', 'false');
    const pop = $(b.getAttribute('aria-controls'));
    if (pop) pop.hidden = true;
  });
}
$('panel').addEventListener('click', (e) => { // delegação: o painel é refeito com innerHTML
  const b = e.target.closest('.help-btn');
  if (!b) return;
  const open = b.getAttribute('aria-expanded') !== 'true';
  closeHelp(b);
  b.setAttribute('aria-expanded', String(open));
  const pop = $(b.getAttribute('aria-controls'));
  if (pop) pop.hidden = !open;
});
document.addEventListener('click', (e) => { if (!e.target.closest('.help-btn, .help-pop')) closeHelp(); });
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  const b = document.querySelector('.help-btn[aria-expanded="true"]');
  if (b) { closeHelp(); b.focus(); }
});

function scoreKpi(sc) {
  const lab = `<span class="label">${t('score.title')} · ${ymLabel(sc.ym)}</span>`;
  if (sc.status === 'nodata') return `<div class="kpi">${lab}<b>—</b></div>`;
  if (sc.status === 'insufficient') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('ind.insufficient')}</span></div>`;
  if (sc.band === 'none') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('score.none')}</span></div>`;
  const ratio = sc.ratio == null ? '' : ` · ${fmt(sc.ratio)}× ${t('score.median')}`;
  return `<div class="kpi">${lab}<b>${sc.score}<small>/100</small></b>
    <span class="muted">${t(`band.${sc.band}`)}${ratio} · ${sc.years} ${t('ind.years')}</span></div>`;
}

function peakKpi(p) {
  const lab = `<span class="label">${t('peak.title')}</span>`;
  if (p.status !== 'ok') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('ind.insufficient')}</span></div>`;
  const second = p.second ? ` · ${t('peak.then')} ${monthName(p.second.month)} (${p.second.hits})` : '';
  return `<div class="kpi">${lab}<b>${monthName(p.month)}</b><span class="muted">${p.hits} ${t('chance.of')} ${p.years} ${t('ind.years')}${second}</span></div>`;
}

// Faixa dos 12 meses (D27): número grande = anos acima do normal; "/10" pequeno; legenda explica cores e "–".
function chanceStrip(all) {
  const ok = all.find((c) => c.status === 'ok');
  const cells = all.map((c) => {
    const isOk = c.status === 'ok';
    const v = isOk ? `${c.k}<small>/${c.n}</small>` : '–';
    const cls = !isOk ? 'na' : c.k >= 7 ? 'hi' : c.k >= 4 ? 'mid' : 'lo';
    const tip = `${monthName(c.month)}: ${isOk ? `${c.k} ${t('chance.of')} ${c.n} ${t('ind.years')}` : t('chance.leg.na')}`;
    return `<li class="${cls}" title="${tip}"><span>${monthName(c.month)}</span><b>${v}</b></li>`;
  }).join('');
  const help = t('help.chance').replace('{range}', ok ? ` (${ok.from}–${ok.to})` : '');
  return `${chartHead(t('chance.strip'), 'chance', help)}
    <ul class="chance-strip">${cells}</ul>
    <ul class="strip-legend"><li class="leg-cap">${t('chance.leg')}</li>
      <li><i class="hi"></i>7–10</li><li><i class="mid"></i>4–6</li><li><i class="lo"></i>0–3</li>
      <li><i class="na"></i>– ${t('chance.leg.na')}</li></ul>`;
}

/** "Como ler": definição curta de cada indicador, na ordem dos cartões; fechada por padrão (não empurra o calendário). */
function howTo(ref) {
  return `<details class="howto"><summary>${t('ind.how.title')}</summary><dl>
    <dt>${t('panel.harm')}</dt><dd>${t('ind.how.harm')}</dd>
    <dt>${t('panel.raw')}</dt><dd>${t('ind.how.raw')}</dd>
    <dt>${t('panel.peak')}</dt><dd>${t('ind.how.busiest')}</dd>
    <dt>${t('score.title')} · ${ymLabel(ref)}</dt><dd>${t('ind.how.score')}</dd>
    <dt>${t('peak.title')}</dt><dd>${t('ind.how.peak')}</dd>
    </dl><p class="muted">${t('ind.how.base')}</p></details>`;
}

function downloadCSV(s) {
  const sel = state.sel;
  const tag = sel.kind === 'point' ? `${sel.lat.toFixed(3)}_${sel.lon.toFixed(3)}` : `area_${sel.cells.length}cells`;
  const blob = new Blob([toCSV(s)], { type: 'text/csv;charset=utf-8' });
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `fire-almanac_${tag}_${s.months[0]}-${s.months.at(-1)}.csv` });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// Cabeçalho: só região (lat, lon ou área desenhada). O id H3 não aparece mais (pedido do Capitão, 15/11).
function regionHead(sel) {
  if (sel.kind === 'point') return `<div><span class="label">${t('panel.area')}</span>
      <strong>${sel.lat.toFixed(3)}, ${sel.lon.toFixed(3)}</strong></div>`;
  return `<div><span class="label">${t('panel.drawn')}</span>
      <strong>${sel.cells.length} ${t('panel.cells')} · ~${fmt(sel.km2)} km²</strong></div>`;
}

// ---------- previsão climatológica 2026 (aba Previsão) ----------
// Faixas da legenda; classifica pelo valor exibido (arredondado): 69,6% não aparece como "70%" em azul-claro.
const climaBand = (r) => (r >= 70 ? 'hi' : r >= 40 ? 'mid' : 'lo');

/** Meses seguidos viram "jul–out"; a faixa pode atravessar o ano ("dez–fev"). idx = 0..11. */
function monthRuns(idx) {
  const runs = [];
  for (const m of idx) {
    const last = runs.at(-1);
    if (last && m === last[1] + 1) last[1] = m; else runs.push([m, m]);
  }
  if (runs.length > 1 && runs[0][0] === 0 && runs.at(-1)[1] === 11) runs[0][0] = runs.pop()[0];
  return runs.map(([a, b]) => (a === b ? monthName(a + 1) : `${monthName(a + 1)}–${monthName(b + 1)}`)).join(', ');
}

// Resumo em 2 números: maior chance do ano (e em que meses) · meses na faixa alta (≥ 70%).
function climaKpis(pct) {
  const r = pct.map(Math.round);
  const max = Math.max(...r);
  const top = r.flatMap((v, i) => (v === max ? [i] : []));
  const high = r.flatMap((v, i) => (v >= 70 ? [i] : []));
  const n = high.length;
  return `<div class="kpis clima-kpis">
    <div class="kpi"><span class="label">${t('clim.top')}</span><b>${max}<small>%</small></b>
      <span class="muted">${max > 0 ? monthRuns(top) : t('clim.none')}</span></div>
    <div class="kpi"><span class="label">${t('clim.high')}</span><b>${n ? monthRuns(high) : '—'}</b>
      <span class="muted">${n ? `${n} ${t(n === 1 ? 'clim.month' : 'clim.months')}` : t('clim.high.none')}</span></div>
    </div>`;
}

// Faixa dos 12 meses: número grande + "%" pequeno + barra de 0 a 100%; legenda com as 3 faixas de cor.
function climaStrip(pct, nYears, single) {
  const cells = pct.map((p, i) => {
    const r = Math.round(p);
    const tip = single && nYears
      ? `${monthName(i + 1)}: ${Math.round((p * nYears) / 100)} ${t('chance.of')} ${nYears} ${t('ind.years')}`
      : `${monthName(i + 1)}: ${p.toFixed(1)}%`;
    return `<li class="${climaBand(r)}" style="--p:${(r / 100).toFixed(2)}" title="${tip}"><span>${monthName(i + 1)}</span><b>${r}<small>%</small></b></li>`;
  }).join('');
  return `<ul class="chance-strip clima-strip">${cells}</ul>
    <ul class="strip-legend"><li class="leg-cap">${t('clim.leg')}</li>
      <li><i class="hi"></i>70–100%</li><li><i class="mid"></i>40–69%</li><li><i class="lo"></i>0–39%</li></ul>`;
}

/** "Como ler a previsão": mesma caixa recolhível do Histórico, fechada por padrão. */
function climaHowTo() {
  return `<details class="howto"><summary>${t('clim.how.title')}</summary><dl>
    <dt>${t('clim.top')}</dt><dd>${t('clim.how.top')}</dd>
    <dt>${t('clim.high')}</dt><dd>${t('clim.how.high')}</dd>
    <dt>${t('clim.how.value.t')}</dt><dd>${t('clim.how.value')}</dd>
    <dt>${t('clim.how.limits.t')}</dt><dd>${t('clim.how.limits')}</dd>
    </dl><p class="muted">${t('soon.outlook')}</p></details>`;
}

let climaSeq = 0;
async function renderClima() {
  const el = $('panel');
  const sel = state.sel;
  if (!sel) { el.innerHTML = `<p class="panel-msg">${t('panel.empty')}</p>`; return; }
  const my = ++climaSeq;
  el.innerHTML = `<p class="panel-msg">${t('panel.loading')}</p>`;
  let c;
  try { c = await areaClimatologia(climaStore, sel.cells, cellToParent); } catch (err) {
    if (my === climaSeq) el.innerHTML = `<p class="panel-msg">${t('panel.error')} ${err.message}</p>`;
    return;
  }
  if (my !== climaSeq || state.tab !== 'outlook' || state.sel !== sel) return;
  if (c.outOfScope) { el.innerHTML = `<p class="panel-msg">${t('panel.outscope')}</p>`; return; }
  if (c.empty) { el.innerHTML = `<p class="panel-msg">${t('panel.nofire')}</p>`; return; }
  const avg = sel.kind === 'area' ? `<p class="muted card-sub">${t('clim.avg')} ${c.cellsTotal} ${t('panel.cells')}</p>` : '';
  el.innerHTML = `
    <div class="p-col"><div class="panel-head">${regionHead(sel)}</div></div>
    <div class="p-card p-w2 clima-card">
    ${chartHead(t('clim.title'), 'clim', t('help.clim'))}
    ${avg}
    ${climaKpis(c.pct)}
    ${climaStrip(c.pct, c.nYears, c.cellsTotal === 1)}
    ${climaHowTo()}
    </div>`;
}

// ---------- Timeline (4.4): área fixada + cursor de ano e mês ----------
let tlSeq = 0;
let tlFor = null; // seleção (state.sel) a que state.timeline pertence: mesma seleção = sem recarregar

const tlKey = () => (state.mode === 'raw' ? 'raw' : 'harm');
const tlIndex = (d) => (state.cursorYM == null
  ? peakIndex(d, tlKey()) // 1ª vez: começa no mês mais forte da área
  : indexFor(d.months, Math.floor(state.cursorYM / 100), state.cursorYM % 100));

function setCursor(i) {
  const d = state.timeline.data;
  state.cursorYM = d.months[Math.max(0, Math.min(d.months.length - 1, i))];
  paintCursor();
}

/** Atualiza só o que muda com o cursor (slider, seletores, números, hash); não refaz o painel. */
function paintCursor() {
  const tl = state.timeline, sl = $('tl-slider');
  if (!tl || !sl || state.tab !== 'timeline') return;
  const d = tl.data, i = tlIndex(d), m = describeMonth(d, i, tlKey());
  state.cursorYM = m.ym;
  sl.value = i;
  sl.setAttribute('aria-valuetext', ymLabel(m.ym));
  $('tl-year').value = Math.floor(m.ym / 100);
  $('tl-month').value = m.ym % 100;
  $('tl-date').textContent = ymLabel(m.ym);
  $('tl-sum').textContent = fmt(m.sum);
  renderTimelineChart();
  syncTimelineMap();
  try { history.replaceState(null, '', `#${formatHash(m.ym)}`); } catch { /* sem history */ }
}

function buildTimelineUI() {
  stopTlPlay(); // painel refeito (modo/idioma/área): o botão volta a Reproduzir
  const tl = state.timeline, d = tl.data, n = d.months.length;
  const modeLabel = t(state.mode === 'raw' ? 'f.raw' : 'f.harm');
  // Ordem pedida (15/11 21:18), 1 coluna: região → mês exibido + detecções → série mensal (com o cursor embaixo).
  // Saem "Hexágonos com fogo", "Satélite" (o gráfico já rotula os satélites) e a linha "Área fixada…".
  $('panel').innerHTML = `
    <div class="panel-head p-wide tl-head">
      ${regionHead(tl.sel)}
      <button type="button" id="tl-edit" class="btn-apply btn-outline"></button>
      <p id="tl-edit-hint" class="muted small tl-hint"></p>
    </div>
    <div class="kpis tl-readout p-wide">
      <div class="kpi"><span class="label">${t('tl.date')}</span><b id="tl-date">—</b></div>
      <div class="kpi"><span class="label">${t('tl.sum')} · ${modeLabel}</span><b id="tl-sum">—</b>
        <span class="muted">${t(state.mode === 'raw' ? 'panel.raw.u' : 'panel.harm.u')}</span></div>
    </div>
    <div class="p-card p-wide tl-card">
    ${chartHead(t('tl.chart'), 'tl', t('help.tl'))}
    <div id="tl-chart" class="tl-chart" role="img" aria-label="${t('tl.chart')}"></div>
    <div class="tl-controls">
      <button type="button" id="tl-prev" class="btn-apply btn-outline tl-step" aria-label="${t('tl.btn.prev')}">‹</button>
      <button type="button" id="tl-play" class="btn-apply btn-outline tl-step"></button>
      <input type="range" id="tl-slider" min="0" max="${n - 1}" step="1" value="0" aria-label="${t('tl.cursor')}">
      <button type="button" id="tl-next" class="btn-apply btn-outline tl-step" aria-label="${t('tl.btn.next')}">›</button>
    </div>
    <div class="tl-selects">
      <div class="field"><label for="tl-year">${t('f.year')}</label><select id="tl-year"></select></div>
      <div class="field"><label for="tl-month">${t('f.month')}</label><select id="tl-month"></select></div>
    </div>
    </div>`;
  const ys = $('tl-year'), ms = $('tl-month');
  for (let y = Math.floor(d.months[0] / 100); y <= Math.floor(d.months.at(-1) / 100); y++) ys.add(new Option(y, y));
  for (let mo = 1; mo <= 12; mo++) ms.add(new Option(monthName(mo), mo));
  $('tl-play').addEventListener('click', toggleTlPlay);
  $('tl-edit').addEventListener('click', () => setTlEdit(!tlEditing));
  $('tl-slider').addEventListener('input', (e) => { stopTlPlay(); setCursor(Number(e.target.value)); });
  $('tl-prev').addEventListener('click', () => { stopTlPlay(); setCursor(stepIndex(tlIndex(d), -1, n)); });
  $('tl-next').addEventListener('click', () => { stopTlPlay(); setCursor(stepIndex(tlIndex(d), 1, n)); });
  const fromSelects = () => stopTlPlay() || setCursor(indexFor(d.months, Number(ys.value), Number(ms.value)));
  ys.addEventListener('change', fromSelects);
  ms.addEventListener('change', fromSelects);
  const chart = $('tl-chart');
  chart.addEventListener('pointerdown', (e) => { chart.setPointerCapture?.(e.pointerId); onChartPointer(e); });
  chart.addEventListener('pointermove', (e) => { if (e.buttons) onChartPointer(e); });
  setPlayButton(false);
  syncTlEditUI();
  paintCursor();
  renderTimelineLegend(); // depende do modo e do idioma: refeita sempre que o painel é refeito
}

// ---------- Timeline: reproduzir (anima o cursor mês a mês, como no protótipo) ----------
const TL_PLAY_MS = 110; // ms por mês: a série inteira (302 meses) leva ~33 s
const ICON_PLAY = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M7 4v16l13-8z" fill="currentColor"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M6 4h4v16H6zM14 4h4v16h-4z" fill="currentColor"/></svg>';
let tlTimer = null;

function setPlayButton(playing) {
  const b = $('tl-play');
  if (!b) return;
  b.innerHTML = playing ? ICON_PAUSE : ICON_PLAY;
  b.setAttribute('aria-label', t(playing ? 'tl.btn.pause' : 'tl.btn.play'));
}

/** Idempotente. Chamada por qualquer ação manual no cursor, ao reconstruir o painel e ao sair da aba. */
function stopTlPlay() {
  if (tlTimer) { clearInterval(tlTimer); tlTimer = null; }
  setPlayButton(false);
}

function toggleTlPlay() {
  if (tlTimer) { stopTlPlay(); return; }
  const d = state.timeline?.data;
  if (!d) return;
  if (tlIndex(d) >= d.months.length - 1) setCursor(0); // no fim: recomeça do início
  setPlayButton(true);
  tlTimer = setInterval(() => {
    const dd = state.timeline?.data;
    if (!dd || state.tab !== 'timeline') { stopTlPlay(); return; }
    const i = tlIndex(dd);
    if (i >= dd.months.length - 1) { stopTlPlay(); return; }
    setCursor(i + 1);
  }, TL_PLAY_MS);
}

// ---------- Timeline: série mensal com emendas dos satélites (4.4, Parte 4) ----------
const TL_BAND = { TERRA: '#5aaee8', AQUA: '#2a6fb0', SNPP: '#f2c14e' }; // faixas sutis; o rótulo diz o satélite (nunca só a cor)

/** Refeito a cada mudança de cursor/modo: 302 pontos, barato. Só desenha; o estado vive em state.cursorYM. */
function renderTimelineChart() {
  const host = $('tl-chart'), tl = state.timeline;
  if (!host || !tl) return;
  const d = tl.data, key = tlKey(), series = timelineSeries(d, key), bands = satelliteSeams(d.months);
  const cur = series[tlIndex(d)];
  const ymax = Math.max(1, ...series.map((p) => p.value)) * 1.05;
  const plot = Plot.plot({
    width: host.clientWidth || 560, height: 190, marginTop: 20, marginBottom: 24, marginLeft: 8, marginRight: 8,
    style: { background: 'transparent', overflow: 'visible' },
    x: { type: 'utc', label: null, ticks: 6, tickFormat: '%Y' },
    y: { axis: null, domain: [0, ymax] },
    marks: [
      Plot.rectX(bands, { x1: 'x1', x2: 'x2', fill: (b) => TL_BAND[b.src], fillOpacity: 0.16 }),
      Plot.text(bands, { x: 'x1', text: (b) => satLabel(b.src), frameAnchor: 'top', textAnchor: 'start', dx: 4, dy: -14, fontSize: 11, fill: '#4a6580' }),
      Plot.lineY(series, { x: 'date', y: 'value', stroke: '#0b2540', strokeWidth: 1.4 }),
      ...(cur ? [
        Plot.ruleX([cur.date], { stroke: '#1769b5', strokeWidth: 2 }),
        Plot.dot([cur], { x: 'date', y: 'value', fill: '#f2c14e', stroke: '#1769b5', strokeWidth: 2, r: 4.5 }),
      ] : []),
      Plot.tip(series, Plot.pointerX({ x: 'date', y: 'value', title: (p) => `${ymLabel(p.ym)}\n${fmt(p.value)}` })),
    ],
  });
  host.replaceChildren(plot);
  host.__scale = plot.scale('x');
}

/** Ponteiro no gráfico (clique ou arrasto) → mês mais próximo → mesmo setCursor do slider (hash, KPIs e mapa seguem juntos). */
function onChartPointer(ev) {
  stopTlPlay();
  const host = ev.currentTarget, svg = host.querySelector('svg'), sc = host.__scale, d = state.timeline?.data;
  if (!svg || !sc || !d) return;
  const rect = svg.getBoundingClientRect();
  const px = (ev.clientX - rect.left) * ((Number(svg.getAttribute('width')) || rect.width) / rect.width); // compensa SVG redimensionado por CSS
  const [r0, r1] = sc.range, [d0, d1] = sc.domain.map((v) => +v);
  const frac = Math.min(1, Math.max(0, (px - r0) / (r1 - r0)));
  const ym = ymAtDate(new Date(d0 + frac * (d1 - d0)));
  setCursor(indexFor(d.months, Math.floor(ym / 100), ym % 100));
}

async function renderTimeline() {
  const el = $('panel');
  const sel = state.sel;
  if (!sel) { el.innerHTML = `<p class="panel-msg">${t('panel.empty')}</p>`; return; }
  if (state.timeline && tlFor === sel) { buildTimelineUI(); return; } // troca de modo/idioma: reaproveita a área fixada
  const my = ++tlSeq;
  el.innerHTML = `<p class="panel-msg">${t('panel.loading')}</p>`;
  let data;
  try { data = await loadTimelineArea(store, sel.cells, cellToParent); } catch (err) {
    if (my === tlSeq) el.innerHTML = `<p class="panel-msg">${t('panel.error')} ${err.message}</p>`;
    return;
  }
  if (my !== tlSeq || state.tab !== 'timeline' || state.sel !== sel) return;
  if (data.empty) { state.timeline = null; el.innerHTML = `<p class="panel-msg">${t(data.outOfScope ? 'panel.outscope' : 'panel.nofire')}</p>`; return; }
  state.timeline = freezeArea(sel, data); // área fixa: o cursor só mexe no mês
  tlFor = sel;
  buildTimelineUI();
}


// ---------- Timeline: hexágonos da área pintados pelo mês do cursor ----------
// Escala fixa (p98 de todos os meses da área): meses diferentes ficam comparáveis. Polígonos criados uma vez por
// área fixada; mexer no cursor só troca a cor (setStyle).
let tlMap = null; // { src, layer, polys, scales: { harm, raw } }
const TL_NONE = { fillColor: '#9fb6cc', fillOpacity: 0.18 }; // hexágono da área sem fogo no mês (< MIN_SHOW)

function timelineMapActive() { return state.tab === 'timeline' && Boolean(state.timeline); }

function tlScale() {
  const key = tlKey();
  if (!tlMap.scales[key]) {
    const vmax = scaleMax(state.timeline.data, key);
    tlMap.scales[key] = { vmax, scale: Plot.scale({ color: { ...COLOR, domain: [0, vmax], clamp: true } }) };
  }
  return tlMap.scales[key];
}

function paintTimelineMap() {
  const d = state.timeline.data, i = tlIndex(d), key = tlKey(), { scale } = tlScale();
  tlMap.polys.forEach((p, k) => {
    const v = d.cells[k][key][i];
    p.setStyle(v < MIN_SHOW ? TL_NONE : { fillColor: scale.apply(v), fillOpacity: 0.72 });
  });
}

/** Liga/desliga o mapa da Timeline conforme aba e área fixada; idempotente. */
// Na Timeline o mapa fica travado na área fixada, centralizada: só o cursor se mexe, os hexágonos é que variam.
const MAP_HANDLERS = ['dragging', 'touchZoom', 'doubleClickZoom', 'scrollWheelZoom', 'boxZoom', 'keyboard'];
let tlPrevView = null; // vista do mapa antes de travar, para devolver ao sair da aba

function fitTimelineMap() {
  if (!tlMap) return;
  map.invalidateSize({ animate: false }); // o painel pode ter mudado o tamanho do contêiner
  const b = tlMap.polys[0].getBounds();
  tlMap.polys.forEach((p) => b.extend(p.getBounds()));
  map.fitBounds(b, { padding: [24, 24], maxZoom: 10, animate: false });
}

let tlEditing = false; // modo "Alterar região": mapa solto para clicar, desenhar, arrastar; a Timeline segue na área antiga até a nova carregar
const tlLocked = () => Boolean(tlMap) && !tlEditing;

function setMapLocked(locked) {
  MAP_HANDLERS.forEach((h) => map[h][locked ? 'disable' : 'enable']());
  $('map').classList.toggle('tl-locked', locked);
}

/** Texto do botão e da dica conforme o modo; seguro de chamar com o painel ausente. */
function syncTlEditUI() {
  const b = $('tl-edit'), hint = $('tl-edit-hint');
  if (b) b.textContent = t(tlEditing ? 'tl.edit.done' : 'tl.edit');
  if (hint) hint.textContent = tlEditing ? t('tl.edit.hint') : '';
}

function setTlEdit(on) {
  if (!tlMap || on === tlEditing) return;
  if (!on && draw.on) drawMode(false);
  stopTlPlay();
  tlEditing = on;
  setMapLocked(!on);
  if (!on) fitTimelineMap(); // voltar à região fixada: reenquadra
  syncTlEditUI();
}

function lockTimelineMap() {
  if (!tlPrevView) tlPrevView = { center: map.getCenter(), zoom: map.getZoom() };
  tlEditing = false; // área nova carregada: sai do modo de edição
  setMapLocked(true);
  fitTimelineMap();
  syncTlEditUI();
}

function unlockTimelineMap(restore) {
  tlEditing = false;
  setMapLocked(false);
  if (restore && tlPrevView) map.setView(tlPrevView.center, tlPrevView.zoom, { animate: false });
  if (restore) tlPrevView = null; // trocar só a seleção (restore = false) mantém a vista original para devolver ao sair da aba
}
window.addEventListener('resize', () => { if (tlLocked()) fitTimelineMap(); });

function syncTimelineMap() {
  if (!timelineMapActive()) {
    stopTlPlay();
    if (!tlMap) { if (tlPrevView && state.tab !== 'timeline') unlockTimelineMap(true); return; }
    tlMap.layer.remove();
    tlMap = null;
    unlockTimelineMap(state.tab !== 'timeline'); // trocou de aba: devolve a vista; trocou só a seleção: deixa a nova
    map.addLayer(hexLayer);
    refreshMap(); // volta o mapa do período
    return;
  }
  if (!tlMap || tlMap.src !== state.timeline) {
    if (tlMap) tlMap.layer.remove(); else map.removeLayer(hexLayer);
    mapSeq++; // descarta um refreshMap ainda em andamento
    const layer = L.layerGroup().addTo(map);
    const polys = state.timeline.data.cells.map((c) => L.polygon(cellToBoundary(c.id), { stroke: false, fillOpacity: 0.72, interactive: false }).addTo(layer));
    tlMap = { src: state.timeline, layer, polys, scales: {} };
    lockTimelineMap();
    if (selLayer) selLayer.eachLayer((l) => l.bringToFront?.()); // contorno da área por cima da cor
  }
  paintTimelineMap();
}

function renderTimelineLegend() {
  const leg = document.querySelector('.map-legend');
  if (!leg || !tlMap) return;
  leg.replaceChildren();
  const cap = document.createElement('div');
  cap.textContent = `${t('tl.legend')} (${t(state.mode === 'raw' ? 'f.raw' : 'f.harm')}) · ${t('tl.legend.fixed')}`;
  leg.append(cap, Plot.legend({ color: { ...COLOR, domain: [0, tlScale().vmax] }, width: 220, ticks: 4, tickFormat: (v) => fmt(v) }));
}

// colar/editar "#t=AAAA-MM" na URL move o cursor (replaceState em paintCursor não dispara este evento)
window.addEventListener('hashchange', () => {
  const ym = parseHash(location.hash);
  if (ym == null || state.tab !== 'timeline' || !state.timeline) return;
  stopTlPlay();
  state.cursorYM = ym;
  paintCursor();
});

function renderPanel(status) {
  syncTimelineMap();
  const el = $('panel');
  const msg = (k, extra = '') => { el.innerHTML = `<p class="panel-msg">${t(k)} ${extra}</p>`; };
  if (state.tab === 'timeline') return status === 'loading' ? msg('panel.loading') : renderTimeline();
  if (state.tab === 'outlook') return status === 'loading' ? msg('panel.loading') : renderClima();
  if (status === 'loading') return msg('panel.loading');
  if (state.error) return msg('panel.error', state.error);
  if (!state.sel) return msg('panel.empty');
  if (state.series?.outOfScope) return msg('panel.outscope'); // nenhum tile: ponto/área fora do Brasil
  if (!state.series || state.series.empty) {
    const dev = import.meta.env.DEV ? `<br><small>(dev: harm_${cellToParent(state.sel.cells[0], RES_TILE)}.json em app/public/data/?)</small>` : '';
    return msg('panel.nofire', dev);
  }
  const full = state.series;
  const s = slicePeriod(full, state.from, state.to);
  const r = summarize(s);
  if (!r) return msg('panel.nofire');
  // Indicadores (D25, D27): série completa, harmonizada e mensal; o mês de referência é o "Até" do período.
  const ref = r.last;
  const sc = fireScore(full, ref);
  // Ordem pedida (15/11): 1) dados isolados (KPIs) · 2) calendário de fogo · 3) chance histórica. Tudo em 1 coluna.
  el.innerHTML = `
    <div class="panel-head p-wide">
      ${regionHead(state.sel)}
      <div><span class="label">${t('panel.period')}</span><strong>${ymLabel(r.first)} – ${ymLabel(r.last)}</strong></div>
    </div>
    <section class="p-wide" aria-label="${t('panel.sum')}">
    <div class="kpis k3">
      <div class="kpi"><span class="label">${t('panel.harm')}</span><b>${fmt(r.totalHarm)}</b><span class="muted">${t('panel.harm.u')}</span></div>
      <div class="kpi"><span class="label">${t('panel.raw')}</span><b>${fmt(r.totalRaw)}</b><span class="muted">${t('panel.raw.u')}</span></div>
      <div class="kpi"><span class="label">${t('panel.peak')}</span><b>${ymLabel(r.peak.ym)}</b><span class="muted">${fmt(r.peak.value)} · ${r.peak.src}</span></div>
      ${scoreKpi(sc)}
      ${peakKpi(typicalPeak(full))}
    </div>
    ${howTo(ref)}
    </section>
    <div class="p-card p-wide">
    ${chartHead(`${t('cal.title')} · ${state.mode === 'raw' ? t('f.raw') : t('f.harm')}`, 'cal', t('help.cal'))}
    <div id="calendar" class="calendar"></div>
    </div>
    <div class="p-card p-wide chance-card">
    ${chanceStrip(chanceAllMonths(full))}
    </div>
    <button type="button" id="csv-btn" class="btn-apply btn-navy btn-csv p-wide">${t('csv.btn')}</button>`;
  renderCalendar($('calendar'), s, state.mode);
  $('csv-btn').addEventListener('click', () => downloadCSV(s));
}

onLang(() => { fillSelects(); $('filtro-status').textContent = ''; drawRender(); refreshMap(); renderPanel(); });
renderPanel();
refreshMap();
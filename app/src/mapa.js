// Página do mapa (D46): visual do Samuel, sem backend. Lê os tiles harm_<pai res 2>.json direto no navegador.
import 'leaflet/dist/leaflet.css';
import './mapa.css';
import * as L from 'leaflet';
import * as Plot from '@observablehq/plot';
import { latLngToCell, cellToParent, cellToBoundary, polygonToCells } from 'h3-js';
import { RES_PRODUCT, RES_TILE, TileStore, areaSeries, slicePeriod, periodIndex, cellTotals, summarize } from './data.js';
import { initI18n, onLang, t, monthName, ymLabel, fmt } from './i18n.js';
import { renderCalendar, COLOR, MIN_SHOW } from './calendar.js';

const FIRST = 200011, LAST = 202512;   // série nov/2000–dez/2025 (D33)
const MIN_ZOOM_HEX = 7;                // abaixo disso não desenha hexágonos (peso dos tiles)
const MAX_PARENTS = 12;                // ~12 tiles × ~1 MB no máximo por vista
const store = new TileStore(import.meta.env.BASE_URL);
const $ = (id) => document.getElementById(id);

const state = { from: FIRST, to: LAST, mode: 'harm', tab: 'history', cell: null, lat: null, lon: null, series: null, error: null };

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
  renderPanel();
}));

// ---------- mapa ----------
const map = L.map('map', { preferCanvas: true, minZoom: 3, maxBounds: [[-60, -100], [20, -10]], maxBoundsViscosity: 0.8 })
  .setView([-14.2, -51.9], 4);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 12, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);
const hexLayer = L.layerGroup().addTo(map);
let selLayer = null;
const legendCtl = L.control({ position: 'bottomright' });
legendCtl.onAdd = () => { const d = L.DomUtil.create('div', 'map-legend'); L.DomEvent.disableClickPropagation(d); return d; };
legendCtl.addTo(map);

let mapSeq = 0;
async function refreshMap() {
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
  leg.append(cap, Plot.legend({ color: { ...COLOR, domain: [0, vmax] }, width: 220, tickFormat: (d) => fmt(d) }));
}
map.on('moveend', refreshMap);

// ---------- seleção de local ----------
let selSeq = 0;
async function select(lat, lon) {
  const my = ++selSeq;
  Object.assign(state, { lat, lon, cell: latLngToCell(lat, lon, RES_PRODUCT), series: null, error: null });
  $('lat').value = lat.toFixed(4); $('lon').value = lon.toFixed(4);
  if (selLayer) selLayer.remove();
  selLayer = L.layerGroup([
    L.polygon(cellToBoundary(state.cell), { color: '#ff5a1f', weight: 3, fill: false }),
    L.circleMarker([lat, lon], { radius: 5, color: '#0b2545', weight: 2, fillColor: '#fff', fillOpacity: 1 }),
  ]).addTo(map);
  if (map.getZoom() < MIN_ZOOM_HEX) map.setView([lat, lon], 8); else map.panTo([lat, lon]);
  renderPanel('loading');
  try {
    const s = await areaSeries(store, [state.cell], cellToParent);
    if (my !== selSeq) return;
    state.series = s;
  } catch (err) {
    if (my !== selSeq) return;
    state.error = err.message;
  }
  renderPanel();
}

map.on('click', (e) => select(e.latlng.lat, ((e.latlng.lng + 540) % 360) - 180));

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
function renderPanel(status) {
  const el = $('panel');
  const msg = (k, extra = '') => { el.innerHTML = `<p class="panel-msg">${t(k)} ${extra}</p>`; };
  if (state.tab === 'timeline') return msg('soon.timeline');
  if (state.tab === 'outlook') return msg('soon.outlook');
  if (status === 'loading') return msg('panel.loading');
  if (state.error) return msg('panel.error', state.error);
  if (!state.cell) return msg('panel.empty');
  if (!state.series || state.series.empty) {
    const dev = import.meta.env.DEV ? `<br><small>(dev: harm_${cellToParent(state.cell, RES_TILE)}.json em app/public/data/?)</small>` : '';
    return msg('panel.nofire', dev);
  }
  const s = slicePeriod(state.series, state.from, state.to);
  const r = summarize(s);
  if (!r) return msg('panel.nofire');
  const lowConf = s.low_conf.reduce((a, b) => a + b, 0);
  el.innerHTML = `
    <div class="panel-head">
      <div><span class="label">${t('panel.area')}</span>
        <strong>${state.lat.toFixed(3)}, ${state.lon.toFixed(3)}</strong>
        <span class="muted">${t('panel.cell')} <code>${state.cell}</code></span></div>
      <div><span class="label">${t('panel.period')}</span><strong>${ymLabel(r.first)} – ${ymLabel(r.last)}</strong></div>
    </div>
    <div class="kpis">
      <div class="kpi ${state.mode === 'harm' ? 'on' : ''}"><span class="label">${t('panel.harm')}</span><b>${fmt(r.totalHarm)}</b><span class="muted">${t('panel.harm.u')}</span></div>
      <div class="kpi ${state.mode === 'raw' ? 'on' : ''}"><span class="label">${t('panel.raw')}</span><b>${fmt(r.totalRaw)}</b><span class="muted">${t('panel.raw.u')}</span></div>
      <div class="kpi"><span class="label">${t('panel.peak')}</span><b>${ymLabel(r.peak.ym)}</b><span class="muted">${fmt(r.peak.value)} · ${r.peak.src}</span></div>
      ${lowConf ? `<div class="kpi"><span class="label">${t('panel.lowconf')}</span><b>${lowConf}</b></div>` : ''}
    </div>
    <h3 class="cal-title">${t('cal.title')} · ${state.mode === 'raw' ? t('f.raw') : t('f.harm')}</h3>
    <div id="calendar" class="calendar"></div>
    <p class="muted small">${t('cal.lowconf')} · ${t('cal.toggle')}</p>
    <p class="note">${t('panel.note')}</p>`;
  renderCalendar($('calendar'), s, state.mode);
}

onLang(() => { fillSelects(); $('filtro-status').textContent = ''; refreshMap(); renderPanel(); });
renderPanel();
refreshMap();

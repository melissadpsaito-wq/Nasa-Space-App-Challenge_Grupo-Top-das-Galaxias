// Página do mapa (D46): visual do Samuel, sem backend. Lê os tiles harm_<pai res 2>.json direto no navegador.
import 'leaflet/dist/leaflet.css';
import './mapa.css';
import * as L from 'leaflet';
import * as Plot from '@observablehq/plot';
import { latLngToCell, cellToParent, cellToBoundary, polygonToCells, cellsToMultiPolygon, cellArea } from 'h3-js';
import { RES_PRODUCT, RES_TILE, TileStore, areaSeries, slicePeriod, periodIndex, cellTotals, summarize } from './data.js';
import { initI18n, onLang, t, monthName, ymLabel, fmt } from './i18n.js';
import { renderCalendar, COLOR, MIN_SHOW } from './calendar.js';
import { fireScore, typicalPeak, historicalChance, chanceAllMonths, toCSV } from './analytics.js';
import { ForecastStore, areaOutlook, gateStatus, outlookSummary } from './forecast.js';

const FIRST = 200011, LAST = 202512;   // série nov/2000–dez/2025 (D33)
const MIN_ZOOM_HEX = 7;                // abaixo disso não desenha hexágonos (peso dos tiles)
const MAX_PARENTS = 12;                // ~12 tiles × ~1 MB no máximo por vista
const MAX_PARENTS_AREA = 16;           // área desenhada: até ~16 tiles (~um estado médio)
const store = new TileStore(import.meta.env.BASE_URL);
const fstore = new ForecastStore(import.meta.env.BASE_URL);   // Fire Outlook 2026 (D35, D48)
// Só no `npm run dev`: ?force-outlook mostra o Outlook mesmo reprovado no portão (para conferir a tela; nunca no site).
const FORCE_OUTLOOK = import.meta.env.DEV && new URLSearchParams(location.search).has('force-outlook');
const $ = (id) => document.getElementById(id);

// sel = { kind: 'point', lat, lon, cells: [cell] } | { kind: 'area', ring, cells }
const state = { from: FIRST, to: LAST, mode: 'harm', tab: 'history', sel: null, series: null, error: null,
  fc: null, fcSel: null, fcErr: null, skill: undefined };

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
  if (state.tab === 'outlook') loadOutlook();
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

// ---------- seleção: ponto ou área (4.2) ----------
const wrapLon = (lng) => ((lng + 540) % 360) - 180;
let selSeq = 0;
async function loadSelection(sel, highlight) {
  const my = ++selSeq;
  Object.assign(state, { sel, series: null, error: null });
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
  if (state.tab === 'outlook') loadOutlook();
}

// ---------- Fire Outlook 2026 (D35, D48): carrega só quando a aba é aberta ----------
let fcSeq = 0;
async function loadOutlook() {
  const sel = state.sel;
  if (!sel || state.fcSel === sel) return;
  const my = ++fcSeq;
  Object.assign(state, { fc: null, fcSel: sel, fcErr: null });
  renderPanel();
  try {
    const [skill, fc] = await Promise.all([fstore.skill(), areaOutlook(fstore, sel.cells, cellToParent, RES_TILE)]);
    if (my !== fcSeq) return;
    Object.assign(state, { skill, fc });
  } catch (err) {
    if (my !== fcSeq) return;
    state.fcErr = err.message;
  }
  renderPanel();
}

function select(lat, lon) {
  const cell = latLngToCell(lat, lon, RES_PRODUCT);
  $('lat').value = lat.toFixed(4); $('lon').value = lon.toFixed(4);
  if (map.getZoom() < MIN_ZOOM_HEX) map.setView([lat, lon], 8); else map.panTo([lat, lon]);
  loadSelection({ kind: 'point', lat, lon, cells: [cell] }, [
    L.polygon(cellToBoundary(cell), { color: '#ff5a1f', weight: 3, fill: false }),
    L.circleMarker([lat, lon], { radius: 5, color: '#0b2545', weight: 2, fillColor: '#fff', fillOpacity: 1 }),
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
  const shape = L.polygon(ring, { color: '#0b2545', weight: 2, dashArray: '5 4', fill: false });
  if (parents.size > MAX_PARENTS_AREA) {
    ++selSeq;
    Object.assign(state, { sel: null, series: null, error: null });
    if (selLayer) selLayer.remove();
    selLayer = L.layerGroup([shape]).addTo(map);
    $('panel').innerHTML = `<p class="panel-msg">${t('draw.big')}</p>`;
    return;
  }
  const km2 = cells.reduce((a, c) => a + cellArea(c, 'km2'), 0);
  map.fitBounds(shape.getBounds(), { maxZoom: 9, padding: [20, 20] });
  loadSelection({ kind: 'area', ring, cells, km2 }, [
    L.polygon(cellsToMultiPolygon(cells), { color: '#ff5a1f', weight: 2, fillOpacity: 0.05 }),
    shape,
  ]);
}

// ---------- desenho de área (cliques no mapa; sem leaflet-draw) ----------
const draw = { on: false, pts: [], layer: L.layerGroup().addTo(map) };
function drawRender() {
  draw.layer.clearLayers();
  if (draw.pts.length > 1) L.polyline(draw.pts.length > 2 ? [...draw.pts, draw.pts[0]] : draw.pts, { color: '#0b2545', weight: 2, dashArray: '5 4' }).addTo(draw.layer);
  draw.pts.forEach((p) => L.circleMarker(p, { radius: 4, color: '#0b2545', weight: 2, fillColor: '#fff', fillOpacity: 1, interactive: false }).addTo(draw.layer));
  $('draw-finish').disabled = draw.pts.length < 3;
  $('draw-hint').textContent = draw.on ? t(draw.pts.length < 3 ? 'draw.hint' : 'draw.hint2') : '';
}
function drawMode(on) {
  draw.on = on; draw.pts = [];
  map.getContainer().classList.toggle('drawing', on);
  if (on) map.doubleClickZoom.disable(); else map.doubleClickZoom.enable();
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
const BAND_CLASS = { extreme: 'b-extreme', high: 'b-high', above: 'b-above', normal: 'b-normal', none: 'b-normal' };

function scoreKpi(sc) {
  const lab = `<span class="label">${t('score.title')} · ${ymLabel(sc.ym)}</span>`;
  if (sc.status === 'nodata') return `<div class="kpi">${lab}<b>—</b></div>`;
  if (sc.status === 'insufficient') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('ind.insufficient')}</span></div>`;
  if (sc.band === 'none') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('score.none')}</span></div>`;
  const ratio = sc.ratio == null ? '' : ` · ${fmt(sc.ratio)}× ${t('score.median')}`;
  return `<div class="kpi score ${BAND_CLASS[sc.band]}">${lab}<b>${sc.score}<small>/100</small></b>
    <span class="muted">${t(`band.${sc.band}`)}${ratio} · ${sc.years} ${t('ind.years')}</span></div>`;
}

function chanceKpi(c) {
  const lab = `<span class="label">${t('chance.title')} · ${monthName(c.month)}</span>`;
  if (c.status !== 'ok') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('ind.insufficient')}</span></div>`;
  return `<div class="kpi">${lab}<b>${c.pct}%</b><span class="muted">${c.k} ${t('chance.of')} ${c.n} ${t('ind.years')} (${c.from}–${c.to})</span></div>`;
}

function peakKpi(p) {
  const lab = `<span class="label">${t('peak.title')}</span>`;
  if (p.status !== 'ok') return `<div class="kpi">${lab}<b>—</b><span class="muted">${t('ind.insufficient')}</span></div>`;
  const second = p.second ? ` · ${t('peak.then')} ${monthName(p.second.month)} (${p.second.hits})` : '';
  return `<div class="kpi">${lab}<b>${monthName(p.month)}</b><span class="muted">${p.hits} ${t('chance.of')} ${p.years} ${t('ind.years')}${second}</span></div>`;
}

function chanceStrip(all) {
  const cells = all.map((c) => {
    const v = c.status === 'ok' ? `${c.k}/${c.n}` : '–';
    const cls = c.status !== 'ok' ? 'na' : c.k >= 7 ? 'hi' : c.k >= 4 ? 'mid' : 'lo';
    return `<li class="${cls}" title="${monthName(c.month)}: ${c.status === 'ok' ? `${c.k} ${t('chance.of')} ${c.n}` : t('ind.insufficient')}"><span>${monthName(c.month)}</span><b>${v}</b></li>`;
  }).join('');
  return `<h3 class="cal-title">${t('chance.strip')}</h3><ul class="chance-strip">${cells}</ul>`;
}

function downloadCSV(s) {
  const sel = state.sel;
  const tag = sel.kind === 'point' ? `${sel.lat.toFixed(3)}_${sel.lon.toFixed(3)}` : `area_${sel.cells.length}cells`;
  const blob = new Blob([toCSV(s)], { type: 'text/csv;charset=utf-8' });
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `fire-almanac_${tag}_${s.months[0]}-${s.months.at(-1)}.csv` });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function regionHead(sel) {
  if (sel.kind === 'point') return `<div><span class="label">${t('panel.area')}</span>
      <strong>${sel.lat.toFixed(3)}, ${sel.lon.toFixed(3)}</strong>
      <span class="muted">${t('panel.cell')} <code>${sel.cells[0]}</code></span></div>`;
  return `<div><span class="label">${t('panel.drawn')}</span>
      <strong>${sel.cells.length} ${t('panel.cells')} · ~${fmt(sel.km2)} km²</strong>
      <span class="muted">${t('panel.drawn.u')}</span></div>`;
}

function renderPanel(status) {
  const el = $('panel');
  const msg = (k, extra = '') => { el.innerHTML = `<p class="panel-msg">${t(k)} ${extra}</p>`; };
  if (state.tab === 'timeline') return msg('soon.timeline');
  if (state.tab === 'outlook') return renderOutlook(el, msg, status);
  if (status === 'loading') return msg('panel.loading');
  if (state.error) return msg('panel.error', state.error);
  if (!state.sel) return msg('panel.empty');
  if (!state.series || state.series.empty) {
    const dev = import.meta.env.DEV ? `<br><small>(dev: harm_${cellToParent(state.sel.cells[0], RES_TILE)}.json em app/public/data/?)</small>` : '';
    return msg('panel.nofire', dev);
  }
  const full = state.series;
  const s = slicePeriod(full, state.from, state.to);
  const r = summarize(s);
  if (!r) return msg('panel.nofire');
  const lowConf = s.low_conf.reduce((a, b) => a + b, 0);
  // Indicadores (D25, D27): série completa, harmonizada e mensal; o mês de referência é o "Até" do período.
  const ref = r.last;
  const sc = fireScore(full, ref);
  el.innerHTML = `
    <div class="panel-head">
      ${regionHead(state.sel)}
      <div><span class="label">${t('panel.period')}</span><strong>${ymLabel(r.first)} – ${ymLabel(r.last)}</strong></div>
    </div>
    <div class="kpis">
      <div class="kpi ${state.mode === 'harm' ? 'on' : ''}"><span class="label">${t('panel.harm')}</span><b>${fmt(r.totalHarm)}</b><span class="muted">${t('panel.harm.u')}</span></div>
      <div class="kpi ${state.mode === 'raw' ? 'on' : ''}"><span class="label">${t('panel.raw')}</span><b>${fmt(r.totalRaw)}</b><span class="muted">${t('panel.raw.u')}</span></div>
      <div class="kpi"><span class="label">${t('panel.peak')}</span><b>${ymLabel(r.peak.ym)}</b><span class="muted">${fmt(r.peak.value)} · ${r.peak.src}</span></div>
      ${lowConf ? `<div class="kpi"><span class="label">${t('panel.lowconf')}</span><b>${lowConf}</b></div>` : ''}
    </div>
    <div class="kpis ind">
      ${scoreKpi(sc)}
      ${chanceKpi(historicalChance(full, ref % 100))}
      ${peakKpi(typicalPeak(full))}
    </div>
    ${chanceStrip(chanceAllMonths(full))}
    <p class="muted small">${t('ind.how')}</p>
    <h3 class="cal-title">${t('cal.title')} · ${state.mode === 'raw' ? t('f.raw') : t('f.harm')}</h3>
    <div id="calendar" class="calendar"></div>
    <p class="muted small">${t('cal.lowconf')} · ${t('cal.toggle')}</p>
    <button type="button" id="csv-btn" class="btn-apply btn-navy btn-csv">${t('csv.btn')}</button>
    <p class="note">${t(state.sel.kind === 'area' ? 'panel.note.area' : 'panel.note')}</p>`;
  renderCalendar($('calendar'), s, state.mode);
  $('csv-btn').addEventListener('click', () => downloadCSV(s));
}

// ---------- aba Outlook ----------
const pct = (p) => `${Math.round(p * 100)}%`;
const unitLabel = (u) => t(`fc.unit.${u}`);

function skillLine(skill) {
  const o = skill?.overall;
  if (!o) return '';
  const s = (v) => `${v >= 0 ? '+' : ''}${Math.round(v * 100)}%`;
  return `${t('fc.skill')}: <b>${s(o.bss_clim)}</b> ${t('fc.vsclim')} · <b>${s(o.bss_d27)}</b> ${t('fc.vsd27')} · AUC ${fmt(o.auc)} · ${t('fc.cov')} ${pct(o.coverage_80)}`;
}

/** Plano B (R18): chance histórica D27 dos 12 meses, já calculada na série harmonizada. */
function planB(reasonKey, skill) {
  const s = state.series;
  const strip = s && !s.empty ? chanceStrip(chanceAllMonths(s)) : `<p class="panel-msg">${t('panel.nofire')}</p>`;
  return `<div class="fc-banner warn">${t(reasonKey)}${skill ? `<br><small>${skillLine(skill)}</small>` : ''}</div>${strip}
    <p class="muted small">${t('ind.how')}</p>`;
}

function outlookChart(el, o) {
  const rows = Array.from({ length: 12 }, (_, i) => ({ m: i + 1, q10: o.q10[i], q50: o.q50[i], q90: o.q90[i], normal: o.normal?.[i], p: o.p[i] }));
  el.replaceChildren(Plot.plot({
    width: Math.max(320, el.clientWidth), height: 220, marginLeft: 52,
    x: { domain: [0.6, 12.4], ticks: rows.map((r) => r.m), tickFormat: (m) => monthName(m), label: null },
    y: { label: unitLabel(o.unit), grid: true, nice: true },
    marks: [
      Plot.areaY(rows, { x: 'm', y1: 'q10', y2: 'q90', fill: '#a59c74', fillOpacity: 0.35, curve: 'monotone-x' }),
      Plot.lineY(rows, { x: 'm', y: 'q50', stroke: '#00204d', strokeWidth: 2, marker: 'circle', curve: 'monotone-x' }),
      o.normal ? Plot.dot(rows, { x: 'm', y: 'normal', symbol: 'diamond', stroke: '#ff5a1f', fill: '#fff', r: 4 }) : null,
      Plot.tip(rows, Plot.pointerX({ x: 'm', y: 'q50', title: (r) => `${monthName(r.m)} 2026\n${t('fc.pabove')}: ${pct(r.p)}\n${t('fc.expected')}: ${fmt(r.q50)} (${fmt(r.q10)}–${fmt(r.q90)})${r.normal != null ? `\n${t('fc.normal')}: ${fmt(r.normal)}` : ''}` })),
    ],
  }));
}

function renderOutlook(el, msg, status) {
  if (status === 'loading') return msg('panel.loading');
  if (!state.sel) return msg('fc.empty');
  if (state.fcErr) return msg('panel.error', state.fcErr);
  if (state.fcSel !== state.sel || state.skill === undefined) return msg('panel.loading');
  const gate = gateStatus(state.skill);
  const head = `<div class="panel-head">${regionHead(state.sel)}<div><span class="label">${t('fc.horizon')}</span><strong>${t('fc.horizon.v')}</strong></div></div>`;
  if (gate === 'none') { el.innerHTML = head + planB('fc.none'); return; }
  if (gate === 'failed' && !FORCE_OUTLOOK) { el.innerHTML = head + planB('fc.failed', state.skill); return; }
  const o = state.fc;
  if (!o || o.empty) { el.innerHTML = head + planB('fc.nocell', state.skill); return; }
  const r = outlookSummary(o);
  const u = unitLabel(o.unit);
  const strip = Array.from({ length: 12 }, (_, i) => {
    const p = o.p[i], cls = p >= 0.7 ? 'hi' : p >= 0.4 ? 'mid' : 'lo';
    return `<li class="${cls}" title="${monthName(i + 1)}: ${t('fc.pabove')} ${pct(p)} · ${t('fc.expected')} ${fmt(o.q50[i])} (${fmt(o.q10[i])}–${fmt(o.q90[i])}) ${u}"><span>${monthName(i + 1)}</span><b>${pct(p)}</b></li>`;
  }).join('');
  const rows = Array.from({ length: 12 }, (_, i) => `<tr><td>${monthName(i + 1)}</td><td>${pct(o.p[i])}</td>
    <td>${fmt(o.q50[i])} <span class="muted">(${fmt(o.q10[i])}–${fmt(o.q90[i])})</span></td><td>${o.normal ? fmt(o.normal[i]) : '—'}</td></tr>`).join('');
  el.innerHTML = `${head}
    ${gate === 'failed' ? `<div class="fc-banner warn">${t('fc.forced')}</div>` : ''}
    <div class="fc-banner">${skillLine(state.skill)}</div>
    <div class="kpis ind">
      <div class="kpi"><span class="label">${t('fc.top')}</span><b>${monthName(r.topP.month)}</b><span class="muted">${t('fc.pabove')} ${pct(r.topP.p)}</span></div>
      <div class="kpi"><span class="label">${t('fc.peak')}</span><b>${monthName(r.peak.month)}</b><span class="muted">${fmt(r.peak.q50)} ${u}</span></div>
      <div class="kpi"><span class="label">${t('fc.total')}</span><b>${fmt(r.total.q50)}</b><span class="muted">${fmt(r.total.q10)}–${fmt(r.total.q90)} ${u}${r.total.normal != null ? ` · ${t('fc.normal')} ${fmt(r.total.normal)}` : ''}</span></div>
    </div>
    <h3 class="cal-title">${t('fc.strip')}</h3>
    <ul class="chance-strip fc-strip">${strip}</ul>
    <div id="fc-chart" class="calendar"></div>
    <p class="muted small">${t('fc.legend')}</p>
    <details class="fc-table"><summary>${t('fc.table')}</summary>
      <table><thead><tr><th>${t('f.month')}</th><th>${t('fc.pabove')}</th><th>${t('fc.expected')} (${u})</th><th>${t('fc.normal')}</th></tr></thead><tbody>${rows}</tbody></table>
    </details>
    ${o.coverage < 1 ? `<p class="muted small">${t('fc.coverage')} ${o.cellsWith}/${o.cellsTotal}.</p>` : ''}
    <p class="note">${t(state.sel.kind === 'area' ? 'fc.note.area' : 'fc.note')}</p>`;
  outlookChart($('fc-chart'), o);
}

onLang(() => { fillSelects(); $('filtro-status').textContent = ''; drawRender(); refreshMap(); renderPanel(); });
renderPanel();
refreshMap();

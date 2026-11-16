// Timeline (4.4, Parte 1): área fixada + valores mensais por hexágono.
// Funções puras sobre data.js; sem Leaflet/h3 (testável com `node --test`).
// Valores já ÷ 10 (como areaSeries). Série da área = a MESMA do painel (areaSeries), por construção.

import { RES_TILE, SCALE, areaSeries } from './data.js';
import { MIN_FIRE } from './analytics.js';

/**
 * Carrega a área célula a célula: todas as células da seleção entram (com ou sem fogo),
 * para o contorno ficar fixo ao mexer no cursor. Célula sem fogo ou em tile 404 = zeros.
 * Devolve { months, src, low_conf, lo, hi, sum:{harm,raw}, cells:[{id,harm,raw,hasFire}], ... }.
 */
export async function loadTimelineArea(store, cells, cellToParent) {
  const base = await areaSeries(store, cells, cellToParent); // soma, lo/hi, low_conf (igual ao painel)
  if (base.empty) return { empty: true, outOfScope: Boolean(base.outOfScope), months: [], src: [], cells: [], cellsWithFire: 0, cellsTotal: cells.length };

  const parents = [...new Set(cells.map((c) => cellToParent(c, RES_TILE)))];
  const tiles = new Map(await Promise.all(parents.map(async (p) => [p, await store.get(p)]))); // cache do TileStore
  const n = base.months.length;

  const list = cells.map((id) => {
    const tile = tiles.get(cellToParent(id, RES_TILE));
    const h = tile?.cells?.[id], r = tile?.raw?.[id];
    const harm = new Float64Array(n), raw = new Float64Array(n);
    for (let k = 0; k < n; k++) {
      if (h) harm[k] = h[k] / SCALE;
      if (r) raw[k] = r[k] / SCALE;
    }
    return { id, harm, raw, hasFire: Boolean(h) };
  });

  return {
    empty: false, months: base.months, src: base.src, low_conf: base.low_conf, lo: base.lo, hi: base.hi,
    sum: { harm: base.harm, raw: base.raw }, cells: list,
    cellsWithFire: base.cellsWithFire, cellsTotal: base.cellsTotal,
  };
}

/** Fixa a área: cópia da seleção + dados, imutável. Mexer em state.sel depois não altera a Timeline. */
export function freezeArea(sel, data) {
  const snap = Object.freeze({ ...sel, cells: Object.freeze([...sel.cells]) });
  return Object.freeze({ sel: snap, data: Object.freeze({ ...data, cells: Object.freeze([...data.cells]) }) });
}

/** Índice do mês (year, month) em months; fora do intervalo, trava na ponta. */
export function indexFor(months, year, month) {
  const ym = year * 100 + month;
  if (!months.length || ym <= months[0]) return 0;
  if (ym >= months.at(-1)) return months.length - 1;
  return months.findIndex((m) => m >= ym);
}

/** Anda `delta` meses a partir de i, travando nas pontas. */
export const stepIndex = (i, delta, n) => Math.max(0, Math.min(n - 1, i + delta));

/** Valores de cada célula no mês i, na ordem de area.cells. key = 'harm' | 'raw'. */
export const valuesAt = (area, i, key = 'harm') => area.cells.map((c) => c[key][i]);

/**
 * Teto fixo da escala de cor: p98 de todos os valores célula-mês ≥ MIN_FIRE (mesma ideia do mapa: um extremo
 * não apaga o resto). Fixo no período inteiro, para que meses diferentes sejam comparáveis. Mínimo 1.
 */
export function scaleMax(area, key = 'harm') {
  const vals = [];
  for (const c of area.cells) for (const v of c[key]) if (v >= MIN_FIRE) vals.push(v);
  vals.sort((a, b) => a - b);
  return Math.max(1, vals[Math.floor(vals.length * 0.98)] ?? 1);
}

/** Resumo do mês i para o texto ao lado do mapa. */
export function describeMonth(area, i, key = 'harm') {
  let active = 0, top = null;
  for (const c of area.cells) {
    const v = c[key][i];
    if (v >= MIN_FIRE) active++;
    if (v > 0 && (!top || v > top.value)) top = { id: c.id, value: v };
  }
  return {
    ym: area.months[i], src: area.src[i], lowConf: area.low_conf[i] === 1,
    sum: area.sum[key][i], active, topCell: top,
  };
}

/** Trechos contínuos de cada satélite na série (Terra → Aqua → S-NPP): [{src, from, to}] com índices inclusivos. */
export function seams(area) {
  const out = [];
  area.src.forEach((s, k) => {
    const last = out.at(-1);
    if (last && last.src === s) last.to = k; else out.push({ src: s, from: k, to: k });
  });
  return out;
}

/** Índice do mês de maior valor da área (1º em empate); ponto de partida do cursor. */
export function peakIndex(area, key = 'harm') {
  const s = area.sum?.[key];
  if (!s || !s.length) return 0;
  let best = 0;
  for (let k = 1; k < s.length; k++) if (s[k] > s[best]) best = k;
  return best;
}

/** Hash da data, no estilo do FIRMS: "#t=2004-09" → 200409; qualquer outra coisa → null. */
export function parseHash(hash) {
  const m = /^#?t=(\d{4})-(\d{1,2})$/.exec(String(hash ?? ''));
  if (!m) return null;
  const y = Number(m[1]), mo = Number(m[2]);
  return mo >= 1 && mo <= 12 ? y * 100 + mo : null;
}

/** 200409 → "t=2004-09" (sem o "#"; quem escreve na URL põe o "#"). */
export const formatHash = (ym) => `t=${Math.floor(ym / 100)}-${String(ym % 100).padStart(2, '0')}`;

const SAT = { TERRA: 'Terra', AQUA: 'Aqua', SNPP: 'S-NPP', N20: 'NOAA-20' };
/** Nome de exibição do satélite do contrato (`src`); desconhecido volta como veio. */
export const satLabel = (src) => SAT[src] ?? String(src ?? '—');

// ---------- Parte 4: série mensal + emendas de satélite (gráfico) ----------

/** Satélites e seus meses (YYYYMM, inclusivos), na ordem cronológica. `src` = código do contrato (satLabel dá o nome). */
const SAT_SPANS = [
  { src: 'TERRA', from: 200011, to: 200206 },
  { src: 'AQUA', from: 200207, to: 201112 },
  { src: 'SNPP', from: 201201, to: 202512 },
];
const ymIdx = (ym) => Math.floor(ym / 100) * 12 + (ym % 100 - 1);
const ymDate = (ym) => new Date(Date.UTC(Math.floor(ym / 100), ym % 100 - 1, 1));

/**
 * Faixas de fundo por satélite, recortadas ao intervalo de `months` (YYYYMM). x1 = início do 1º mês;
 * x2 = início do mês seguinte ao último (exclusivo), então as faixas encostam, sem vão nas emendas.
 * Calendário fixo (D10), independente de `area.src`; `seams(area)` é a versão derivada dos dados.
 */
export function satelliteSeams(months) {
  if (!months?.length) return [];
  const first = months[0], last = months.at(-1);
  const out = [];
  for (const s of SAT_SPANS) {
    const a = Math.max(s.from, first), b = Math.min(s.to, last);
    if (a > b) continue;
    const next = ymIdx(b) + 1;
    out.push({ src: s.src, from: a, to: b, x1: ymDate(a), x2: new Date(Date.UTC(Math.floor(next / 12), next % 12, 1)) });
  }
  return out;
}

/** Série mensal agregada da área para o gráfico: [{ i, ym, date, value }]. key = 'harm' | 'raw'. Ausente/NaN = 0. */
export function timelineSeries(area, key = 'harm') {
  const s = area?.sum?.[key];
  if (!area?.months?.length || !s) return [];
  return area.months.map((ym, i) => {
    const v = Number(s[i]);
    return { i, ym, date: ymDate(ym), value: Number.isFinite(v) ? v : 0 };
  });
}

/** Data sob o ponteiro → mês mais próximo (YYYYMM). Quem chama trava nas pontas com indexFor. */
export function ymAtDate(date) {
  const d = new Date(date);
  const idx = Math.round(d.getUTCFullYear() * 12 + d.getUTCMonth() + (d.getUTCDate() - 1) / 30);
  return Math.floor(idx / 12) * 100 + (idx % 12) + 1;
}

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
  if (base.empty) return { empty: true, months: [], src: [], cells: [], cellsWithFire: 0, cellsTotal: cells.length };

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

// Leitor dos tiles da previsão climatológica 2026 (script climatologia_2026.py).
// Mesmo padrão do data.js: funções puras + cache de tiles, sem dependência de Leaflet/h3
// (cellToParent entra por parâmetro; testável com `node --test`).
// Tile = um arquivo por célula-pai H3 res 2: climatologia_<pai>.json, células res 5,
// cada célula com 12 inteiros (jan..dez) = nº de anos com fogo. pct = inteiro / n_years × 100.

import { RES_TILE, isMissingTile } from './data.js';

export const MONTHS_N = 12;

export function climaUrl(base, parent) {
  const b = base.endsWith('/') ? base : `${base}/`;
  return `${b}data/climatologia_${parent}.json`;
}

/** Confere o tile contra o contrato. Devolve lista de erros (vazia = ok). */
export function validateClimaTile(t) {
  const errs = [];
  if (!t || typeof t !== 'object') return ['tile não é objeto'];
  if (!Number.isInteger(t.n_years) || t.n_years < 1) errs.push('n_years ausente ou inválido');
  if (!t.cells || typeof t.cells !== 'object') return [...errs, 'cells ausente'];
  for (const [cell, v] of Object.entries(t.cells)) {
    if (!Array.isArray(v) || v.length !== MONTHS_N) { errs.push(`cells[${cell}] com ${v?.length} valores (esperado ${MONTHS_N})`); break; }
    if (!v.every((x) => Number.isInteger(x) && x >= 0 && x <= t.n_years)) { errs.push(`cells[${cell}] com valor fora de 0..n_years`); break; }
  }
  return errs;
}

/** Cache de tiles. 404 = pai sem tile → null. Outros erros sobem. */
export class ClimaStore {
  constructor(base, fetchFn = globalThis.fetch.bind(globalThis)) {
    this.base = base;
    this.fetch = fetchFn;
    this.cache = new Map();
  }
  get(parent) {
    if (!this.cache.has(parent)) {
      const p = (async () => {
        const r = await this.fetch(climaUrl(this.base, parent));
        if (isMissingTile(r)) return null; // 404 ou fallback HTML do Vite
        if (!r.ok) throw new Error(`clima ${parent}: HTTP ${r.status}`);
        const t = await r.json();
        const errs = validateClimaTile(t);
        if (errs.length) throw new Error(`clima ${parent} fora do contrato: ${errs.slice(0, 3).join('; ')}`);
        return t;
      })();
      p.catch(() => this.cache.delete(parent)); // permite tentar de novo após falha de rede
      this.cache.set(parent, p);
    }
    return this.cache.get(parent);
  }
}

/**
 * 12 percentuais (jan..dez) de uma seleção: 1 célula = ponto; várias = média das células da área.
 * Célula ausente num tile existente = sem fogo na janela (zeros), como no data.js; ela conta na média.
 * empty = nenhuma célula da seleção tem dados (nenhum tile ou nenhuma célula listada).
 * outOfScope = nenhum tile existe para a seleção (ex.: ponto fora do Brasil).
 */
export async function areaClimatologia(store, cells, cellToParent) {
  const byParent = new Map();
  for (const c of cells) {
    const p = cellToParent(c, RES_TILE);
    if (!byParent.has(p)) byParent.set(p, []);
    byParent.get(p).push(c);
  }
  const tiles = await Promise.all([...byParent.keys()].map((p) => store.get(p)));

  let nYears = null;
  for (const t of tiles) {
    if (!t) continue;
    if (nYears === null) nYears = t.n_years;
    else if (t.n_years !== nYears) throw new Error('tiles com n_years diferentes (export misturado?)');
  }

  const hits = new Array(MONTHS_N).fill(0);
  let cellsWithData = 0;
  [...byParent.values()].forEach((group, i) => {
    const t = tiles[i];
    if (!t) return;
    for (const c of group) {
      const v = t.cells[c];
      if (!v) continue;
      cellsWithData++;
      for (let m = 0; m < MONTHS_N; m++) hits[m] += v[m];
    }
  });

  const total = cells.length;
  const pct = nYears ? hits.map((h) => (100 * h) / (total * nYears)) : new Array(MONTHS_N).fill(0);
  return { pct, nYears, cellsTotal: total, cellsWithData, empty: cellsWithData === 0, outOfScope: nYears === null };
}

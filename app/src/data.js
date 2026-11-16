// Leitor dos tiles do app (DATA_DICTIONARY §3 e §11, D36, D38).
// Funções puras + cache de tiles; sem dependência de Leaflet/h3 (testável com `node --test`).
// Tile = um arquivo por célula-pai H3 res 2: harm_<pai>.json, células res 5, valores × 10.

export const RES_PRODUCT = 5; // D36: resolução do produto
export const RES_TILE = 2;    // D38: célula-pai do tile
export const SCALE = 10;      // contrato §3: valores × 10, inteiros (exceto low_conf)

const VEC_KEYS = ['cells', 'raw', 'lo', 'hi', 'low_conf'];
const REQUIRED = ['cells', 'raw'];

export function tileUrl(base, parent) {
  const b = base.endsWith('/') ? base : `${base}/`;
  return `${b}data/harm_${parent}.json`;
}

/** Confere o tile contra o contrato. Devolve lista de erros (vazia = ok). */
export function validateTile(t) {
  const errs = [];
  if (!t || typeof t !== 'object') return ['tile não é objeto'];
  const n = Array.isArray(t.months) ? t.months.length : 0;
  if (!n) errs.push('months ausente ou vazio');
  else if (!t.months.every((m, i) => Number.isInteger(m) && (i === 0 || m > t.months[i - 1])))
    errs.push('months fora de ordem ou não inteiro');
  if (!Array.isArray(t.src) || t.src.length !== n) errs.push('src não alinhado com months');
  for (const k of REQUIRED) if (!t[k] || typeof t[k] !== 'object') errs.push(`${k} ausente`);
  for (const k of VEC_KEYS) {
    if (!t[k]) continue;
    for (const [cell, v] of Object.entries(t[k])) {
      if (!Array.isArray(v) || v.length !== n) { errs.push(`${k}[${cell}] com ${v?.length} valores (esperado ${n})`); break; }
      if (!v.every(Number.isInteger)) { errs.push(`${k}[${cell}] com valor não inteiro`); break; }
    }
  }
  return errs;
}

/**
 * Tile inexistente → true (contrato §11: tratado como null).
 * Além do 404, cobre o fallback de SPA do Vite (dev/preview): arquivo que não existe volta 200
 * com o index.html (text/html). Sem isto, r.json() quebrava com "Unexpected token '<'" fora do Brasil.
 */
export function isMissingTile(r) {
  if (r.status === 404) return true;
  const ct = r.headers?.get?.('content-type') ?? '';
  return Boolean(r.ok && ct.includes('text/html'));
}

/** Cache de tiles. 404 = pai sem fogo (contrato §11) → null. Outros erros sobem. */
export class TileStore {
  constructor(base, fetchFn = globalThis.fetch.bind(globalThis)) {
    this.base = base;
    this.fetch = fetchFn;
    this.cache = new Map();
  }
  get(parent) {
    if (!this.cache.has(parent)) {
      const p = (async () => {
        const r = await this.fetch(tileUrl(this.base, parent));
        if (isMissingTile(r)) return null;
        if (!r.ok) throw new Error(`tile ${parent}: HTTP ${r.status}`);
        const t = await r.json();
        const errs = validateTile(t);
        if (errs.length) throw new Error(`tile ${parent} fora do contrato: ${errs.slice(0, 3).join('; ')}`);
        return t;
      })();
      p.catch(() => this.cache.delete(parent)); // permite tentar de novo após falha de rede
      this.cache.set(parent, p);
    }
    return this.cache.get(parent);
  }
}

/**
 * Série de uma área (1 célula = ponto lat/lon; várias = área desenhada).
 * Soma mês a mês e divide por 10. Célula ausente num tile existente = sem fogo (zeros).
 * low_conf da área = 1 se qualquer célula com fogo no mês tiver low_conf = 1 (conservador).
 * outOfScope = nenhum tile existe para a seleção (ex.: ponto fora do Brasil) → painel mostra "fora do escopo".
 */
export async function areaSeries(store, cells, cellToParent) {
  const byParent = new Map();
  for (const c of cells) {
    const p = cellToParent(c, RES_TILE);
    if (!byParent.has(p)) byParent.set(p, []);
    byParent.get(p).push(c);
  }
  const tiles = await Promise.all([...byParent.keys()].map((p) => store.get(p)));

  let months = null, src = null;
  for (const t of tiles) {
    if (!t) continue;
    if (!months) { months = t.months; src = t.src; }
    else if (t.months.length !== months.length || t.months[0] !== months[0])
      throw new Error('tiles com meses diferentes (export misturado?)');
  }
  if (!months) return { months: [], src: [], cellsWithFire: 0, cellsTotal: cells.length, empty: true, outOfScope: true };

  const n = months.length;
  const out = { harm: new Float64Array(n), raw: new Float64Array(n), lo: new Float64Array(n), hi: new Float64Array(n), low_conf: new Uint8Array(n) };
  let cellsWithFire = 0;
  [...byParent.values()].forEach((group, i) => {
    const t = tiles[i];
    if (!t) return;
    for (const c of group) {
      const h = t.cells[c];
      if (!h) continue;
      cellsWithFire++;
      const r = t.raw?.[c], lo = t.lo?.[c] ?? h, hi = t.hi?.[c] ?? h, lc = t.low_conf?.[c];
      for (let k = 0; k < n; k++) {
        out.harm[k] += h[k] / SCALE;
        out.raw[k] += (r ? r[k] : 0) / SCALE;
        out.lo[k] += lo[k] / SCALE;
        out.hi[k] += hi[k] / SCALE;
        if (lc && lc[k] && h[k] > 0) out.low_conf[k] = 1;
      }
    }
  });
  return { months, src, ...out, cellsWithFire, cellsTotal: cells.length, empty: cellsWithFire === 0, outOfScope: false };
}

/** Índices [i0, i1] (inclusivos) do período from..to (AAAAMM) dentro de months; null se vazio. */
export function periodIndex(months, from, to) {
  const lo = Math.min(from, to), hi = Math.max(from, to);
  let i0 = months.findIndex((m) => m >= lo);
  let i1 = -1;
  for (let k = months.length - 1; k >= 0; k--) if (months[k] <= hi) { i1 = k; break; }
  if (i0 < 0 || i1 < 0 || i0 > i1) return null;
  return [i0, i1];
}

/** Recorta a série da área ao período (para o card e o calendário). */
export function slicePeriod(s, from, to) {
  if (s.empty) return s;
  const r = periodIndex(s.months, from, to);
  if (!r) return { ...s, empty: true };
  const [i0, i1] = r;
  const cut = (a) => a.slice(i0, i1 + 1);
  return { ...s, months: cut(s.months), src: cut(s.src), harm: cut(s.harm), raw: cut(s.raw), lo: cut(s.lo), hi: cut(s.hi), low_conf: cut(s.low_conf) };
}

/** Total do período por célula de um tile (camada do mapa). key = 'cells' (harmonizado) ou 'raw'. */
export function cellTotals(tile, i0, i1, key = 'cells') {
  const out = new Map();
  for (const [cell, v] of Object.entries(tile[key] ?? {})) {
    let s = 0;
    for (let k = i0; k <= i1; k++) s += v[k];
    if (s > 0) out.set(cell, s / SCALE);
  }
  return out;
}

/** Resumo do card (não é o score D25 nem o pico típico). */
export function summarize(s) {
  if (s.empty) return null;
  const sum = (a) => a.reduce((x, y) => x + y, 0);
  const annual = new Map();
  s.months.forEach((ym, k) => {
    const y = Math.floor(ym / 100);
    const a = annual.get(y) ?? { harm: 0, raw: 0 };
    a.harm += s.harm[k]; a.raw += s.raw[k];
    annual.set(y, a);
  });
  let peakK = 0;
  for (let k = 1; k < s.harm.length; k++) if (s.harm[k] > s.harm[peakK]) peakK = k;
  return {
    first: s.months[0], last: s.months.at(-1),
    totalHarm: sum(s.harm), totalRaw: sum(s.raw),
    activeMonths: s.harm.filter((v) => v > 0).length,
    peak: { ym: s.months[peakK], value: s.harm[peakK], src: s.src[peakK] },
    annual,
  };
}

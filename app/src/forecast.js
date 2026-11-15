// Fire Outlook 2026 no navegador (D35, D48, DATA_DICTIONARY §9).
// Lê forecast_<pai res 2>.json e forecast_skill.json gerados por pipeline/forecast/export_forecast.py.
// Funções puras + cache; sem Leaflet/h3 (testável com `node --test`).

export const UNITS = ['detections', 'frp_mw'];
export const P_SCALE = 100; // p × 100
export const Q_SCALE = 10;  // q10/q50/q90/normal × 10
const QKEYS = ['q10', 'q50', 'q90'];

const join = (base, f) => `${base.endsWith('/') ? base : `${base}/`}data/${f}`;
export const forecastUrl = (base, parent) => join(base, `forecast_${parent}.json`);
export const skillUrl = (base) => join(base, 'forecast_skill.json');

/** Confere um tile de previsão contra o contrato §9. Devolve lista de erros (vazia = ok). */
export function validateForecastTile(t) {
  const errs = [];
  if (!t || typeof t !== 'object') return ['tile não é objeto'];
  if (!Array.isArray(t.months) || t.months.length !== 12) errs.push('months deve ter 12 meses');
  if (!UNITS.includes(t.unit)) errs.push(`unit inválida: ${t.unit}`);
  if (!t.cells || typeof t.cells !== 'object') return [...errs, 'cells ausente'];
  for (const [c, v] of Object.entries(t.cells)) {
    const keys = ['p', ...QKEYS, ...(v.normal ? ['normal'] : [])];
    const bad = keys.find((k) => !Array.isArray(v[k]) || v[k].length !== 12 || !v[k].every(Number.isInteger));
    if (bad) { errs.push(`${c}.${bad} fora do contrato`); break; }
    if (!v.p.every((x) => x >= 0 && x <= P_SCALE)) { errs.push(`${c}.p fora de 0–100`); break; }
    if (v.q10.some((x, k) => x > v.q50[k] || v.q50[k] > v.q90[k])) { errs.push(`${c}: quantis cruzados`); break; }
  }
  return errs;
}

/** Cache dos tiles de previsão e do skill. 404 = sem previsão para o pai / sem skill → null. */
export class ForecastStore {
  constructor(base, fetchFn = globalThis.fetch.bind(globalThis)) {
    this.base = base; this.fetch = fetchFn; this.cache = new Map(); this.skillP = null;
  }
  async #json(url, validate) {
    const r = await this.fetch(url);
    if (r.status === 404) return null;
    if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
    const j = await r.json();
    const errs = validate ? validate(j) : [];
    if (errs.length) throw new Error(`${url} fora do contrato: ${errs.slice(0, 3).join('; ')}`);
    return j;
  }
  get(parent) {
    if (!this.cache.has(parent)) {
      const p = this.#json(forecastUrl(this.base, parent), validateForecastTile);
      p.catch(() => this.cache.delete(parent));
      this.cache.set(parent, p);
    }
    return this.cache.get(parent);
  }
  skill() {
    if (!this.skillP) {
      this.skillP = this.#json(skillUrl(this.base));
      this.skillP.catch(() => { this.skillP = null; });
    }
    return this.skillP;
  }
}

/** 'none' = previsão não exportada · 'failed' = reprovada no portão (R18) · 'ok' = aprovada. */
export function gateStatus(skill) {
  if (!skill) return 'none';
  return skill.passes_gate === true ? 'ok' : 'failed';
}

/**
 * Outlook de um ponto (1 célula) ou área (várias células res 5) — PREVISAO §1:
 * faixa da área = soma de q10/q50/q90 das células (conservadora); normal = soma dos normais;
 * P(área acima do normal) = média das P das células ponderada pela atividade esperada do mês
 * (normal + q50 da célula; se tudo zero, média simples) — aproximação declarada na tela.
 */
export async function areaOutlook(store, cells, cellToParent, resTile = 2) {
  const byParent = new Map();
  for (const c of cells) {
    const p = cellToParent(c, resTile);
    if (!byParent.has(p)) byParent.set(p, []);
    byParent.get(p).push(c);
  }
  const tiles = await Promise.all([...byParent.keys()].map((p) => store.get(p)));
  const out = { months: null, unit: null, p: new Float64Array(12), normal: null, cellsWith: 0, cellsTotal: cells.length };
  for (const k of QKEYS) out[k] = new Float64Array(12);
  const pw = new Float64Array(12), w = new Float64Array(12), pm = new Float64Array(12);
  let hasNormal = true;
  [...byParent.values()].forEach((group, i) => {
    const t = tiles[i];
    if (!t) return;
    if (!out.months) { out.months = t.months; out.unit = t.unit; }
    else if (t.unit !== out.unit) throw new Error('tiles de previsão com unidades diferentes');
    for (const c of group) {
      const v = t.cells[c];
      if (!v) continue;
      out.cellsWith++;
      if (!v.normal) hasNormal = false;
      for (let m = 0; m < 12; m++) {
        for (const k of QKEYS) out[k][m] += v[k][m] / Q_SCALE;
        const nm = v.normal ? v.normal[m] / Q_SCALE : 0;
        const wt = nm + v.q50[m] / Q_SCALE;
        const p = v.p[m] / P_SCALE;
        pw[m] += p * wt; w[m] += wt; pm[m] += p;
        if (v.normal) { out.normal ??= new Float64Array(12); out.normal[m] += nm; }
      }
    }
  });
  if (!out.cellsWith) return { ...out, empty: true };
  for (let m = 0; m < 12; m++) out.p[m] = w[m] > 0 ? pw[m] / w[m] : pm[m] / out.cellsWith;
  if (!hasNormal) out.normal = null;
  return { ...out, empty: false, coverage: out.cellsWith / out.cellsTotal };
}

/** Resumo para o card: mês com maior P, mês com maior q50 e total do ano (q10–q90). */
export function outlookSummary(o) {
  if (o.empty) return null;
  const arg = (a) => a.reduce((b, v, i) => (v > a[b] ? i : b), 0);
  const sum = (a) => a.reduce((x, y) => x + y, 0);
  const iP = arg(o.p), iQ = arg(o.q50);
  return {
    topP: { month: iP + 1, p: o.p[iP] },
    peak: { month: iQ + 1, q50: o.q50[iQ] },
    total: { q10: sum(o.q10), q50: sum(o.q50), q90: sum(o.q90), normal: o.normal ? sum(o.normal) : null },
    monthsAbove: [...o.p].filter((p) => p >= 0.5).length,
  };
}

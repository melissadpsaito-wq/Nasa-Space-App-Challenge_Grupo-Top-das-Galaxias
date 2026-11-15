// Indicadores da área no navegador (4.2): Fire Anomaly Score e pico típico (D25), chance histórica (D27), CSV (§7).
// Funções puras sobre a série de areaSeries() (valores já ÷ 10). Sempre na série HARMONIZADA e MENSAL
// (D44/R24: comparações mensais; o modo Bruto só muda o calendário). Sem dependências: `node --test`.

export const MIN_FIRE = 0.5;   // < 0,5 detecção no mês = "sem fogo" (mesmo corte da exibição, R22)
export const MIN_YEARS = 5;    // D27: < 5 anos com fogo no mês → "dados insuficientes" (usado também no score e no pico)
export const BANDS = [95, 85, 60]; // D25: faixas do score

export const median = (a) => {
  if (!a.length) return NaN;
  const s = [...a].sort((x, y) => x - y), h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
};

/** Valores harmonizados por mês do calendário: Map(M → [{year, v}]) em ordem de ano. */
export function byCalendarMonth(s) {
  const out = new Map();
  for (let M = 1; M <= 12; M++) out.set(M, []);
  s.months.forEach((ym, k) => out.get(ym % 100).push({ year: Math.floor(ym / 100), v: s.harm[k] }));
  return out;
}

/** Último ano com os 12 meses na série (dados até dez/2025 → 2025). */
export function lastCompleteYear(s) {
  const n = new Map();
  for (const ym of s.months) { const y = Math.floor(ym / 100); n.set(y, (n.get(y) ?? 0) + 1); }
  return Math.max(...[...n].filter(([, c]) => c === 12).map(([y]) => y));
}

/**
 * D25 — Fire Anomaly Score do mês `ym` da área: percentil empírico (mid-rank, 0–100) entre o mesmo mês
 * dos anos ANTERIORES (sem usar o próprio ano nem anos futuros). Também a razão sobre a mediana.
 * band: 'extreme' ≥ 95 · 'high' ≥ 85 · 'above' ≥ 60 · 'normal'; 'none' = sem fogo no mês e no histórico.
 */
export function fireScore(s, ym) {
  const k = s.months.indexOf(ym);
  if (s.empty || k < 0) return { ym, status: 'nodata' };
  const v = s.harm[k], Y = Math.floor(ym / 100);
  const H = byCalendarMonth(s).get(ym % 100).filter((r) => r.year < Y).map((r) => r.v);
  const withFire = H.filter((h) => h >= MIN_FIRE).length;
  const med = median(H);
  const base = { ym, value: v, median: med, years: H.length, yearsWithFire: withFire };
  if (H.length < MIN_YEARS) return { ...base, status: 'insufficient' };
  if (v < MIN_FIRE && withFire === 0) return { ...base, status: 'ok', score: null, band: 'none', ratio: null };
  const below = H.filter((h) => h < v).length, eq = H.filter((h) => h === v).length;
  const score = Math.round((100 * (below + 0.5 * eq)) / H.length);
  const band = score >= BANDS[0] ? 'extreme' : score >= BANDS[1] ? 'high' : score >= BANDS[2] ? 'above' : 'normal';
  return { ...base, status: 'ok', score, band, ratio: med >= MIN_FIRE ? v / med : null };
}

/**
 * D25 — Pico típico: em cada ano completo com fogo, o mês de maior valor harmonizado;
 * pico típico = mês que mais vezes foi o pico. Devolve também o 2º colocado (temporada larga).
 */
export function typicalPeak(s) {
  if (s.empty) return { status: 'nodata' };
  const years = new Map();
  s.months.forEach((ym, k) => {
    const y = Math.floor(ym / 100);
    if (!years.has(y)) years.set(y, []);
    years.get(y).push({ M: ym % 100, v: s.harm[k] });
  });
  const count = new Array(13).fill(0);
  let n = 0, y0 = null, y1 = null;
  for (const [y, rows] of years) {
    if (rows.length !== 12 || rows.reduce((a, r) => a + r.v, 0) < MIN_FIRE) continue;
    let best = rows[0];
    for (const r of rows) if (r.v > best.v) best = r;
    count[best.M]++; n++;
    y0 = y0 ?? y; y1 = y;
  }
  if (n < MIN_YEARS) return { status: 'insufficient', years: n };
  const order = [...count.keys()].slice(1).sort((a, b) => count[b] - count[a] || a - b);
  return {
    status: 'ok', month: order[0], hits: count[order[0]], years: n, from: y0, to: y1,
    second: count[order[1]] ? { month: order[1], hits: count[order[1]] } : null,
  };
}

/**
 * D27 — Chance histórica de o mês M ficar acima do normal.
 * normal = mediana de M em todos os anos da área; chance = anos acima do normal entre os últimos 10 anos completos.
 * < MIN_YEARS anos com fogo em M → 'insufficient'.
 */
export function historicalChance(s, M, window = 10) {
  if (s.empty) return { month: M, status: 'nodata' };
  const rows = byCalendarMonth(s).get(M);
  const normal = median(rows.map((r) => r.v));
  const withFire = rows.filter((r) => r.v >= MIN_FIRE).length;
  if (withFire < MIN_YEARS) return { month: M, status: 'insufficient', yearsWithFire: withFire };
  const last = lastCompleteYear(s);
  const recent = rows.filter((r) => r.year > last - window && r.year <= last);
  const k = recent.filter((r) => r.v > normal).length;
  return { month: M, status: 'ok', normal, k, n: recent.length, pct: Math.round((100 * k) / recent.length), from: last - window + 1, to: last };
}

/** D27 para os 12 meses (plano B do Outlook, R18). */
export const chanceAllMonths = (s) => Array.from({ length: 12 }, (_, i) => historicalChance(s, i + 1));

/** CSV do contrato §7: year,month,harmonized,lo,hi,raw,low_conf — uma linha por mês da série recortada. */
export function toCSV(s) {
  const r1 = (v) => Math.round(v * 10) / 10; // dados vêm × 10 inteiros → 1 casa decimal é exata
  const lines = ['year,month,harmonized,lo,hi,raw,low_conf'];
  if (!s.empty) s.months.forEach((ym, k) => {
    lines.push([Math.floor(ym / 100), ym % 100, r1(s.harm[k]), r1(s.lo[k]), r1(s.hi[k]), r1(s.raw[k]), s.low_conf[k]].join(','));
  });
  return `${lines.join('\n')}\n`;
}

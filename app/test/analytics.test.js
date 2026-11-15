// Testes dos indicadores da 4.2 (D25, D27, CSV §7): `npm test` em app/.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { median, fireScore, typicalPeak, historicalChance, chanceAllMonths, toCSV, lastCompleteYear } from '../src/analytics.js';

// Série sintética no formato de areaSeries (já ÷ 10). f(year, month) → valor harmonizado.
function series(y0, y1, f, { m0 = 1 } = {}) {
  const months = [], harm = [];
  for (let y = y0; y <= y1; y++) for (let m = y === y0 ? m0 : 1; m <= 12; m++) { months.push(y * 100 + m); harm.push(f(y, m)); }
  const n = months.length;
  return {
    months, src: months.map((ym) => (ym < 201202 ? 'AQUA' : 'SNPP')),
    harm: Float64Array.from(harm), raw: Float64Array.from(harm, (v) => v / 4),
    lo: Float64Array.from(harm), hi: Float64Array.from(harm), low_conf: new Uint8Array(n), empty: false,
  };
}

test('median: par, ímpar, vazio', () => {
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([4, 1, 3, 2]), 2.5);
  assert.ok(Number.isNaN(median([])));
});

test('lastCompleteYear ignora ano incompleto (nov/2000)', () => {
  assert.equal(lastCompleteYear(series(2000, 2025, () => 1, { m0: 11 })), 2025);
});

test('score D25: mid-rank só com anos anteriores, faixas e razão', () => {
  // setembro = ano − 2000 (crescente): set/2025 = 25 é maior que os 24 anteriores → 100
  const s = series(2001, 2025, (y, m) => (m === 9 ? y - 2000 : 1));
  const top = fireScore(s, 202509);
  assert.equal(top.status, 'ok');
  assert.equal(top.years, 24);
  assert.equal(top.score, 100);
  assert.equal(top.band, 'extreme');
  assert.equal(top.ratio, 25 / 12.5);
  // set/2010 = 10 vs 1..9 → 100; não olha 2011+ (sem vazamento)
  assert.equal(fireScore(s, 201009).score, 100);
  // empates contam metade: mês constante → 50, faixa normal
  const flat = fireScore(s, 202503);
  assert.equal(flat.score, 50);
  assert.equal(flat.band, 'normal');
  assert.equal(flat.ratio, 1);
});

test('score D25: histórico curto e mês sem fogo', () => {
  const s = series(2001, 2025, (y, m) => (m === 9 ? 5 : 0));
  assert.equal(fireScore(s, 200409).status, 'insufficient'); // 3 anos antes
  const none = fireScore(s, 202503);
  assert.equal(none.band, 'none');
  assert.equal(none.score, null);
  assert.equal(fireScore(s, 203001).status, 'nodata');
});

test('pico típico D25: mês que mais vezes foi pico, com 2º colocado', () => {
  // pico em setembro, exceto 2003–2007 (outubro)
  const s = series(2001, 2025, (y, m) => (m === 9 ? (y >= 2003 && y <= 2007 ? 5 : 10) : m === 10 ? 8 : 1));
  const p = typicalPeak(s);
  assert.equal(p.status, 'ok');
  assert.equal(p.month, 9);
  assert.equal(p.hits, 20);
  assert.equal(p.years, 25);
  assert.deepEqual(p.second, { month: 10, hits: 5 });
});

test('pico típico ignora ano incompleto e anos sem fogo; < 5 anos = insuficiente', () => {
  const s = series(2000, 2025, (y, m) => (y <= 2021 ? 0 : m === 8 ? 3 : 0), { m0: 11 });
  const p = typicalPeak(s);
  assert.equal(p.status, 'insufficient');
  assert.equal(p.years, 4);
});

test('chance D27: normal = mediana de todos os anos; k de 10 nos últimos anos completos', () => {
  // agosto: 1 em 2001–2015, 9 em 2016–2025 → mediana (25 anos) = 1 → 10 de 10 acima
  const s = series(2001, 2025, (y, m) => (m === 8 ? (y >= 2016 ? 9 : 1) : 0));
  const c = historicalChance(s, 8);
  assert.equal(c.status, 'ok');
  assert.equal(c.normal, 1);
  assert.deepEqual([c.k, c.n, c.pct, c.from, c.to], [10, 10, 100, 2016, 2025]);
  // maio sem fogo → insuficiente
  assert.equal(historicalChance(s, 5).status, 'insufficient');
  assert.equal(chanceAllMonths(s).length, 12);
});

test('chance D27: igual à mediana não conta como acima', () => {
  const s = series(2001, 2025, () => 2);
  assert.equal(historicalChance(s, 1).k, 0);
});

test('CSV §7: cabeçalho, uma linha por mês, 1 casa decimal', () => {
  const s = series(2025, 2025, (y, m) => m / 10 + 0.2); // 0.30000000000000004 etc.
  const csv = toCSV(s).trim().split('\n');
  assert.equal(csv[0], 'year,month,harmonized,lo,hi,raw,low_conf');
  assert.equal(csv.length, 13);
  assert.equal(csv[1], '2025,1,0.3,0.3,0.3,0.1,0');
  assert.equal(toCSV({ empty: true }).trim(), 'year,month,harmonized,lo,hi,raw,low_conf');
});

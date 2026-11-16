// Testes da Parte 4 (node --test). Mesmo estilo das Partes 1–3: funções puras, sem DOM.
import test from 'node:test';
import assert from 'node:assert/strict';
import { satelliteSeams, timelineSeries, ymAtDate, indexFor } from '../src/timeline.js';

const months = [];
for (let y = 2000; y <= 2025; y++) for (let m = 1; m <= 12; m++) { const ym = y * 100 + m; if (ym >= 200011) months.push(ym); }

test('série completa tem 302 meses (nov/2000 – dez/2025)', () => assert.equal(months.length, 302));

test('satelliteSeams: Terra → Aqua → S-NPP, contíguas, nas datas do D10', () => {
  const s = satelliteSeams(months);
  assert.deepEqual(s.map((b) => [b.src, b.from, b.to]), [
    ['TERRA', 200011, 200206], ['AQUA', 200207, 201112], ['SNPP', 201201, 202512],
  ]);
  assert.equal(s[0].x2.getTime(), s[1].x1.getTime());
  assert.equal(s[1].x2.getTime(), s[2].x1.getTime());
  assert.equal(s[2].x2.toISOString(), '2026-01-01T00:00:00.000Z');
});

test('satelliteSeams: recorta ao intervalo e descarta faixa vazia', () => {
  const s = satelliteSeams(months.filter((m) => m >= 200501 && m <= 200612));
  assert.deepEqual(s.map((b) => [b.src, b.from, b.to]), [['AQUA', 200501, 200612]]);
  assert.deepEqual(satelliteSeams([]), []);
  assert.deepEqual(satelliteSeams(undefined), []);
});

test('timelineSeries: lê area.sum.harm / .raw; NaN vira 0; alinhada a months', () => {
  const area = { months: [200011, 200012, 200101], sum: { harm: Float64Array.from([1, 2, NaN]), raw: [10, 20, 30] } };
  assert.deepEqual(timelineSeries(area, 'harm').map((p) => p.value), [1, 2, 0]);
  assert.deepEqual(timelineSeries(area, 'raw').map((p) => p.value), [10, 20, 30]);
  assert.equal(timelineSeries(area, 'raw')[1].ym, 200012);
  assert.equal(timelineSeries(area, 'raw')[2].date.toISOString(), '2001-01-01T00:00:00.000Z');
  assert.deepEqual(timelineSeries(null), []);
  assert.deepEqual(timelineSeries({ months: [200011], sum: {} }, 'harm'), []);
});

test('ymAtDate: arredonda ao mês mais próximo; indexFor trava nas pontas', () => {
  assert.equal(ymAtDate(new Date(Date.UTC(2006, 3, 1))), 200604);
  assert.equal(ymAtDate(new Date(Date.UTC(2006, 3, 20))), 200605);
  assert.equal(ymAtDate(new Date(Date.UTC(2006, 11, 25))), 200701); // vira o ano
  assert.equal(indexFor(months, 1990, 1), 0);
  assert.equal(indexFor(months, 2040, 1), months.length - 1);
  assert.equal(months[indexFor(months, 2006, 4)], 200604);
});

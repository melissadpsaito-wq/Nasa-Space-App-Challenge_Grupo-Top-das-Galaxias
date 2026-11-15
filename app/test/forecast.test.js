// Testes do leitor do Fire Outlook 2026 (D35, D48, contrato §9): `npm test` em app/.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { forecastUrl, skillUrl, validateForecastTile, ForecastStore, gateStatus, areaOutlook, outlookSummary } from '../src/forecast.js';

const parentOf = (c) => `${c.slice(0, 2)}x`;
const months = Array.from({ length: 12 }, (_, i) => 202601 + i);
const vec = (f) => Array.from({ length: 12 }, (_, i) => f(i + 1));

const cellA = { p: vec((m) => (m === 9 ? 80 : 20)), q10: vec((m) => (m === 9 ? 100 : 0)), q50: vec((m) => (m === 9 ? 300 : 10)), q90: vec((m) => (m === 9 ? 600 : 20)), normal: vec((m) => (m === 9 ? 200 : 10)) };
const cellB = { p: vec(() => 40), q10: vec(() => 0), q50: vec(() => 0), q90: vec(() => 10), normal: vec(() => 0) };
const tileA = { months, unit: 'frp_mw', cells: { A01: cellA, A02: cellB } };

function fakeFetch(files) {
  return async (url) => {
    const k = url.split('/data/')[1].replace('.json', '');
    if (!(k in files)) return { status: 404, ok: false };
    return { status: 200, ok: true, json: async () => structuredClone(files[k]) };
  };
}

test('urls', () => {
  assert.equal(forecastUrl('/app/', '82abc'), '/app/data/forecast_82abc.json');
  assert.equal(skillUrl('/app'), '/app/data/forecast_skill.json');
});

test('validateForecastTile: ok e erros', () => {
  assert.deepEqual(validateForecastTile(tileA), []);
  assert.match(validateForecastTile({ ...tileA, unit: 'focos' })[0], /unit/);
  const cross = structuredClone(tileA); cross.cells.A01.q10[8] = 999;
  assert.match(validateForecastTile(cross).join(), /cruzados/);
  const pct = structuredClone(tileA); pct.cells.A01.p[0] = 140;
  assert.match(validateForecastTile(pct).join(), /0–100/);
  const short = structuredClone(tileA); short.cells.A02.q50 = [1];
  assert.match(validateForecastTile(short).join(), /A02.q50/);
});

test('gateStatus', () => {
  assert.equal(gateStatus(null), 'none');
  assert.equal(gateStatus({ passes_gate: false }), 'failed');
  assert.equal(gateStatus({ passes_gate: 'true' }), 'failed'); // só booleano verdadeiro aprova
  assert.equal(gateStatus({ passes_gate: true }), 'ok');
});

test('areaOutlook: ponto, área (soma + P ponderada) e sem previsão', async () => {
  const store = new ForecastStore('/', fakeFetch({ forecast_A0x: tileA, forecast_skill: { passes_gate: true } }));
  const one = await areaOutlook(store, ['A01'], parentOf);
  assert.equal(one.unit, 'frp_mw');
  assert.equal(one.p[8], 0.8);
  assert.equal(one.q50[8], 30);
  assert.equal(one.normal[8], 20);

  const area = await areaOutlook(store, ['A01', 'A02', 'B01'], parentOf);   // B0x sem arquivo (404)
  assert.equal(area.cellsWith, 2);
  assert.equal(area.coverage, 2 / 3);
  assert.equal(area.q90[8], 61);                                            // 60 + 1
  // setembro: peso A = 20 + 30 = 50, peso B = 0 → P = 0,8
  assert.equal(area.p[8], 0.8);
  // janeiro: peso A = 1 + 1 = 2, B = 0 → 0,2
  assert.equal(area.p[0], 0.2);

  const none = await areaOutlook(store, ['B01'], parentOf);
  assert.equal(none.empty, true);
  assert.equal(gateStatus(await store.skill()), 'ok');
});

test('areaOutlook: pesos todos zero → média simples; sem normal → normal null', async () => {
  const z = { p: vec(() => 60), q10: vec(() => 0), q50: vec(() => 0), q90: vec(() => 0) };
  const t = { months, unit: 'detections', cells: { A01: z, A02: { ...z, p: vec(() => 20) } } };
  const store = new ForecastStore('/', fakeFetch({ forecast_A0x: t }));
  const o = await areaOutlook(store, ['A01', 'A02'], parentOf);
  assert.ok(Math.abs(o.p[0] - 0.4) < 1e-12);
  assert.equal(o.normal, null);
  assert.equal(gateStatus(await store.skill()), 'none');
});

test('outlookSummary', async () => {
  const store = new ForecastStore('/', fakeFetch({ forecast_A0x: tileA }));
  const s = outlookSummary(await areaOutlook(store, ['A01'], parentOf));
  assert.deepEqual(s.topP, { month: 9, p: 0.8 });
  assert.equal(s.peak.month, 9);
  assert.equal(s.total.q50, 30 + 11 * 1);
  assert.equal(s.total.normal, 20 + 11 * 1);
  assert.equal(s.monthsAbove, 1);
});

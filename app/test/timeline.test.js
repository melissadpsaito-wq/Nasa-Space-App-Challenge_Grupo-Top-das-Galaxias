import test from 'node:test';
import assert from 'node:assert/strict';
import { areaSeries } from '../src/data.js';
import { loadTimelineArea, freezeArea, indexFor, stepIndex, valuesAt, scaleMax, describeMonth, seams } from '../src/timeline.js';

// Tiles falsos no contrato §3 (valores × 10). Pai = 1ª letra da célula.
const months = [200011, 200012, 200101, 200102];
const src = ['TERRA', 'TERRA', 'TERRA', 'AQUA'];
const tileA = {
  months, src,
  cells: { a1: [10, 0, 50, 100], a2: [0, 0, 0, 0] },
  raw: { a1: [5, 0, 20, 40], a2: [0, 0, 0, 0] },
  low_conf: { a1: [1, 0, 0, 0], a2: [0, 0, 0, 0] },
};
const parentOf = (c) => c[0];
const storeWith = (tiles) => ({ get: async (p) => tiles[p] ?? null });

test('por célula: vetores ÷ 10, soma igual à do painel (areaSeries)', async () => {
  const store = storeWith({ a: tileA });
  const area = await loadTimelineArea(store, ['a1', 'a2'], parentOf);
  assert.deepEqual([...area.cells[0].harm], [1, 0, 5, 10]);
  assert.deepEqual([...area.cells[0].raw], [0.5, 0, 2, 4]);
  const panel = await areaSeries(store, ['a1', 'a2'], parentOf);
  assert.deepEqual([...area.sum.harm], [...panel.harm]);
  assert.deepEqual([...area.sum.raw], [...panel.raw]);
  const soma = area.months.map((_, k) => area.cells.reduce((a, c) => a + c.harm[k], 0));
  assert.deepEqual(soma, [...area.sum.harm]);
});

test('células sem fogo (ausente no tile ou tile 404) ficam na área com zeros', async () => {
  const area = await loadTimelineArea(storeWith({ a: tileA }), ['a1', 'a3', 'b1'], parentOf);
  assert.equal(area.cells.length, 3);
  assert.equal(area.cellsTotal, 3);
  assert.equal(area.cellsWithFire, 1);
  assert.deepEqual(area.cells.map((c) => c.hasFire), [true, false, false]);
  assert.ok(area.cells[1].harm.every((v) => v === 0));
  assert.ok(area.cells[2].raw.every((v) => v === 0));
});

test('todos os tiles 404 → área vazia', async () => {
  const area = await loadTimelineArea(storeWith({}), ['a1', 'b1'], parentOf);
  assert.equal(area.empty, true);
  assert.deepEqual(area.cells, []);
  assert.equal(area.cellsTotal, 2);
});

test('tiles com meses diferentes → erro (herdado de areaSeries)', async () => {
  const tileB = { ...tileA, months: [200012, 200101, 200102, 200103], cells: { b1: [1, 2, 3, 4] }, raw: {}, low_conf: {} };
  await assert.rejects(loadTimelineArea(storeWith({ a: tileA, b: tileB }), ['a1', 'b1'], parentOf), /meses diferentes/);
});

test('valuesAt e describeMonth', async () => {
  const area = await loadTimelineArea(storeWith({ a: tileA }), ['a1', 'a2'], parentOf);
  assert.deepEqual(valuesAt(area, 3), [10, 0]);
  assert.deepEqual(valuesAt(area, 3, 'raw'), [4, 0]);
  const d = describeMonth(area, 3);
  assert.equal(d.ym, 200102);
  assert.equal(d.src, 'AQUA');
  assert.equal(d.sum, 10);
  assert.equal(d.active, 1);
  assert.deepEqual(d.topCell, { id: 'a1', value: 10 });
  assert.equal(d.lowConf, false);
  assert.equal(describeMonth(area, 0).lowConf, true); // a1 tem fogo e low_conf no 1º mês
  assert.equal(describeMonth(area, 1).topCell, null);  // mês sem fogo
});

test('scaleMax: p98 dos valores ≥ 0,5, fixo, mínimo 1', () => {
  const cem = { cells: [{ harm: Array.from({ length: 100 }, (_, k) => k + 1) }, { harm: [0, 0, 0.2] }] };
  assert.equal(scaleMax(cem), 99);            // zeros e < 0,5 não entram
  assert.equal(scaleMax({ cells: [{ harm: [0.6, 0.7] }] }), 1); // piso 1
  assert.equal(scaleMax({ cells: [{ harm: [0, 0] }] }), 1);     // sem fogo
});

test('indexFor e stepIndex travam nas pontas', () => {
  assert.equal(indexFor(months, 2000, 11), 0);
  assert.equal(indexFor(months, 1999, 1), 0);
  assert.equal(indexFor(months, 2001, 1), 2);
  assert.equal(indexFor(months, 2030, 1), 3);
  assert.equal(indexFor([], 2001, 1), 0);
  assert.equal(stepIndex(0, -1, 4), 0);
  assert.equal(stepIndex(2, 5, 4), 3);
  assert.equal(stepIndex(1, 1, 4), 2);
});

test('seams: trechos contínuos Terra → Aqua → S-NPP', () => {
  const area = { src: ['TERRA', 'TERRA', 'AQUA', 'AQUA', 'AQUA', 'SNPP'] };
  assert.deepEqual(seams(area), [
    { src: 'TERRA', from: 0, to: 1 }, { src: 'AQUA', from: 2, to: 4 }, { src: 'SNPP', from: 5, to: 5 },
  ]);
});

test('freezeArea: mexer na seleção original não altera a Timeline; estrutura imutável', async () => {
  const data = await loadTimelineArea(storeWith({ a: tileA }), ['a1'], parentOf);
  const sel = { kind: 'area', cells: ['a1'], km2: 250 };
  const f = freezeArea(sel, data);
  sel.cells.push('zz'); sel.kind = 'point';
  assert.equal(f.sel.cells.length, 1);
  assert.equal(f.sel.kind, 'area');
  assert.ok(Object.isFrozen(f) && Object.isFrozen(f.sel) && Object.isFrozen(f.data));
  assert.throws(() => { f.sel.kind = 'x'; }, TypeError);
});

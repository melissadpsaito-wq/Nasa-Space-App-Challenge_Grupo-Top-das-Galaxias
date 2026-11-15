// Testes do leitor de tiles (sem rede, sem h3): `npm test` em app/.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { tileUrl, validateTile, TileStore, areaSeries, summarize } from '../src/data.js';

// h3 falso: pai = 2 primeiros caracteres + 'x' (A01, A02 → A0x)
const parentOf = (c) => `${c.slice(0, 2)}x`;

const tileA = {
  months: [201101, 201102, 201201, 201202],
  src: ['AQUA', 'AQUA', 'AQUA', 'SNPP'],
  cells: { A01: [10, 0, 25, 40], A02: [5, 5, 0, 0] },
  raw: { A01: [2, 0, 5, 40], A02: [1, 1, 0, 0] },
  lo: { A01: [8, 0, 20, 40], A02: [5, 5, 0, 0] },
  hi: { A01: [12, 0, 30, 40], A02: [5, 5, 0, 0] },
  low_conf: { A01: [0, 0, 1, 0], A02: [1, 1, 0, 0] },
};
const tileB = { ...tileA, cells: { B01: [0, 0, 0, 10] }, raw: { B01: [0, 0, 0, 10] }, lo: {}, hi: {}, low_conf: {} };

function fakeFetch(files) {
  const calls = [];
  const fn = async (url) => {
    calls.push(url);
    const k = url.split('harm_')[1]?.replace('.json', '');
    if (!(k in files)) return { status: 404, ok: false };
    return { status: 200, ok: true, json: async () => structuredClone(files[k]) };
  };
  fn.calls = calls;
  return fn;
}

test('tileUrl respeita a base do Vite', () => {
  assert.equal(tileUrl('/repo/', 'A0x'), '/repo/data/harm_A0x.json');
  assert.equal(tileUrl('/repo', 'A0x'), '/repo/data/harm_A0x.json');
});

test('validateTile aceita tile no contrato e acusa vetor desalinhado', () => {
  assert.deepEqual(validateTile(tileA), []);
  const bad = structuredClone(tileA); bad.cells.A01.pop();
  assert.match(validateTile(bad).join(), /cells\[A01\]/);
  const frac = structuredClone(tileA); frac.raw.A02[0] = 1.5;
  assert.match(validateTile(frac).join(), /não inteiro/);
});

test('uma célula: divide por 10 e mantém raw separado', async () => {
  const s = await areaSeries(new TileStore('/', fakeFetch({ A0x: tileA })), ['A01'], (c) => 'A0x');
  assert.deepEqual([...s.harm], [1, 0, 2.5, 4]);
  assert.deepEqual([...s.raw], [0.2, 0, 0.5, 4]);
  assert.deepEqual([...s.low_conf], [0, 0, 1, 0]);
  assert.equal(s.cellsWithFire, 1);
});

test('área em 2 tiles soma; célula omitida = sem fogo; pai 404 = sem fogo', async () => {
  const f = fakeFetch({ A01: tileA, B01: tileB });
  const store = new TileStore('/', f);
  const cellToParent = (c) => c; // cada célula num tile próprio só para o teste
  const s = await areaSeries(store, ['A01', 'B01', 'Zzz'], cellToParent);
  // A01 está no tile "A01", mas a chave lá é A01 → 1 célula; B01 idem; Zzz → 404
  assert.deepEqual([...s.harm], [1, 0, 2.5, 5]);
  assert.equal(s.cellsWithFire, 2);
  assert.equal(s.cellsTotal, 3);
  // lo/hi ausentes em B01 → usam o próprio harm (lo = hi, série provisória)
  assert.deepEqual([...s.lo], [0.8, 0, 2, 5]);
});

test('cache: o mesmo pai é baixado uma vez', async () => {
  const f = fakeFetch({ A0x: tileA });
  const store = new TileStore('/', f);
  await areaSeries(store, ['A01', 'A02'], parentOf);
  await areaSeries(store, ['A01'], parentOf);
  assert.equal(f.calls.length, 1);
});

test('ponto fora do fogo devolve empty', async () => {
  const s = await areaSeries(new TileStore('/', fakeFetch({})), ['X99'], parentOf);
  assert.equal(s.empty, true);
  assert.equal(summarize(s), null);
});

test('tile fora do contrato gera erro claro', async () => {
  const bad = structuredClone(tileA); bad.src = ['AQUA'];
  await assert.rejects(areaSeries(new TileStore('/', fakeFetch({ A0x: bad })), ['A01'], parentOf), /fora do contrato/);
});

test('summarize: totais, pico e anos', async () => {
  const s = await areaSeries(new TileStore('/', fakeFetch({ A0x: tileA })), ['A01', 'A02'], parentOf);
  const r = summarize(s);
  assert.equal(r.totalHarm, 1.5 + 0.5 + 2.5 + 4);
  assert.equal(r.peak.ym, 201202);
  assert.equal(r.peak.src, 'SNPP');
  assert.deepEqual([...r.annual.keys()], [2011, 2012]);
});

import { periodIndex, slicePeriod, cellTotals } from '../src/data.js';

test('periodIndex: recorte inclusivo, invertido e fora da faixa', () => {
  const m = tileA.months; // 201101, 201102, 201201, 201202
  assert.deepEqual(periodIndex(m, 201102, 201201), [1, 2]);
  assert.deepEqual(periodIndex(m, 201201, 201102), [1, 2]);
  assert.deepEqual(periodIndex(m, 200001, 209912), [0, 3]);
  assert.equal(periodIndex(m, 201103, 201112), null);
});

test('slicePeriod recorta todas as séries juntas', async () => {
  const s = await areaSeries(new TileStore('/', fakeFetch({ A0x: tileA })), ['A01'], parentOf);
  const p = slicePeriod(s, 201201, 201202);
  assert.deepEqual(p.months, [201201, 201202]);
  assert.deepEqual([...p.harm], [2.5, 4]);
  assert.deepEqual(p.src, ['AQUA', 'SNPP']);
  assert.equal(slicePeriod(s, 201103, 201112).empty, true);
});

test('cellTotals: soma do período por célula, omite zeros', () => {
  const h = cellTotals(tileA, 2, 3, 'cells');
  assert.equal(h.get('A01'), 6.5);
  assert.equal(h.has('A02'), false);
  assert.equal(cellTotals(tileA, 0, 1, 'raw').get('A02'), 0.2);
});

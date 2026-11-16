// Ponto fora do Brasil (sem tile): sem erro "Unexpected token '<'" e com flag outOfScope (sem rede, sem h3).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TileStore, areaSeries, isMissingTile } from '../src/data.js';
import { ClimaStore, areaClimatologia } from '../src/climatologia.js';
import { loadTimelineArea } from '../src/timeline.js';

const tileA = {
  months: [201101, 201102],
  src: ['AQUA', 'AQUA'],
  cells: { A01: [10, 0] },
  raw: { A01: [2, 0] },
};
const climaA = { n_years: 10, cells: { A01: [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3] } };

// Imita o `npm run dev`/`preview`: arquivo inexistente volta 200 com o index.html.
const htmlFallback = () => ({
  status: 200, ok: true,
  headers: new Headers({ 'content-type': 'text/html' }),
  json: async () => { throw new SyntaxError("Unexpected token '<', \"<!doctype \"... is not valid JSON"); },
});
const jsonOk = (body) => ({
  status: 200, ok: true,
  headers: new Headers({ 'content-type': 'application/json' }),
  json: async () => structuredClone(body),
});
function fetchWith(files, missing) {
  return async (url) => {
    const k = url.split('/').pop().replace(/^(harm|climatologia)_/, '').replace('.json', '');
    return k in files ? jsonOk(files[k]) : missing();
  };
}
const notFound = () => ({ status: 404, ok: false });
const parentOf = (c) => `${c.slice(0, 2)}x`;

test('isMissingTile: 404 e fallback HTML contam como tile ausente; JSON não', () => {
  assert.equal(isMissingTile(notFound()), true);
  assert.equal(isMissingTile(htmlFallback()), true);
  assert.equal(isMissingTile(jsonOk({})), false);
  assert.equal(isMissingTile({ status: 200, ok: true }), false); // mock sem headers
  assert.equal(isMissingTile({ status: 500, ok: false, headers: new Headers({ 'content-type': 'text/html' }) }), false);
});

for (const [nome, missing] of [['fallback HTML do Vite', htmlFallback], ['404', notFound]]) {
  test(`fora do escopo (${nome}): histórico, timeline e previsão sem erro e com outOfScope`, async () => {
    const store = new TileStore('/', fetchWith({ A0x: tileA }, missing));
    const clima = new ClimaStore('/', fetchWith({ A0x: climaA }, missing));

    const s = await areaSeries(store, ['Z01'], parentOf);
    assert.equal(s.empty, true);
    assert.equal(s.outOfScope, true);

    const tl = await loadTimelineArea(store, ['Z01'], parentOf);
    assert.equal(tl.empty, true);
    assert.equal(tl.outOfScope, true);

    const c = await areaClimatologia(clima, ['Z01'], parentOf);
    assert.equal(c.empty, true);
    assert.equal(c.outOfScope, true);
  });
}

test('tile existe mas a célula não: "sem fogo", não "fora do escopo" (contrato §11)', async () => {
  const store = new TileStore('/', fetchWith({ A0x: tileA }, htmlFallback));
  const s = await areaSeries(store, ['A09'], parentOf); // pai A0x existe; A09 não está nele
  assert.equal(s.empty, true);
  assert.equal(s.outOfScope, false);
});

test('área metade dentro, metade fora: soma só a parte com tile', async () => {
  const store = new TileStore('/', fetchWith({ A0x: tileA }, htmlFallback));
  const s = await areaSeries(store, ['A01', 'Z01'], parentOf);
  assert.equal(s.outOfScope, false);
  assert.deepEqual([...s.harm], [1, 0]);

  const clima = new ClimaStore('/', fetchWith({ A0x: climaA }, htmlFallback));
  const c = await areaClimatologia(clima, ['A01', 'Z01'], parentOf);
  assert.equal(c.outOfScope, false);
  assert.equal(c.cellsWithData, 1);
});

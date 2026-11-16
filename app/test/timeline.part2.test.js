// Testes da Parte 2 (4.4): peakIndex, parseHash, formatHash, satLabel. Reescritos: não estavam no repositório.
import test from 'node:test';
import assert from 'node:assert/strict';
import { peakIndex, parseHash, formatHash, satLabel } from '../src/timeline.js';

test('peakIndex: mês de maior valor da área, 1º em empate, por modo; vazio = 0', () => {
  const area = { sum: { harm: [1, 5, 5, 2], raw: [9, 1, 1, 1] } };
  assert.equal(peakIndex(area, 'harm'), 1);
  assert.equal(peakIndex(area, 'raw'), 0);
  assert.equal(peakIndex(area), 1); // padrão: harm
  assert.equal(peakIndex({ sum: { harm: [] } }, 'harm'), 0);
  assert.equal(peakIndex({}, 'harm'), 0);
});

test('parseHash: "#t=AAAA-MM" → AAAAMM; qualquer outra coisa → null', () => {
  assert.equal(parseHash('#t=2004-09'), 200409);
  assert.equal(parseHash('t=2004-9'), 200409); // sem "#" e mês de 1 dígito
  assert.equal(parseHash('#t=2004-13'), null);
  assert.equal(parseHash('#t=2004-00'), null);
  assert.equal(parseHash('#t=04-09'), null);
  assert.equal(parseHash('#x=2004-09'), null);
  assert.equal(parseHash(''), null);
  assert.equal(parseHash(null), null);
  assert.equal(parseHash(undefined), null);
});

test('formatHash: AAAAMM → "t=AAAA-MM" (sem "#"), ida e volta com parseHash', () => {
  assert.equal(formatHash(200409), 't=2004-09');
  assert.equal(formatHash(201112), 't=2011-12');
  for (const ym of [200011, 200206, 201201, 202512]) assert.equal(parseHash(`#${formatHash(ym)}`), ym);
});

test('satLabel: nome de exibição do satélite; desconhecido volta como veio; ausente = "—"', () => {
  assert.equal(satLabel('TERRA'), 'Terra');
  assert.equal(satLabel('AQUA'), 'Aqua');
  assert.equal(satLabel('SNPP'), 'S-NPP');
  assert.equal(satLabel('N20'), 'NOAA-20');
  assert.equal(satLabel('XYZ'), 'XYZ');
  assert.equal(satLabel(undefined), '—');
  assert.equal(satLabel(null), '—');
});

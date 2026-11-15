// Calendário ano × mês da área no período escolhido (Guia §4.3). Cividis, mesmo domínio para bruto e harmonizado.
import * as Plot from '@observablehq/plot';
import { t, monthName, fmt } from './i18n.js';
import { MIN_FIRE } from './analytics.js';

export const COLOR = { scheme: 'cividis', reverse: true, type: 'sqrt' };
// Abaixo disso o mês/hexágono aparece como "sem fogo" (só exibição; o dado não muda).
export const MIN_SHOW = MIN_FIRE;

/** s = série já recortada ao período (slicePeriod). mode = 'harm' | 'raw'. */
export function renderCalendar(el, s, mode) {
  el.replaceChildren();
  if (s.empty) return;
  const rows = s.months.map((ym, k) => ({
    year: Math.floor(ym / 100), month: ym % 100,
    value: mode === 'raw' ? s.raw[k] : s.harm[k],
    harm: s.harm[k], raw: s.raw[k], src: s.src[k], low: s.low_conf[k] === 1,
  }));
  // Mesmo domínio nos dois modos: é o que faz o salto de 2012 aparecer (bruto) e sumir (harmonizado).
  const vmax = Math.max(1, ...rows.map((r) => Math.max(r.harm, r.raw)));
  const years = [...new Set(rows.map((r) => r.year))];
  const narrow = el.clientWidth < 520;

  const plot = Plot.plot({
    width: Math.max(320, el.clientWidth),
    height: Math.max(160, 22 + years.length * 18),
    marginLeft: 44, marginTop: 24,
    x: { domain: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], tickFormat: (m) => (narrow ? monthName(m)[0] : monthName(m)), label: null, axis: 'top' },
    y: { domain: years, label: null, tickFormat: (y) => (years.length > 14 && y % 2 ? '' : String(y)) },
    color: { ...COLOR, domain: [0, vmax], legend: true, label: t('cal.legend') },
    marks: [
      // fundo cinza = menos de MIN_SHOW detecção no mês (inclui o termo aditivo minúsculo do M1, R22); valor exato no tooltip
      Plot.cell(rows, {
        x: 'month', y: 'year', fill: '#ebe8e0', inset: 0.5,
        title: (r) => `${monthName(r.month)} ${r.year}\n${t('f.harm')}: ${fmt(r.harm)}\n${t('f.raw')}: ${fmt(r.raw)}\n${r.src}${r.low ? `\n${t('panel.lowconf')}` : ''}`,
        tip: true,
      }),
      Plot.cell(rows.filter((r) => r.value >= MIN_SHOW), { x: 'month', y: 'year', fill: 'value', inset: 0.5 }),
      Plot.dot(rows.filter((r) => r.low), { x: 'month', y: 'year', r: 2.2, stroke: '#fff', fill: 'none', strokeWidth: 1.2 }),
    ],
  });
  el.append(plot);
}

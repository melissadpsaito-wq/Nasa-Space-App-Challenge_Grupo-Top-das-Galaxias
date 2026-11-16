// Calendário ano × mês da área no período escolhido (Guia §4.3). Cividis, mesmo domínio para bruto e harmonizado.
import * as Plot from '@observablehq/plot';
import { t, monthName, fmt } from './i18n.js';
import { MIN_FIRE } from './analytics.js';

// Escala do novo visual: azul claro → azul escuro → areia (maior concentração). Só aparência; o domínio e a raiz quadrada não mudam.
const STOPS = ['#e6f3fc', '#a9d7f6', '#5aaee8', '#2a6fb0', '#f2c14e'].map((h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)));
export function ramp(u) {
  const x = Math.min(1, Math.max(0, u)) * (STOPS.length - 1), i = Math.min(STOPS.length - 2, Math.floor(x)), f = x - i;
  return `rgb(${STOPS[i].map((v, k) => Math.round(v + (STOPS[i + 1][k] - v) * f)).join(',')})`;
}
export const COLOR = { interpolate: ramp, type: 'sqrt' };
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

  // Legibilidade (15/11): linhas de 20 px e todos os anos no eixo quando há largura; "0" da legenda não corta (marginLeft).
  const rowH = narrow ? 18 : 20;
  const plot = Plot.plot({
    width: Math.max(240, el.clientWidth),
    height: Math.max(160, 22 + years.length * rowH),
    marginLeft: 44, marginTop: 24,
    x: { domain: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], tickFormat: (m) => (narrow ? monthName(m)[0] : monthName(m)), label: null, axis: 'top' },
    y: { domain: years, label: null, tickFormat: (y) => (narrow && years.length > 14 && y % 2 ? '' : String(y)) },
    color: { ...COLOR, domain: [0, vmax], legend: true, label: t('cal.legend'), marginLeft: 8 },
    marks: [
      // fundo cinza = menos de MIN_SHOW detecção no mês (inclui o termo aditivo minúsculo do M1, R22); valor exato no tooltip
      Plot.cell(rows, {
        x: 'month', y: 'year', fill: '#e9eff5', inset: 0.5,
        title: (r) => `${monthName(r.month)} ${r.year}\n${t('f.harm')}: ${fmt(r.harm)}\n${t('f.raw')}: ${fmt(r.raw)}\n${r.src}${r.low ? `\n${t('panel.lowconf')}` : ''}`,
        tip: true,
      }),
      Plot.cell(rows.filter((r) => r.value >= MIN_SHOW), { x: 'month', y: 'year', fill: 'value', inset: 0.5 }),
      Plot.dot(rows.filter((r) => r.low), { x: 'month', y: 'year', r: 2.2, stroke: '#fff', fill: 'none', strokeWidth: 1.2 }),
    ],
  });
  el.append(plot);
}

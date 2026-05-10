import { describe, expect, it } from 'vitest';
import {
  buildDataZoom,
  buildLegend,
  formatChartDate,
  formatLiters,
  formatRub,
  formatRubPerLiter,
  getResponsiveChartHeight,
} from './chartOptions';

describe('chartOptions', () => {
  it('formats chart values in Russian business units', () => {
    expect(formatChartDate('2026-05-01', false)).toBe('01.05');
    expect(formatLiters(12000)).toContain('12');
    expect(formatLiters(12000)).toContain('л');
    expect(formatRub(59.75)).toBe('59,75 ₽');
    expect(formatRubPerLiter(4.9)).toBe('4,9 ₽/л');
  });

  it('keeps responsive chart defaults centralized', () => {
    expect(getResponsiveChartHeight(true)).toBe(300);
    expect(getResponsiveChartHeight(false)).toBe(400);
    expect(buildDataZoom(true)).toEqual([]);
    expect(buildDataZoom(false)).toHaveLength(1);
  });

  it('hides noisy overlay series only on compact charts', () => {
    expect(buildLegend(['Продажи', 'Инд 1'], true, ['Инд 1'])).toMatchObject({
      selected: { 'Инд 1': false },
    });
    expect(buildLegend(['Продажи', 'Инд 1'], false, ['Инд 1'])).not.toHaveProperty('selected');
  });
});

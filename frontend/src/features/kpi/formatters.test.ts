import { describe, expect, it } from 'vitest';
import { formatLiters, formatPercent, formatRub, toIsoDateInput } from './formatters';

describe('kpi formatters', () => {
  it('formats rubles and liters for ru locale', () => {
    expect(formatRub(1234.56)).toContain('₽');
    expect(formatLiters(12000)).toContain('л');
  });

  it('formats percent with nullable value', () => {
    expect(formatPercent(10.43)).toContain('%');
    expect(formatPercent(null)).toBe('N/A');
  });

  it('converts date to input format', () => {
    expect(toIsoDateInput(new Date('2026-03-29T00:00:00.000Z'))).toBe('2026-03-29');
  });
});


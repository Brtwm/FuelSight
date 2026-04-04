import { describe, expect, it } from 'vitest';
import { buildDefaultDateRange, resolveAnalyticsFilters, toSearchParams } from './urlFilters';

describe('analytics url filters', () => {
  it('resolves defaults when params are missing', () => {
    const defaults = {
      product_code: 'AI_95',
      date_from: '2026-03-01',
      date_to: '2026-03-30',
    };
    const resolved = resolveAnalyticsFilters(new URLSearchParams(), defaults);
    expect(resolved.product_code).toBe('AI_95');
    expect(resolved.granularity).toBe('day');
    expect(resolved.date_from).toBe('2026-03-01');
  });

  it('keeps valid params and serializes them back', () => {
    const params = new URLSearchParams(
      'product_code=dt_s&date_from=2026-02-01&date_to=2026-02-28&granularity=week',
    );
    const resolved = resolveAnalyticsFilters(params, {
      product_code: 'AI_95',
      date_from: '2026-03-01',
      date_to: '2026-03-30',
    });

    expect(resolved.product_code).toBe('DT_S');
    expect(resolved.granularity).toBe('week');
    expect(toSearchParams(resolved).toString()).toContain('product_code=DT_S');
    expect(toSearchParams(resolved).toString()).toContain('granularity=week');
  });

  it('builds default range for 30 calendar days', () => {
    const range = buildDefaultDateRange(new Date('2026-03-30T00:00:00.000Z'));
    expect(range.date_to).toBe('2026-03-30');
    expect(range.date_from).toBe('2026-03-01');
  });
});

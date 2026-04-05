import { describe, expect, it } from 'vitest';
import { buildDefaultNewsRange, resolveNewsFilters, toSearchParams } from './urlFilters';

describe('news url filters', () => {
  it('resolves defaults for empty params', () => {
    const resolved = resolveNewsFilters(new URLSearchParams(), {
      date_from: '2026-03-01',
      date_to: '2026-03-30',
    });
    expect(resolved.period_type).toBe('daily');
    expect(resolved.q).toBe('');
    expect(resolved.topic).toBe('');
  });

  it('keeps valid params and serializes them back', () => {
    const params = new URLSearchParams(
      'period_type=weekly&q=логистика&date_from=2026-03-01&date_to=2026-03-31&topic=diesel',
    );
    const resolved = resolveNewsFilters(params, {
      date_from: '2026-03-01',
      date_to: '2026-03-30',
    });
    const serialized = toSearchParams(resolved).toString();
    expect(resolved.period_type).toBe('weekly');
    expect(serialized).toContain('q=%D0%BB%D0%BE%D0%B3%D0%B8%D1%81%D1%82%D0%B8%D0%BA%D0%B0');
    expect(serialized).toContain('topic=diesel');
  });

  it('builds default range for 30 days', () => {
    const range = buildDefaultNewsRange(new Date('2026-04-05T00:00:00.000Z'));
    expect(range.date_to).toBe('2026-04-05');
    expect(range.date_from).toBe('2026-03-07');
  });
});

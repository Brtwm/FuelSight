import { describe, expect, it } from 'vitest';
import { generateHistorySchema } from './generateHistorySchema';

describe('generateHistorySchema', () => {
  it('accepts valid payload', () => {
    const result = generateHistorySchema.safeParse({
      startDate: '2025-01-01',
      endDate: '2025-12-31',
      products: ['AI_92', 'DT_S'],
      seed: 42,
      replaceExisting: false,
    });

    expect(result.success).toBe(true);
  });

  it('rejects reversed date range', () => {
    const result = generateHistorySchema.safeParse({
      startDate: '2026-12-31',
      endDate: '2026-01-01',
      products: ['AI_95'],
      seed: 42,
      replaceExisting: false,
    });

    expect(result.success).toBe(false);
  });

  it('rejects empty products', () => {
    const result = generateHistorySchema.safeParse({
      startDate: '2025-01-01',
      endDate: '2025-12-31',
      products: [],
      seed: 42,
      replaceExisting: false,
    });

    expect(result.success).toBe(false);
  });
});


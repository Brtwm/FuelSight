import { describe, expect, it } from 'vitest';

import { formatImportDisplayLabel } from './importDisplayLabel';

describe('formatImportDisplayLabel', () => {
  it('formats known display label codes', () => {
    expect(formatImportDisplayLabel('sales', 'sales')).toBe('Продажи');
    expect(formatImportDisplayLabel('purchases', 'purchases')).toBe('Закупки');
    expect(formatImportDisplayLabel('initial_history', 'historical_data')).toBe('Начальная история');
  });

  it('falls back to raw entity type when code is missing', () => {
    expect(formatImportDisplayLabel(null, 'historical_data')).toBe('historical_data');
  });
});


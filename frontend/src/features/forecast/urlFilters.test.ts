import { describe, expect, it } from 'vitest';
import { resolveForecastFilters, toSearchParams } from './urlFilters';

describe('forecast url filters', () => {
  it('applies defaults for missing query params', () => {
    const resolved = resolveForecastFilters(new URLSearchParams(), {
      product_code: 'AI_95',
      horizon_days: 7,
    });

    expect(resolved.product_code).toBe('AI_95');
    expect(resolved.horizon_days).toBe(7);
    expect(resolved.scenario_enabled).toBe(false);
    expect(resolved.retail_price_delta_pct).toBe(0);
  });

  it('normalizes and serializes scenario filters', () => {
    const resolved = resolveForecastFilters(
      new URLSearchParams('product_code=dt_w&horizon_days=30&scenario_enabled=1&retail_price_delta_pct=2.5'),
      { product_code: 'AI_95', horizon_days: 7 },
    );

    expect(resolved.product_code).toBe('DT_W');
    expect(resolved.horizon_days).toBe(30);
    expect(resolved.scenario_enabled).toBe(true);
    expect(resolved.retail_price_delta_pct).toBe(2.5);

    const params = toSearchParams(resolved).toString();
    expect(params).toContain('product_code=DT_W');
    expect(params).toContain('horizon_days=30');
    expect(params).toContain('scenario_enabled=1');
  });
});


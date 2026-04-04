import { describe, expect, it, vi } from 'vitest';
import { fetchAnalyticsAnomalies, fetchMarginAnalytics, fetchSalesAnalytics } from './analytics';

describe('analytics api client', () => {
  it('serializes sales filters and fetches data', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            product_code: 'AI_95',
            granularity: 'day',
            series: [],
            seasonality: { by_weekday: [], by_month: [] },
            comparisons: { mom_pct: null, yoy_pct: null },
          },
          error: null,
          meta: {},
        }),
        { status: 200 },
      ),
    );

    await fetchSalesAnalytics(authFetch, {
      product_code: 'AI_95',
      date_from: '2026-03-01',
      date_to: '2026-03-31',
      granularity: 'week',
    });

    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/analytics/sales');
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('product_code=AI_95');
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('granularity=week');
  });

  it('fetches margin and anomalies', async () => {
    const authFetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              product_code: 'DT_S',
              granularity: 'month',
              series: [],
              threshold_rub_per_liter: 3,
              below_threshold_days: 0,
              low_margin_days: [],
            },
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: [
              {
                date: '2026-03-15',
                product_code: 'DT_S',
                metric: 'margin',
                severity: 'high',
                actual_value: 1.2,
                expected_range: [3, 4.5],
                possible_reasons: ['Рост закупочной цены'],
                target_path: '/analytics/margin',
              },
            ],
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      );

    const margin = await fetchMarginAnalytics(authFetch, {
      product_code: 'DT_S',
      granularity: 'month',
    });
    const anomalies = await fetchAnalyticsAnomalies(authFetch, {
      metric: 'margin',
      product_code: 'DT_S',
    });

    expect(margin.product_code).toBe('DT_S');
    expect(anomalies).toHaveLength(1);
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/analytics/margin');
    expect(String(authFetch.mock.calls[1]?.[0])).toContain('/analytics/anomalies');
    expect(String(authFetch.mock.calls[1]?.[0])).toContain('metric=margin');
  });
});

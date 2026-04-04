import { describe, expect, it, vi } from 'vitest';
import { fetchKpiAlerts, fetchKpiSnapshot, fetchKpiSummary } from './kpi';

describe('kpi api client', () => {
  it('fetches summary and supports null data', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: null,
          error: null,
          meta: {},
        }),
        { status: 200 },
      ),
    );

    const data = await fetchKpiSummary(authFetch, {
      date_from: '2026-03-01',
      date_to: '2026-03-31',
      product_code: 'AI_95',
    });

    expect(data).toBeNull();
    expect(authFetch).toHaveBeenCalledTimes(1);
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/kpi/summary');
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('product_code=AI_95');
  });

  it('fetches alerts and snapshot', async () => {
    const authFetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: [
              {
                type: 'low_margin',
                severity: 'high',
                date: '2026-03-20',
                product_code: 'AI_92',
                message: 'Маржа ниже порога',
                metric: 'margin',
                actual_value: 2.1,
                expected_range: [3, 4.5],
                target_path: '/analytics/margin',
              },
            ],
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: [{ date: '2026-03-20', volume_liters: 1000, avg_retail_price_rub: 59.2 }],
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      );

    const alerts = await fetchKpiAlerts(authFetch, { severity: 'high' });
    const snapshot = await fetchKpiSnapshot(authFetch);

    expect(alerts).toHaveLength(1);
    expect(alerts[0]?.severity).toBe('high');
    expect(snapshot).toHaveLength(1);
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/kpi/alerts');
    expect(String(authFetch.mock.calls[1]?.[0])).toContain('/kpi/snapshot');
  });
});


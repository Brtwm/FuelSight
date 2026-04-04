import { describe, expect, it, vi } from 'vitest';
import { fetchLatestBacktest, fetchLatestForecast, runBacktest, runForecast } from './forecast';

describe('forecast api client', () => {
  it('runs forecast with scenario payload', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            model_status: 'active',
            scenario_name: 'what_if_price',
            scenario_params: { retail_price_delta_pct: 2.5 },
            forecast_points: [],
            drivers: [],
          },
          error: null,
          meta: {},
        }),
        { status: 200 },
      ),
    );

    await runForecast(authFetch, {
      product_code: 'AI_95',
      horizon_days: 7,
      scenario: { retail_price_delta_pct: 2.5 },
    });

    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/forecasts/run');
    const body = String(authFetch.mock.calls[0]?.[1]?.body);
    expect(body).toContain('"retail_price_delta_pct":2.5');
  });

  it('builds query for latest forecast and backtest', async () => {
    const authFetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: null,
            error: null,
            meta: { empty_state: 'Нет данных' },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: null,
            error: null,
            meta: { empty_state: 'Нет данных' },
          }),
          { status: 200 },
        ),
      );

    await fetchLatestForecast(authFetch, { product_code: 'DT_S', horizon_days: 30 });
    await fetchLatestBacktest(authFetch, { product_code: 'DT_S', horizon_days: 30 });

    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/forecasts/latest');
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('horizon_days=30');
    expect(String(authFetch.mock.calls[1]?.[0])).toContain('/backtests/latest');
  });

  it('runs backtest with default rolling window', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            product_code: 'AI_92',
            horizon_days: 7,
            model_type: 'catboost',
            window_type: 'rolling',
            metrics: { mae: 1, rmse: 1, smape: 1 },
            comparison: {},
            trained_at: '2026-04-04T21:00:00+00:00',
            model_version: '20260404210000',
          },
          error: null,
          meta: {},
        }),
        { status: 200 },
      ),
    );

    await runBacktest(authFetch, { product_code: 'AI_92', horizon_days: 7 });
    const body = String(authFetch.mock.calls[0]?.[1]?.body);
    expect(body).toContain('"window_type":"rolling"');
  });
});


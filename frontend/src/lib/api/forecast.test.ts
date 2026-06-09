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

    const result = await runBacktest(authFetch, { product_code: 'AI_92', horizon_days: 7 });
    const body = String(authFetch.mock.calls[0]?.[1]?.body);
    expect(body).toContain('"window_type":"rolling"');
    expect(result.validation_summary).toBeUndefined();
  });

  it('preserves nested validation summary from latest backtest responses', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            window_type: 'rolling',
            metrics: { mae: 120.2, rmse: 150.3, smape: 4.4 },
            comparison: {
              catboost: { mae: 120.2, rmse: 150.3, smape: 4.4 },
              seasonal_naive: { mae: 170, rmse: 210, smape: 5.8 },
            },
            trained_at: '2026-04-04T21:00:00+00:00',
            model_version: '20260404210000',
            validation_summary: {
              status: 'OK',
              status_reason: 'CatBoost is evaluated on the test period.',
              train_period: { start: '2025-01-01', end: '2025-12-31' },
              test_period: { start: '2026-01-01', end: '2026-01-30' },
              observations: { total: 395, train: 365, test: 30 },
              metrics: {
                catboost: { mae: 120.2, rmse: 150.3, smape: 4.4 },
                seasonal_naive: { mae: 170, rmse: 210, smape: 5.8 },
                improvement: { mae_pct: 29.29, rmse_pct: 28.43, smape_pct: 24.14 },
              },
              series: [
                {
                  date: '2026-01-01',
                  actual: 100,
                  catboost_prediction: 98,
                  seasonal_naive_prediction: 95,
                },
              ],
            },
          },
          error: null,
          meta: {},
        }),
        { status: 200 },
      ),
    );

    const result = await fetchLatestBacktest(authFetch, {
      product_code: 'AI_95',
      horizon_days: 7,
    });

    expect(result?.validation_summary?.status).toBe('OK');
    expect(result?.validation_summary?.metrics?.improvement?.smape_pct).toBe(24.14);
    expect(result?.validation_summary?.series?.[0]).toEqual({
      date: '2026-01-01',
      actual: 100,
      catboost_prediction: 98,
      seasonal_naive_prediction: 95,
    });
  });
});

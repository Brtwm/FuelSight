import { expect, test } from '@playwright/test';

type EnvelopePayload = {
  data: unknown;
  error: null | { code: string; message: string; details?: Record<string, unknown> };
  meta: Record<string, unknown>;
};

function envelope(data: unknown, meta: Record<string, unknown> = {}): EnvelopePayload {
  return {
    data,
    error: null,
    meta: { request_id: 'e2e-request-id', ...meta },
  };
}

test('admin happy-path: login -> import/demo -> dashboard -> sales -> margin -> forecast', async ({ page }) => {
  const state = {
    demoGenerated: false,
    forecastRan: false,
  };

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method().toUpperCase();

    const json = (payload: EnvelopePayload, status = 200) =>
      route.fulfill({
        status,
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(payload),
      });

    if (method === 'POST' && path === '/api/v1/auth/refresh') {
      return json(
        {
          data: null,
          error: { code: 'invalid_refresh_token', message: 'refresh token missing' },
          meta: { request_id: 'e2e-request-id' },
        },
        401,
      );
    }

    if (method === 'POST' && path === '/api/v1/auth/login') {
      return json(
        envelope({
          access_token: 'e2e-access-token',
          token_type: 'bearer',
          expires_in: 1800,
          user: {
            id: '8f602177-c0fc-43d9-9ef6-f81497165a72',
            email: 'admin@fuelsight.local',
            role: 'admin',
            display_name: 'FuelSight Admin',
          },
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/auth/me') {
      return json(
        envelope({
          id: '8f602177-c0fc-43d9-9ef6-f81497165a72',
          email: 'admin@fuelsight.local',
          role: 'admin',
          display_name: 'FuelSight Admin',
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/health') {
      return json(
        envelope({
          ok: true,
          app_env: 'local',
          version: '0.1.0',
          enable_llm: false,
          timestamp: '2026-04-06T10:00:00+00:00',
        }),
      );
    }

    if (method === 'POST' && path === '/api/v1/import/generate-demo') {
      state.demoGenerated = true;
      return json(
        envelope(
          {
            job_id: '63d4060b-d4eb-4899-a773-5a164d096f5d',
            entity_type: 'historical_data',
            status: 'queued',
          },
          { queued: true },
        ),
        202,
      );
    }

    if (method === 'GET' && path === '/api/v1/import/jobs') {
      return json(
        envelope(
          state.demoGenerated
            ? [
                {
                  id: '63d4060b-d4eb-4899-a773-5a164d096f5d',
                  entity_type: 'historical_data',
                  source_type: 'generated',
                  file_name: null,
                  status: 'completed',
                  rows_total: 1460,
                  rows_success: 1460,
                  rows_failed: 0,
                  error_report_path: null,
                  started_at: '2026-04-06T10:00:00+00:00',
                  finished_at: '2026-04-06T10:00:03+00:00',
                },
              ]
            : [],
          { count: state.demoGenerated ? 1 : 0 },
        ),
      );
    }

    if (method === 'GET' && path === '/api/v1/kpi/summary') {
      if (!state.demoGenerated) {
        return json(envelope(null, { empty_state: 'Нет данных' }));
      }
      return json(
        envelope({
          sales_volume_liters: 152340.0,
          revenue_rub: 8876500.45,
          gross_margin_rub: 925340.11,
          gross_margin_pct: 10.43,
          low_margin_days: 3,
          anomaly_count: 2,
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/kpi/alerts') {
      return json(envelope([]));
    }

    if (method === 'GET' && path === '/api/v1/kpi/snapshot') {
      return json(
        envelope([
          { date: '2026-04-04', volume_liters: 12100.0, avg_retail_price_rub: 59.9 },
          { date: '2026-04-05', volume_liters: 12450.0, avg_retail_price_rub: 60.1 },
        ]),
      );
    }

    if (method === 'GET' && path === '/api/v1/analytics/sales') {
      return json(
        envelope({
          product_code: 'AI_95',
          granularity: 'day',
          series: [
            { period_start: '2026-04-01', volume_liters: 12200.0, avg_retail_price_rub: 59.8 },
            { period_start: '2026-04-02', volume_liters: 12320.0, avg_retail_price_rub: 60.0 },
          ],
          seasonality: {
            by_weekday: [{ weekday: 'Mon', avg_volume_liters: 12000.0 }],
            by_month: [{ month: 4, avg_volume_liters: 12300.0 }],
          },
          comparisons: { mom_pct: 2.3, yoy_pct: null },
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/analytics/margin') {
      return json(
        envelope({
          product_code: 'AI_95',
          granularity: 'day',
          series: [
            {
              period_start: '2026-04-01',
              avg_purchase_price_rub: 55.0,
              avg_retail_price_rub: 59.8,
              gross_margin_rub: 46800.0,
              gross_margin_rub_per_liter: 4.8,
              gross_margin_pct: 8.0,
              purchase_data_missing: false,
            },
          ],
          threshold_rub_per_liter: 3.0,
          below_threshold_days: 0,
          low_margin_days: [],
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/analytics/anomalies') {
      return json(envelope([]));
    }

    if (method === 'GET' && path === '/api/v1/forecasts/latest') {
      if (!state.forecastRan) {
        return json(envelope(null, { empty_state: 'Нет данных' }));
      }
      return json(
        envelope({
          product_code: 'AI_95',
          horizon_days: 7,
          model_type: 'catboost',
          model_status: 'active',
          scenario_name: 'base',
          scenario_params: null,
          forecast_points: [
            { target_date: '2026-04-07', y_hat: 12450.0, y_lo: 11900.0, y_hi: 12980.0 },
          ],
          drivers: ['Лаг 7 дней задаёт базовый тренд'],
        }),
      );
    }

    if (method === 'POST' && path === '/api/v1/forecasts/run') {
      state.forecastRan = true;
      return json(
        envelope({
          product_code: 'AI_95',
          horizon_days: 7,
          model_type: 'catboost',
          model_status: 'active',
          scenario_name: 'base',
          scenario_params: null,
          forecast_points: [
            { target_date: '2026-04-07', y_hat: 12450.0, y_lo: 11900.0, y_hi: 12980.0 },
          ],
          drivers: ['Лаг 7 дней задаёт базовый тренд'],
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/backtests/latest') {
      return json(
        envelope({
          product_code: 'AI_95',
          horizon_days: 7,
          model_type: 'catboost',
          window_type: 'rolling',
          metrics: { mae: 412.0, rmse: 553.0, smape: 4.8 },
          comparison: {
            seasonal_naive: { mae: 520.0, rmse: 690.0, smape: 5.9 },
            catboost: { mae: 412.0, rmse: 553.0, smape: 4.8 },
          },
          trained_at: '2026-04-06T10:00:00+00:00',
          model_version: '20260406100000',
        }),
      );
    }

    return json(
      {
        data: null,
        error: { code: 'http_error', message: `Unhandled mock for ${method} ${path}` },
        meta: { request_id: 'e2e-request-id' },
      },
      404,
    );
  });

  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@fuelsight.local');
  await page.getByLabel('Пароль').fill('admin12345');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole('heading', { name: 'KPI Dashboard' })).toBeVisible();

  await page.getByRole('button', { name: 'Импорт', exact: true }).click();
  await expect(page).toHaveURL(/\/import$/);
  await expect(page.getByRole('heading', { name: 'Импорт данных' })).toBeVisible();

  await page.getByRole('tab', { name: 'Исторические данные' }).click();
  await page.getByRole('button', { name: 'Сгенерировать' }).click();
  await expect(page.getByText(/Генерация запущена/)).toBeVisible();

  await page.getByRole('button', { name: 'KPI', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.getByRole('button', { name: 'Продажи', exact: true }).click();
  await expect(page).toHaveURL(/\/analytics\/sales$/);
  await expect(page.getByRole('heading', { name: 'Аналитика продаж' })).toBeVisible();

  await page.getByRole('button', { name: 'Маржа', exact: true }).click();
  await expect(page).toHaveURL(/\/analytics\/margin$/);
  await expect(page.getByRole('heading', { name: 'Закупки и маржа' })).toBeVisible();

  await page.getByRole('button', { name: 'Прогноз', exact: true }).click();
  await expect(page).toHaveURL(/\/forecast$/);
  await page.getByRole('button', { name: 'Запустить прогноз' }).click();
  await expect(page.getByText('Таблица прогноза')).toBeVisible();
});

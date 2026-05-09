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

test('analyst-first flow: login -> dashboard -> sales -> margin -> forecast -> news', async ({ page }) => {
  const state = {
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
          access_token: 'e2e-analyst-token',
          token_type: 'bearer',
          expires_in: 1800,
          user: {
            id: '5e78cd7f-0493-47e2-b8f5-4e84142f0f62',
            email: 'analyst@fuelsight.local',
            role: 'analyst',
            display_name: 'FuelSight Analyst',
            preferred_landing_route: '/dashboard',
          },
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/auth/me') {
      return json(
        envelope({
          id: '5e78cd7f-0493-47e2-b8f5-4e84142f0f62',
          email: 'analyst@fuelsight.local',
          role: 'analyst',
          display_name: 'FuelSight Analyst',
          preferred_landing_route: '/dashboard',
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/health') {
      return json(
        envelope({
          ok: true,
          app_env: 'local',
          version: '0.2.0',
          enable_llm: false,
          timestamp: '2026-04-08T09:00:00+00:00',
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/kpi/summary') {
      return json(
        envelope(
          {
            sales_volume_liters: 152340.0,
            revenue_rub: 8876500.45,
            gross_margin_rub: 925340.11,
            gross_margin_pct: 10.43,
            low_margin_days: 3,
            anomaly_count: 2,
          },
          {
            data_freshness: 'fresh',
            margin_coverage_days: 28,
            margin_missing_days: 2,
            business_summary: {
              title: 'Итог за период',
              summary: 'Продажи стабильны, маржа контролируемая.',
              bullets: ['Риск по марже локализован'],
            },
          },
        ),
      );
    }

    if (method === 'GET' && path === '/api/v1/kpi/alerts') {
      return json(envelope([]));
    }

    if (method === 'GET' && path === '/api/v1/kpi/snapshot') {
      return json(
        envelope(
          [
            { date: '2026-04-06', volume_liters: 12400.0, avg_retail_price_rub: 59.9 },
            { date: '2026-04-07', volume_liters: 12620.0, avg_retail_price_rub: 60.1 },
          ],
          {
            business_summary: {
              title: 'Срез спроса',
              summary: 'Спрос умеренно растет.',
              bullets: [],
            },
            chart_annotations: [{ id: 'snap-peak', date: '2026-04-07', label: 'Пик спроса' }],
            reference_overlays: [
              {
                code: 'usd_rub',
                label: 'USD/RUB',
                provider_mode: 'cached',
                points: [
                  { date: '2026-04-06', value: 89.7 },
                  { date: '2026-04-07', value: 90.1 },
                ],
              },
            ],
            provider_mode: 'cached',
            external_indicators_mode: 'cached',
            data_freshness: 'fresh',
          },
        ),
      );
    }

    if (method === 'GET' && path === '/api/v1/analytics/sales') {
      return json(
        envelope(
          {
            product_code: 'AI_95',
            granularity: 'day',
            series: [
              { period_start: '2026-04-06', volume_liters: 12400.0, avg_retail_price_rub: 59.9 },
              { period_start: '2026-04-07', volume_liters: 12620.0, avg_retail_price_rub: 60.1 },
            ],
            seasonality: {
              by_weekday: [{ weekday: 'Mon', avg_volume_liters: 12100.0 }],
              by_month: [{ month: 4, avg_volume_liters: 12500.0 }],
            },
            comparisons: { mom_pct: 2.1, yoy_pct: null },
          },
          {
            business_summary: {
              title: 'Краткое объяснение динамики',
              summary: 'Спрос растет.',
              bullets: ['YoY: — (недостаточно истории)'],
            },
            chart_annotations: [{ id: 'sales-a1', date: '2026-04-07', label: 'Аномалия спроса' }],
            reference_overlays: [
              {
                code: 'crude_brent_usd',
                label: 'Brent, $/баррель',
                provider_mode: 'cached',
                points: [
                  { date: '2026-04-06', value: 83.2 },
                  { date: '2026-04-07', value: 83.5 },
                ],
              },
            ],
            data_mode: 'cached',
            provider_mode: 'cached',
            external_indicators_mode: 'cached',
            data_freshness: 'fresh',
          },
        ),
      );
    }

    if (method === 'GET' && path === '/api/v1/analytics/margin') {
      return json(
        envelope(
          {
            product_code: 'AI_95',
            granularity: 'day',
            series: [
              {
                period_start: '2026-04-06',
                avg_purchase_price_rub: 55.1,
                avg_retail_price_rub: 60.0,
                gross_margin_rub: 47200.0,
                gross_margin_rub_per_liter: 4.9,
                gross_margin_pct: 8.2,
                purchase_data_missing: false,
              },
            ],
            threshold_rub_per_liter: 3.0,
            below_threshold_days: 0,
            low_margin_days: [],
          },
          {
            business_summary: {
              title: 'Маржинальный риск',
              summary: 'Риск контролируемый.',
              bullets: [],
            },
            chart_annotations: [],
            reference_overlays: [],
            threshold_info: 'Порог 3.0 руб/л; дней ниже порога: 0; дней с неполным покрытием закупки: 0.',
            supporting_refs: [],
            provider_mode: null,
            data_freshness: 'fresh',
          },
        ),
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
            { target_date: '2026-04-10', y_hat: 12500.0, y_lo: 12020.0, y_hi: 13030.0 },
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
            { target_date: '2026-04-10', y_hat: 12500.0, y_lo: 12020.0, y_hi: 13030.0 },
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

    if (method === 'GET' && path === '/api/v1/news/digests/latest') {
      return json(
        envelope({
          digest_date: '2026-04-08',
          period_type: 'daily',
          summary_text: 'Рынок стабилен, существенных шоков не зафиксировано.',
          bullet_points: ['Спрос остается в сезонном диапазоне'],
          source_ids: ['news-1'],
          llm_mode: 'off',
          provider_mode: 'cached',
          news_freshness: 'warning',
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/news/search') {
      return json(
        envelope([
          {
            id: 'news-1',
            published_at: '2026-04-08T07:00:00+00:00',
            topic: 'oil_market',
            title: 'Стабилизация оптовых цен на топливо',
            source_name: 'Energy Daily',
            source_url: 'https://example.org/news-1',
            summary: 'Оптовые цены стабилизировались в пределах сезонного коридора.',
            relevance_score: 0.76,
            provider_mode: 'cached',
            confidence: 0.8,
          },
        ]),
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
  await expect(page.getByLabel('Email')).toHaveValue('analyst@fuelsight.local');
  await expect(page.getByLabel('Пароль')).toHaveValue('analyst12345');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole('heading', { name: 'KPI за период' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Импорт', exact: true })).toHaveCount(0);

  await page.getByRole('button', { name: 'Продажи', exact: true }).click();
  await expect(page).toHaveURL(/\/analytics\/sales$/);

  await page.getByRole('button', { name: 'Маржа', exact: true }).click();
  await expect(page).toHaveURL(/\/analytics\/margin$/);

  await page.getByRole('button', { name: 'Прогноз', exact: true }).click();
  await expect(page).toHaveURL(/\/forecast$/);
  await page.getByRole('button', { name: 'Запустить прогноз' }).click();
  await expect(page.getByText('Таблица прогноза')).toBeVisible();

  await page.getByRole('button', { name: 'Сводка', exact: true }).click();
  await expect(page).toHaveURL(/\/news$/);
  await expect(page.getByRole('heading', { name: 'Сводка и чат' })).toBeVisible();
});

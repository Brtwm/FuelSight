import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
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
    meta: { request_id: 'e2e-mobile-request-id', ...meta },
  };
}

test.describe('mobile smoke flow', () => {
  test('login -> dashboard -> forecast -> news with screenshots', async ({ page }, testInfo) => {
    const screenshotDir = join(process.cwd(), 'output', 'playwright');
    mkdirSync(screenshotDir, { recursive: true });

    let forecastRan = false;

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
            meta: { request_id: 'e2e-mobile-request-id' },
          },
          401,
        );
      }

      if (method === 'POST' && path === '/api/v1/auth/login') {
        return json(
          envelope({
            access_token: 'e2e-mobile-analyst-token',
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
              reference_overlays: [],
              provider_mode: 'cached',
              external_indicators_mode: 'cached',
              data_freshness: 'fresh',
            },
          ),
        );
      }

      if (method === 'GET' && path === '/api/v1/forecasts/latest') {
        if (!forecastRan) {
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
            model_freshness: 'fresh',
            retrain_status: 'ok',
            provider_mode: 'cached',
            forecast_points: [
              { target_date: '2026-04-10', y_hat: 12500.0, y_lo: 12020.0, y_hi: 13030.0 },
            ],
            drivers: ['Лаг 7 дней задаёт базовый тренд'],
          }),
        );
      }

      if (method === 'POST' && path === '/api/v1/forecasts/run') {
        forecastRan = true;
        return json(
          envelope({
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            model_status: 'active',
            scenario_name: 'base',
            scenario_params: null,
            model_freshness: 'fresh',
            retrain_status: 'ok',
            provider_mode: 'cached',
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
              ref_id: 'gdelt_2026_03_24_01',
              published_at: '2026-04-08T07:00:00+00:00',
              topic: 'oil_market',
              title: 'Стабилизация оптовых цен на топливо',
              source_name: 'Energy Daily',
              url: 'https://example.org/news-1',
              summary: 'Оптовые цены стабилизировались в пределах сезонного коридора.',
              relevance_score: 0.76,
              provider_mode: 'cached',
              confidence: 0.8,
              topic_tags: ['market'],
            },
          ]),
        );
      }

      if (method === 'POST' && path === '/api/v1/chat/sessions') {
        return json(envelope({ id: 'session-1', title: 'mobile smoke', created_at: '2026-04-08T10:00:00+00:00' }));
      }

      if (method === 'GET' && path === '/api/v1/chat/sessions/session-1/messages') {
        return json(envelope([]));
      }

      if (method === 'POST' && path === '/api/v1/chat/sessions/session-1/messages') {
        return json(
          envelope({
            id: 'message-1',
            sender_type: 'assistant',
            message_text: 'Ответ с источниками',
            citations: [{ type: 'news', ref_id: 'gdelt_2026_03_24_01', title: 'Логистика' }],
            created_at: '2026-04-08T10:02:00+00:00',
          }),
        );
      }

      return json(
        {
          data: null,
          error: { code: 'http_error', message: `Unhandled mock for ${method} ${path}` },
          meta: { request_id: 'e2e-mobile-request-id' },
        },
        404,
      );
    });

    await page.goto('/login');
    await expect(page.getByLabel('Email')).toHaveValue('analyst@fuelsight.local');
    await page.screenshot({
      path: join(screenshotDir, `${testInfo.project.name}-mobile-login.png`),
      fullPage: true,
    });

    await page.getByRole('button', { name: 'Войти' }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole('heading', { name: 'Аналитический обзор' })).toBeVisible();
    await page.screenshot({
      path: join(screenshotDir, `${testInfo.project.name}-mobile-dashboard.png`),
      fullPage: true,
    });

    await page.getByRole('main').getByRole('button', { name: 'Прогноз спроса', exact: true }).click();
    await expect(page).toHaveURL(/\/forecast$/);
    await page.getByRole('button', { name: 'Запустить прогноз' }).click();
    await expect(page.getByText(/Прогноз по дням|Таблица прогноза/)).toBeVisible();
    await page.screenshot({
      path: join(screenshotDir, `${testInfo.project.name}-mobile-forecast.png`),
      fullPage: true,
    });

    await page.getByRole('button', { name: 'Новости и RAG-чат', exact: true }).click();
    await expect(page).toHaveURL(/\/news$/);
    await expect(page.getByRole('heading', { name: 'Сводка и чат' })).toBeVisible();
    await page.screenshot({
      path: join(screenshotDir, `${testInfo.project.name}-mobile-news.png`),
      fullPage: true,
    });
  });
});

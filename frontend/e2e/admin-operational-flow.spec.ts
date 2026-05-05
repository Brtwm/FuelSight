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

test('admin operational flow: login -> import -> initial-history refresh -> diagnostics', async ({ page }) => {
  const state = {
    historyUpdated: false,
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
          access_token: 'e2e-admin-token',
          token_type: 'bearer',
          expires_in: 1800,
          user: {
            id: '844c5c42-f932-45eb-aa0d-99c8607348f9',
            email: 'admin@fuelsight.local',
            role: 'admin',
            display_name: 'FuelSight Admin',
            preferred_landing_route: '/dashboard',
          },
        }),
      );
    }

    if (method === 'GET' && path === '/api/v1/auth/me') {
      return json(
        envelope({
          id: '844c5c42-f932-45eb-aa0d-99c8607348f9',
          email: 'admin@fuelsight.local',
          role: 'admin',
          display_name: 'FuelSight Admin',
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
          null,
          {
            empty_state: 'Нет данных',
            data_freshness: 'degraded',
            business_summary: {
              title: 'Нет фактических данных',
              summary: 'Требуется обновление начальной истории.',
              bullets: [],
            },
            margin_coverage_days: 0,
            margin_missing_days: 30,
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
          [],
          {
            business_summary: {
              title: 'Срез спроса недоступен',
              summary: 'Нет точек продаж.',
              bullets: [],
            },
            chart_annotations: [],
            reference_overlays: [],
            supporting_refs: [],
            data_freshness: 'degraded',
          },
        ),
      );
    }

    if (method === 'POST' && path === '/api/v1/import/generate-demo') {
      state.historyUpdated = true;
      return json(
        envelope(
          {
            job_id: '63d4060b-d4eb-4899-a773-5a164d096f5d',
            entity_type: 'historical_data',
            status: 'queued',
            display_label: 'initial_history',
            provenance_mode: 'manual_snapshot',
            quality_status: null,
          },
          { queued: true },
        ),
        202,
      );
    }

    if (method === 'GET' && path === '/api/v1/import/jobs') {
      return json(
        envelope(
          state.historyUpdated
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
                  started_at: '2026-04-08T09:00:00+00:00',
                  finished_at: '2026-04-08T09:00:03+00:00',
                  display_label: 'initial_history',
                  provenance_mode: 'manual_snapshot',
                  quality_status: 'ok',
                },
              ]
            : [],
          { count: state.historyUpdated ? 1 : 0 },
        ),
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

  await page.getByRole('button', { name: 'Импорт', exact: true }).click();
  await expect(page).toHaveURL(/\/import$/);
  await expect(page.getByRole('heading', { name: 'Начальные данные и обновления' })).toBeVisible();

  await page.getByRole('tab', { name: 'Начальная история' }).click();
  await page.getByRole('button', { name: 'Обновить историю' }).click();
  await expect(page.getByText(/Обновление начальной истории запущено/)).toBeVisible();

  await page.getByRole('button', { name: 'Диагностика' }).click();
  await expect(page.getByText('Диагностика качества и источников')).toBeVisible();
  await expect(page.getByText('provenance_mode: manual_snapshot')).toBeVisible();
  await expect(page.getByText('quality_status: ok')).toBeVisible();
});

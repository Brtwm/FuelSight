/** @vitest-environment jsdom */

import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { DashboardPage } from './DashboardPage';
import { ApiHttpError } from '../lib/api/http';
import type { UserRole } from '../lib/api/auth.types';

const useQueryMock = vi.fn();
const { authState } = vi.hoisted(() => ({
  authState: { role: 'admin' },
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: (...args: unknown[]) => useQueryMock(...args),
  };
});

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    authFetch: vi.fn(),
    user: { role: authState.role },
  }),
}));

vi.mock('../features/kpi/components/KpiSummaryCards', () => ({
  KpiSummaryCards: () => <div>KPI_SUMMARY_CARDS</div>,
}));

vi.mock('../features/kpi/components/DemandSnapshotChart', () => ({
  DemandSnapshotChart: () => <div>DEMAND_SNAPSHOT_CHART</div>,
}));

vi.mock('../features/kpi/components/AlertFeed', () => ({
  AlertFeed: () => <div>ALERT_FEED</div>,
}));

vi.mock('../components/common', async () => {
  const actual = await vi.importActual<typeof import('../components/common')>('../components/common');
  return {
    ...actual,
    MetricCard: ({ label, value }: { label: string; value: string }) => (
      <div>
        <span>{label}</span>
        <span>{value}</span>
      </div>
    ),
  };
});

function queryState(overrides: Record<string, unknown> = {}) {
  return {
    isLoading: false,
    isError: false,
    data: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

function setupUseQueryStates(
  summaryState: Record<string, unknown>,
  alertsState: Record<string, unknown>,
  snapshotState: Record<string, unknown>,
  importJobsState: Record<string, unknown> = queryState(),
) {
  useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
    const queryKey = options?.queryKey ?? [];
    if (queryKey[0] === 'kpi' && queryKey[1] === 'summary') {
      return summaryState;
    }
    if (queryKey[0] === 'kpi' && queryKey[1] === 'alerts') {
      return alertsState;
    }
    if (queryKey[0] === 'kpi' && queryKey[1] === 'snapshot') {
      return snapshotState;
    }
    if (queryKey[0] === 'import' && queryKey[1] === 'jobs') {
      return importJobsState;
    }
    return queryState();
  });
}

describe('DashboardPage states', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    authState.role = 'admin' satisfies UserRole;
  });

  it('renders loading state', () => {
    setupUseQueryStates(queryState({ isLoading: true }), queryState(), queryState());

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'KPI Dashboard' })).toBeTruthy();
  });

  it('renders error state', () => {
    setupUseQueryStates(queryState({ isError: true }), queryState(), queryState());

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Не удалось загрузить KPI и алерты. Проверьте сервер приложения и попробуйте снова.')).toBeTruthy();
  });

  it('renders role access message for 403 errors', () => {
    setupUseQueryStates(
      queryState({
        isError: true,
        error: new ApiHttpError({ status: 403, message: 'Forbidden' }),
      }),
      queryState(),
      queryState(),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('У вашей роли нет доступа к этому разделу')).toBeTruthy();
  });

  it('renders empty state and navigates to /import via CTA', async () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: null,
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: null, mode: null, data_mode: null },
              state: { status: 'empty', reason: 'Нет данных' },
            },
          },
        },
      }),
      queryState({ data: [] }),
      queryState({
        data: {
          data: [],
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: null, mode: null, data_mode: null },
              state: { status: 'empty', reason: 'Нет данных' },
            },
          },
        },
      }),
    );

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/import" element={<div>IMPORT_PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText('Чтобы увидеть KPI и динамику, загрузите продажи/закупки или выполните обновление начальной истории.'),
    ).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: 'Перейти к импорту' }));
    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });

  it('renders ready state', () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            sales_volume_liters: 152340,
            revenue_rub: 8876500.45,
            gross_margin_rub: 925340.11,
            gross_margin_pct: 10.43,
            low_margin_days: 3,
            anomaly_count: 2,
          },
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: 'fresh', mode: 'cached', data_mode: 'cached' },
              state: { status: 'ready', reason: null },
            },
          },
        },
      }),
      queryState({ data: [] }),
      queryState({
        data: {
          data: [],
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: 'fresh', mode: 'cached', data_mode: 'cached' },
              state: { status: 'ready', reason: null },
            },
          },
        },
      }),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('KPI_SUMMARY_CARDS')).toBeTruthy();
    expect(screen.getByText('DEMAND_SNAPSHOT_CHART')).toBeTruthy();
    expect(screen.getByText('ALERT_FEED')).toBeTruthy();
  });

  it('renders accounting financial overview and purchase import error control', () => {
    authState.role = 'accounting' satisfies UserRole;
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            sales_volume_liters: 152340,
            revenue_rub: 8876500,
            gross_margin_rub: 925300,
            gross_margin_pct: 10.43,
            low_margin_days: 3,
            anomaly_count: 2,
          },
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: 'fresh', mode: 'cached', data_mode: 'cached' },
              state: { status: 'ready', reason: null },
            },
          },
        },
      }),
      queryState({
        data: [
          {
            type: 'low_margin',
            severity: 'high',
            date: '2026-04-01',
            product_code: 'AI_95',
            message: 'Маржа ниже порога',
            metric: 'margin',
            actual_value: 2.1,
            expected_range: [3, 5],
            target_path: '/analytics/margin',
          },
        ],
      }),
      queryState({
        data: {
          data: [],
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: 'fresh', mode: 'cached', data_mode: 'cached' },
              state: { status: 'ready', reason: null },
            },
          },
        },
      }),
      queryState({
        data: [
          {
            id: 'job-1',
            entity_type: 'purchases',
            source_type: 'csv',
            file_name: 'purchases.csv',
            status: 'completed_with_errors',
            rows_total: 100,
            rows_success: 97,
            rows_failed: 3,
            error_report_path: 'errors/purchases.csv',
            started_at: '2026-04-01T08:00:00Z',
            finished_at: '2026-04-01T08:05:00Z',
            display_label: 'purchases',
            provenance_mode: 'manual_snapshot',
            quality_status: 'warning',
          },
        ],
      }),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Финансовый обзор' })).toBeTruthy();
    expect(screen.getByText('Бухгалтерия контролирует закупочные данные, себестоимость, валовую маржу и ошибки импорта закупок')).toBeTruthy();
    expect(screen.getByText('Расчетная себестоимость')).toBeTruthy();
    expect(screen.getByText('Низкомаржинальные позиции')).toBeTruthy();
    expect(screen.getByText('Контроль ошибок импорта закупок')).toBeTruthy();
    expect(screen.getByText('purchases.csv')).toBeTruthy();
    expect(screen.getByText('3 строк с ошибкой')).toBeTruthy();
    expect(screen.queryByText('DEMAND_SNAPSHOT_CHART')).toBeNull();
    expect(screen.queryByText('Контекст внешних сигналов')).toBeNull();
  });

  it('renders sales-oriented dashboard without full margin details', () => {
    authState.role = 'sales' satisfies UserRole;
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            sales_volume_liters: 152340,
            revenue_rub: 8876500,
            gross_margin_rub: 925300,
            gross_margin_pct: 10.43,
            low_margin_days: 3,
            anomaly_count: 2,
          },
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: 'fresh', mode: 'cached', data_mode: 'cached' },
              state: { status: 'ready', reason: null },
            },
          },
        },
      }),
      queryState({
        data: [
          {
            type: 'low_margin',
            severity: 'high',
            date: '2026-04-01',
            product_code: 'AI_95',
            message: 'Маржа ниже порога',
            metric: 'margin',
            actual_value: 2.1,
            expected_range: [3, 5],
            target_path: '/analytics/margin',
          },
          {
            type: 'demand_anomaly',
            severity: 'medium',
            date: '2026-04-02',
            product_code: 'AI_95',
            message: 'Спрос вырос выше обычного уровня',
            metric: 'sales',
            actual_value: 15000,
            expected_range: [9000, 12000],
            target_path: '/analytics/sales',
          },
        ],
      }),
      queryState({
        data: {
          data: [],
          meta: {
            explainability: {
              summary: null,
              chart: { annotations: [], overlays: [], thresholds: [], supporting_refs: [] },
              trust: { data_freshness: 'fresh', mode: 'cached', data_mode: 'cached' },
              state: { status: 'ready', reason: null },
            },
          },
        },
      }),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Продажи' })).toBeTruthy();
    expect(screen.getByText('Раздел помогает отделу продаж отслеживать реализацию нефтепродуктов, видеть изменение спроса и быстро переходить к прогнозу.')).toBeTruthy();
    expect(screen.getByText('Объем продаж')).toBeTruthy();
    expect(screen.getByText('Выручка')).toBeTruthy();
    expect(screen.getByText('Прогноз спроса')).toBeTruthy();
    expect(screen.getByText('Аномалии продаж').parentElement?.textContent).toContain('1');
    expect(screen.getByText('Есть позиции с пониженной маржинальностью, требуется согласование цены/объема с финансовым контуром.')).toBeTruthy();
    expect(screen.getByText('ALERT_FEED')).toBeTruthy();
    expect(screen.queryByText(/Маржа ниже порога/)).toBeNull();
    expect(screen.queryByText('Бизнес-резюме')).toBeNull();
    expect(screen.queryByText('Маржа')).toBeNull();
    expect(screen.queryByText('Валовая маржа')).toBeNull();
    expect(screen.queryByText('KPI_SUMMARY_CARDS')).toBeNull();
  });
});

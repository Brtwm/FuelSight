/** @vitest-environment jsdom */

import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { DashboardPage } from './DashboardPage';

const useQueryMock = vi.fn();

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
    user: { role: 'admin' },
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
    return queryState();
  });
}

describe('DashboardPage states', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
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
});

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

function setupUseQuerySequence(sequence: Array<Record<string, unknown>>) {
  let index = 0;
  useQueryMock.mockImplementation(() => {
    const fallback = sequence[sequence.length - 1];
    const current = sequence[index] ?? fallback;
    index += 1;
    return current;
  });
}

describe('DashboardPage states', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
  });

  it('renders loading state', () => {
    setupUseQuerySequence([queryState({ isLoading: true }), queryState(), queryState()]);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'KPI Dashboard' })).toBeTruthy();
  });

  it('renders error state', () => {
    setupUseQuerySequence([queryState({ isError: true }), queryState(), queryState()]);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Не удалось загрузить KPI и алерты. Проверьте backend и попробуйте снова.')).toBeTruthy();
  });

  it('renders empty state and navigates to /import via CTA', async () => {
    setupUseQuerySequence([
      queryState({
        data: {
          data: null,
          meta: {},
        },
      }),
      queryState({ data: [] }),
      queryState({
        data: {
          data: [],
          meta: {},
        },
      }),
    ]);

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
    setupUseQuerySequence([
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
          meta: {},
        },
      }),
      queryState({ data: [] }),
      queryState({
        data: {
          data: [],
          meta: {},
        },
      }),
    ]);

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

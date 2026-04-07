/** @vitest-environment jsdom */

import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { SalesAnalyticsPage } from './SalesAnalyticsPage';

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

vi.mock('../features/sales/components/SalesFilterBar', () => ({
  SalesFilterBar: () => <div>SALES_FILTER_BAR</div>,
}));
vi.mock('../features/sales/components/SalesTrendChart', () => ({
  SalesTrendChart: () => <div>SALES_TREND_CHART</div>,
}));
vi.mock('../features/sales/components/SeasonalityPanel', () => ({
  SeasonalityPanel: () => <div>SEASONALITY_PANEL</div>,
}));
vi.mock('../features/sales/components/ComparisonsPanel', () => ({
  ComparisonsPanel: () => <div>COMPARISONS_PANEL</div>,
}));
vi.mock('../features/sales/components/SalesAnomalyTable', () => ({
  SalesAnomalyTable: () => <div>SALES_ANOMALY_TABLE</div>,
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
  salesState: Record<string, unknown>,
  anomaliesState: Record<string, unknown>,
) {
  useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
    const queryKey = options?.queryKey ?? [];
    if (queryKey[0] === 'analytics' && queryKey[1] === 'sales') {
      return salesState;
    }
    if (queryKey[0] === 'analytics' && queryKey[1] === 'anomalies') {
      return anomaliesState;
    }
    return queryState();
  });
}

describe('SalesAnalyticsPage states', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
  });

  it('renders loading state', () => {
    setupUseQueryStates(queryState({ isLoading: true }), queryState());

    render(
      <MemoryRouter>
        <SalesAnalyticsPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Аналитика продаж' })).toBeTruthy();
  });

  it('renders error state', () => {
    setupUseQueryStates(queryState({ isError: true }), queryState());

    render(
      <MemoryRouter>
        <SalesAnalyticsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Не удалось загрузить аналитику продаж. Проверьте backend и повторите запрос.')).toBeTruthy();
  });

  it('renders empty state and navigates to /import via CTA', async () => {
    setupUseQueryStates(
      queryState({
        data: {
          product_code: 'AI_95',
          granularity: 'day',
          series: [],
          seasonality: { by_weekday: [], by_month: [] },
          comparisons: { mom_pct: null, yoy_pct: null },
        },
      }),
      queryState({ data: [] }),
    );

    render(
      <MemoryRouter initialEntries={['/analytics/sales']}>
        <Routes>
          <Route path="/analytics/sales" element={<SalesAnalyticsPage />} />
          <Route path="/import" element={<div>IMPORT_PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Перейти к импорту' }));
    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });

  it('renders ready state', () => {
    setupUseQueryStates(
      queryState({
        data: {
          product_code: 'AI_95',
          granularity: 'day',
          series: [{ period_start: '2026-04-01', volume_liters: 12000, avg_retail_price_rub: 59.8 }],
          seasonality: { by_weekday: [], by_month: [] },
          comparisons: { mom_pct: 2.4, yoy_pct: null },
        },
      }),
      queryState({ data: [] }),
    );

    render(
      <MemoryRouter>
        <SalesAnalyticsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('SALES_FILTER_BAR')).toBeTruthy();
    expect(screen.getByText('SALES_TREND_CHART')).toBeTruthy();
    expect(screen.getByText('SEASONALITY_PANEL')).toBeTruthy();
    expect(screen.getByText('COMPARISONS_PANEL')).toBeTruthy();
    expect(screen.getByText('SALES_ANOMALY_TABLE')).toBeTruthy();
  });
});

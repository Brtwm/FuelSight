/** @vitest-environment jsdom */

import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { MarginAnalyticsPage } from './MarginAnalyticsPage';

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

vi.mock('../features/margin/components/MarginFilterBar', () => ({
  MarginFilterBar: () => <div>MARGIN_FILTER_BAR</div>,
}));
vi.mock('../features/margin/components/PriceVsMarginChart', () => ({
  PriceVsMarginChart: () => <div>PRICE_VS_MARGIN_CHART</div>,
}));
vi.mock('../features/margin/components/LowMarginTable', () => ({
  LowMarginTable: () => <div>LOW_MARGIN_TABLE</div>,
}));
vi.mock('../features/margin/components/AnomalyJournal', () => ({
  AnomalyJournal: () => <div>ANOMALY_JOURNAL</div>,
}));
vi.mock('../features/margin/components/PossibleReasonsPanel', () => ({
  PossibleReasonsPanel: () => <div>POSSIBLE_REASONS_PANEL</div>,
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
  marginState: Record<string, unknown>,
  anomaliesState: Record<string, unknown>,
) {
  useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
    const queryKey = options?.queryKey ?? [];
    if (queryKey[0] === 'analytics' && queryKey[1] === 'margin') {
      return marginState;
    }
    if (queryKey[0] === 'analytics' && queryKey[1] === 'anomalies') {
      return anomaliesState;
    }
    return queryState();
  });
}

describe('MarginAnalyticsPage states', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
  });

  it('renders loading state', () => {
    setupUseQueryStates(queryState({ isLoading: true }), queryState());

    render(
      <MemoryRouter>
        <MarginAnalyticsPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Закупки и маржа' })).toBeTruthy();
  });

  it('renders error state', () => {
    setupUseQueryStates(queryState({ isError: true }), queryState());

    render(
      <MemoryRouter>
        <MarginAnalyticsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Не удалось загрузить аналитику маржи. Проверьте backend и повторите запрос.')).toBeTruthy();
  });

  it('renders empty state and navigates to /import via CTA', async () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            granularity: 'day',
            series: [],
            threshold_rub_per_liter: 3,
            below_threshold_days: 0,
            low_margin_days: [],
          },
          meta: {},
        },
      }),
      queryState({ data: [] }),
    );

    render(
      <MemoryRouter initialEntries={['/analytics/margin']}>
        <Routes>
          <Route path="/analytics/margin" element={<MarginAnalyticsPage />} />
          <Route path="/import" element={<div>IMPORT_PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText('Добавьте данные закупок и продаж или обновите начальную историю на странице импорта.'),
    ).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: 'Перейти к импорту' }));
    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });

  it('renders ready state', () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            granularity: 'day',
            series: [
              {
                period_start: '2026-04-01',
                avg_purchase_price_rub: 55.0,
                avg_retail_price_rub: 59.8,
                gross_margin_rub: 45600,
                gross_margin_rub_per_liter: 4.8,
                gross_margin_pct: 8.0,
                purchase_data_missing: false,
              },
            ],
            threshold_rub_per_liter: 3,
            below_threshold_days: 0,
            low_margin_days: [],
          },
          meta: {},
        },
      }),
      queryState({ data: [] }),
    );

    render(
      <MemoryRouter>
        <MarginAnalyticsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('MARGIN_FILTER_BAR')).toBeTruthy();
    expect(screen.getByText('PRICE_VS_MARGIN_CHART')).toBeTruthy();
    expect(screen.getByText('LOW_MARGIN_TABLE')).toBeTruthy();
    expect(screen.getByText('ANOMALY_JOURNAL')).toBeTruthy();
    expect(screen.getByText('POSSIBLE_REASONS_PANEL')).toBeTruthy();
  });
});

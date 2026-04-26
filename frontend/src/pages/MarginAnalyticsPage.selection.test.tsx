/** @vitest-environment jsdom */

import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
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
  MarginFilterBar: ({ onDateFromChange }: { onDateFromChange: (value: string) => void }) => (
    <button type="button" onClick={() => onDateFromChange('2026-04-01')}>
      CHANGE_DATE_FROM
    </button>
  ),
}));

vi.mock('../features/margin/components/PriceVsMarginChart', () => ({
  PriceVsMarginChart: ({ highlightDate }: { highlightDate?: string | null }) => (
    <div>PRICE_CHART_HIGHLIGHT:{highlightDate ?? 'none'}</div>
  ),
}));

vi.mock('../features/margin/components/LowMarginTable', () => ({
  LowMarginTable: ({ onSelectDay }: { onSelectDay: (date: string) => void }) => (
    <button type="button" onClick={() => onSelectDay('2026-04-06')}>
      SELECT_LOW_MARGIN_DAY
    </button>
  ),
}));

vi.mock('../features/margin/components/AnomalyJournal', () => ({
  AnomalyJournal: ({
    onSelectAnomaly,
  }: {
    onSelectAnomaly: (item: {
      date: string;
      metric: string;
      severity: string;
      actual_value: number;
      expected_range: number[];
      possible_reasons: string[];
      product_code: string;
      target_path: string;
    }) => void;
  }) => (
    <button type="button" onClick={() => onSelectAnomaly({
      date: '2026-04-07',
      metric: 'margin',
      severity: 'high',
      actual_value: 2.1,
      expected_range: [3.0, 4.5],
      possible_reasons: ['Рост закупки'],
      product_code: 'AI_95',
      target_path: '/analytics/margin',
    })}>
      SELECT_ANOMALY_DAY
    </button>
  ),
}));

vi.mock('../features/margin/components/PossibleReasonsPanel', () => ({
  PossibleReasonsPanel: () => <div>REASONS_PANEL</div>,
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

describe('MarginAnalyticsPage selection sync', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
      const queryKey = options?.queryKey ?? [];
      if (queryKey[0] === 'analytics' && queryKey[1] === 'margin') {
        const filters = (queryKey[2] ?? {}) as { date_from?: string };
        const lowMarginDate = filters.date_from === '2026-04-01' ? '2026-04-10' : '2026-04-06';
        return queryState({
          data: {
            data: {
              product_code: 'AI_95',
              granularity: 'day',
              series: [
                {
                  period_start: lowMarginDate,
                  avg_purchase_price_rub: 55.0,
                  avg_retail_price_rub: 60.0,
                  gross_margin_rub: 47000,
                  gross_margin_rub_per_liter: 4.9,
                  gross_margin_pct: 8.0,
                  purchase_data_missing: false,
                },
              ],
              threshold_rub_per_liter: 3,
              below_threshold_days: 1,
              low_margin_days: [{ date: lowMarginDate, gross_margin_rub_per_liter: 2.1, purchase_data_missing: false }],
            },
            meta: {
              business_summary: null,
              chart_annotations: [],
              reference_overlays: [],
              supporting_refs: [],
              threshold_info: 'Порог 3.0 руб/л',
            },
          },
        });
      }
      if (queryKey[0] === 'analytics' && queryKey[1] === 'anomalies') {
        return queryState({
          data: [
            {
              date: '2026-04-07',
              product_code: 'AI_95',
              metric: 'margin',
              severity: 'high',
              actual_value: 2.1,
              expected_range: [3.0, 4.5],
              possible_reasons: ['Рост закупки'],
              target_path: '/analytics/margin',
            },
          ],
        });
      }
      return queryState();
    });
  });

  it('keeps chart highlight synced with selected day from table/journal', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <MarginAnalyticsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText('PRICE_CHART_HIGHLIGHT:2026-04-06')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'SELECT_ANOMALY_DAY' }));
    expect(await screen.findByText('PRICE_CHART_HIGHLIGHT:2026-04-07')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'SELECT_LOW_MARGIN_DAY' }));
    expect(await screen.findByText('PRICE_CHART_HIGHLIGHT:2026-04-06')).toBeTruthy();
  });

  it('resets selected day when filters change and old date becomes stale', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <MarginAnalyticsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText('PRICE_CHART_HIGHLIGHT:2026-04-06')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'SELECT_ANOMALY_DAY' }));
    expect(await screen.findByText('PRICE_CHART_HIGHLIGHT:2026-04-07')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'CHANGE_DATE_FROM' }));
    expect(await screen.findByText('PRICE_CHART_HIGHLIGHT:2026-04-10')).toBeTruthy();
  });
});

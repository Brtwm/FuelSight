/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiHttpError } from '../lib/api/http';
import { ReportsPage } from './ReportsPage';

const authFetchMock = vi.fn();
const generateExecutiveReportMock = vi.fn();

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    authFetch: authFetchMock,
  }),
}));

vi.mock('../lib/api/reports', () => ({
  generateExecutiveReport: (...args: unknown[]) => generateExecutiveReportMock(...args),
}));

function reportPayload(overrides: Record<string, unknown> = {}) {
  return {
    report_id: 'test-report',
    generated_at: '2026-03-31T12:00:00+00:00',
    period: { date_from: '2026-03-01', date_to: '2026-03-31' },
    executive_summary: 'Маржа и спрос стабильны.',
    kpi: {
      revenue_rub: 60000,
      sales_volume_liters: 1000,
      gross_margin_rub: 5000,
      gross_margin_pct: 8.33,
    },
    problem_products: [],
    demand_forecast: [
      {
        product_code: 'AI_95',
        product_name: 'Бензин АИ-95',
        forecast_period: '7 дней',
        forecast_volume_liters: 7000,
        risk_level: 'low',
      },
    ],
    margin_risks: [],
    market_context: [{ title: 'Рынок топлива', summary: 'Новостной фон нейтральный.' }],
    recommendations: ['Продолжить мониторинг маржи.'],
    data_quality: {
      has_sales_data: true,
      has_purchase_data: true,
      has_forecast_data: true,
      has_news_data: true,
      warnings: [],
    },
    ...overrides,
  };
}

describe('ReportsPage states', () => {
  beforeEach(() => {
    authFetchMock.mockReset();
    generateExecutiveReportMock.mockReset();
  });

  it('renders initial state before report generation', () => {
    render(<ReportsPage />);

    expect(screen.getByRole('heading', { name: 'Управленческий отчет' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Сформировать управленческий отчет' })).toBeTruthy();
    expect(screen.getByText('Отчет пока не сформирован')).toBeTruthy();
  });

  it('renders report sections after successful generation', async () => {
    const user = userEvent.setup();
    generateExecutiveReportMock.mockResolvedValue(reportPayload());

    render(<ReportsPage />);

    await user.click(screen.getByRole('button', { name: 'Сформировать управленческий отчет' }));

    expect(await screen.findByText('Краткие выводы')).toBeTruthy();
    expect(screen.getByText('Сводка KPI')).toBeTruthy();
    expect(screen.getByText('Выручка')).toBeTruthy();
    expect(screen.getByText('Объем продаж')).toBeTruthy();
    expect(screen.getByText('Валовая маржа')).toBeTruthy();
    expect(screen.getByText('Проблемные продукты')).toBeTruthy();
    expect(screen.getByText('Прогноз спроса')).toBeTruthy();
    expect(screen.getAllByText('Риски по марже').length).toBeGreaterThan(0);
    expect(screen.getByText('Рыночные факторы')).toBeTruthy();
    expect(screen.getByText('Рекомендации')).toBeTruthy();

    const text = document.body.textContent ?? '';
    expect(text).not.toContain('Defense report');
    expect(text).not.toContain('defense');
  });

  it('renders data quality warnings for empty report data', async () => {
    const user = userEvent.setup();
    generateExecutiveReportMock.mockResolvedValue(
      reportPayload({
        executive_summary: 'Данных недостаточно для управленческих выводов.',
        data_quality: {
          has_sales_data: false,
          has_purchase_data: false,
          has_forecast_data: false,
          has_news_data: false,
          warnings: ['Нет данных продаж за выбранный период.'],
        },
      }),
    );

    render(<ReportsPage />);

    await user.click(screen.getByRole('button', { name: 'Сформировать управленческий отчет' }));

    expect(await screen.findByText('Ограничения данных')).toBeTruthy();
    expect(screen.getByText('Нет данных продаж за выбранный период.')).toBeTruthy();
  });

  it('renders API error state', async () => {
    const user = userEvent.setup();
    generateExecutiveReportMock.mockRejectedValue(
      new ApiHttpError({ status: 500, message: 'Internal server error' }),
    );

    render(<ReportsPage />);

    await user.click(screen.getByRole('button', { name: 'Сформировать управленческий отчет' }));

    expect(await screen.findByText('Internal server error')).toBeTruthy();
  });
});

/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ValidationEvidencePanel } from './ValidationEvidencePanel';
import type { BacktestData } from '../../../lib/api/forecast.types';

const mediaQueryMock = vi.fn();

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: { legend?: { data?: string[] } } }) => (
    <div data-testid="validation-chart">
      {(option.legend?.data ?? []).map((label) => (
        <span key={label}>{label}</span>
      ))}
    </div>
  ),
}));

function backtestWithValidation(
  validationSummary: NonNullable<BacktestData['validation_summary']>,
): BacktestData {
  return {
    product_code: 'AI_95',
    horizon_days: 7,
    model_type: 'catboost',
    window_type: 'rolling',
    metrics: { mae: 120.2, rmse: 150.3, smape: 4.4 },
    comparison: {
      catboost: { mae: 120.2, rmse: 150.3, smape: 4.4 },
      seasonal_naive: { mae: 170, rmse: 210, smape: 5.8 },
    },
    trained_at: '2026-04-04T20:00:00+00:00',
    model_version: '20260404200000',
    validation_summary: validationSummary,
  };
}

describe('ValidationEvidencePanel', () => {
  it('renders OK validation evidence with periods, chart, metrics, improvement and disclaimer', () => {
    mediaQueryMock.mockReturnValue(false);
    render(
      <ValidationEvidencePanel
        backtest={backtestWithValidation({
          status: 'OK',
          status_reason: 'CatBoost is evaluated on the test period and is not worse than Seasonal Naive by SMAPE.',
          train_period: { start: '2025-01-01', end: '2025-12-31' },
          test_period: { start: '2026-01-01', end: '2026-01-30' },
          observations: { total: 395, train: 365, test: 30 },
          metrics: {
            catboost: { mae: 120.2, rmse: 150.3, smape: 4.4 },
            seasonal_naive: { mae: 170, rmse: 210, smape: 5.8 },
            improvement: { mae_pct: 29.29, rmse_pct: 28.43, smape_pct: 24.14 },
          },
          series: [
            {
              date: '2026-01-01',
              actual: 100,
              catboost_prediction: 98,
              seasonal_naive_prediction: 95,
            },
          ],
        })}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Качество модели' })).toBeTruthy();
    expect(screen.getByText('OK')).toBeTruthy();
    expect(screen.getByText('Проверка на отложенном периоде и сравнение с простым сезонным ориентиром')).toBeTruthy();
    expect(screen.getByText(/CatBoost проверен на тестовом периоде/)).toBeTruthy();
    expect(screen.getByText(/Период обучения/)).toBeTruthy();
    expect(screen.getByText(/01\.01\.2025/)).toBeTruthy();
    expect(screen.getByText(/Тестовый период/)).toBeTruthy();
    expect(screen.getByText(/30\.01\.2026/)).toBeTruthy();
    expect(screen.getByText(/Наблюдения/)).toBeTruthy();
    expect(screen.getByText(/395 всего/)).toBeTruthy();
    expect(screen.getByText('Факт vs CatBoost vs простой сезонный ориентир')).toBeTruthy();
    expect(screen.getByText('Факт')).toBeTruthy();
    expect(screen.getAllByText('CatBoost').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Сезонный ориентир').length).toBeGreaterThan(0);
    expect(screen.getByText('Модель')).toBeTruthy();
    expect(screen.getByText('MAE')).toBeTruthy();
    expect(screen.getByText('RMSE')).toBeTruthy();
    expect(screen.getByText('SMAPE')).toBeTruthy();
    expect(screen.getByText('Улучшение')).toBeTruthy();
    expect(screen.getByText(/SMAPE: CatBoost лучше сезонного ориентира на 24,14%/)).toBeTruthy();
    expect(screen.getByText('Прогноз является аналитической оценкой и не гарантирует точное значение будущего спроса или цены.')).toBeTruthy();
  });

  it('renders LIMITED state with an empty-series fallback instead of a broken chart', () => {
    render(
      <ValidationEvidencePanel
        backtest={backtestWithValidation({
          status: 'LIMITED',
          status_reason: 'Backtest metrics are available, but dated test-period series is not persisted yet.',
          train_period: { start: '2025-01-01', end: '2025-12-31' },
          test_period: null,
          observations: { total: null, train: null, test: 40 },
          metrics: {
            catboost: { mae: 120.2, rmse: 150.3, smape: 4.4 },
            seasonal_naive: { mae: 170, rmse: 210, smape: 5.8 },
            improvement: { mae_pct: 29.29, rmse_pct: 28.43, smape_pct: 24.14 },
          },
          series: [],
        })}
      />,
    );

    expect(screen.getByText('LIMITED')).toBeTruthy();
    expect(screen.getByText(/Метрики backtest доступны, но датированный тестовый ряд пока не сохранён/)).toBeTruthy();
    expect(screen.getByText('Backtest найден, но тестовый ряд недоступен для визуального сравнения')).toBeTruthy();
    expect(screen.queryByTestId('validation-chart')).toBeNull();
  });

  it('renders UNKNOWN empty state when validation summary is absent or backtest is null', () => {
    const { rerender } = render(<ValidationEvidencePanel backtest={null} />);

    expect(screen.getByText('UNKNOWN')).toBeTruthy();
    expect(screen.getByText('Проверка качества пока недоступна')).toBeTruthy();
    expect(screen.getByText('Недостаточно данных для уверенного вывода')).toBeTruthy();
    expect(screen.queryByTestId('validation-chart')).toBeNull();
    expect(screen.queryByText('Модель')).toBeNull();

    rerender(
      <ValidationEvidencePanel
        backtest={{
          product_code: 'AI_95',
          horizon_days: 7,
          model_type: 'catboost',
          window_type: 'rolling',
          metrics: { mae: 1, rmse: 1, smape: 1 },
          comparison: {},
          trained_at: '2026-04-04T20:00:00+00:00',
          model_version: null,
          validation_summary: null,
        }}
      />,
    );

    expect(screen.getByText('UNKNOWN')).toBeTruthy();
    expect(screen.getByText('Проверка качества пока недоступна')).toBeTruthy();
  });

  it('renders partial data without leaking NaN, undefined or null', () => {
    const { container } = render(
      <ValidationEvidencePanel
        backtest={backtestWithValidation({
          status: 'LIMITED',
          status_reason: 'CatBoost metrics are incomplete.',
          train_period: { start: null, end: null },
          test_period: null,
          observations: { total: null, train: null, test: null },
          metrics: {
            catboost: { mae: null, rmse: 150.3, smape: null },
            seasonal_naive: null,
            improvement: { mae_pct: null, rmse_pct: null, smape_pct: -2.5 },
          },
          series: [
            {
              date: '2026-01-01',
              actual: null,
              catboost_prediction: 98,
              seasonal_naive_prediction: null,
            },
          ],
        })}
      />,
    );

    const text = container.textContent ?? '';
    expect(text).toContain('—');
    expect(text).toContain('Недоступно');
    expect(text).not.toContain('NaN');
    expect(text).not.toContain('undefined');
    expect(text).not.toContain('null');
  });
});

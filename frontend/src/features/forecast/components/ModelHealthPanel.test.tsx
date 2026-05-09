/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ModelHealthPanel } from './ModelHealthPanel';
import type { ForecastData } from '../../../lib/api/forecast.types';

const forecast: ForecastData = {
  product_code: 'AI_95',
  horizon_days: 7,
  model_type: 'catboost',
  model_status: 'active',
  scenario_name: 'base',
  scenario_params: null,
  forecast_points: [
    {
      target_date: '2026-04-07',
      y_hat: 12450,
      y_lo: 11900,
      y_hi: 12980,
    },
  ],
  drivers: ['Лаг 7 дней задаёт базовый тренд'],
  model_freshness: 'warning',
  retrain_status: 'degraded',
  provider_mode: 'manual_snapshot',
  training_window: { start_date: '2026-03-01', end_date: '2026-04-01' },
  baseline_comparison: {
    winner: { smape: 4.2 },
    seasonal_naive: { smape: 5.1 },
    delta_vs_baseline: { smape: -0.9 },
  },
  feature_sources: ['calendar', 'price', 'lag'],
};

describe('ModelHealthPanel', () => {
  it('maps technical model status values to readable Russian labels', () => {
    const { container } = render(<ModelHealthPanel forecast={forecast} backtest={null} />);

    expect(screen.getByText('Надёжность прогноза')).toBeTruthy();
    expect(screen.getByText('Свежесть модели: требует проверки')).toBeTruthy();
    expect(screen.getByText('Последнее обновление модели: нужно обновить')).toBeTruthy();
    expect(screen.getByText('Источник: Данные из локального проверенного источника')).toBeTruthy();
    expect(screen.getByText(/Период обучения:/)).toBeTruthy();
    expect(screen.getByText(/лучше простого ориентира/)).toBeTruthy();
    expect(screen.getByText('Группы факторов: календарь, цены, история спроса')).toBeTruthy();

    const text = container.textContent ?? '';
    expect(text).not.toContain('manual_snapshot');
    expect(text).not.toContain('model_freshness');
    expect(text).not.toContain('retrain');
    expect(text).not.toContain('n/a');
  });

  it('hides empty status rows instead of rendering placeholders', () => {
    const { container } = render(
      <ModelHealthPanel
        forecast={{
          ...forecast,
          model_freshness: null,
          retrain_status: null,
          provider_mode: null,
          training_window: null,
          baseline_comparison: null,
          feature_sources: [],
        }}
        backtest={null}
      />,
    );

    const text = container.textContent ?? '';
    expect(text).not.toContain('—');
    expect(text).not.toContain('n/a');
  });
});

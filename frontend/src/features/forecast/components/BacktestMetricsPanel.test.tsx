/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BacktestMetricsPanel } from './BacktestMetricsPanel';
import type { BacktestData } from '../../../lib/api/forecast.types';

const backtest: BacktestData = {
  product_code: 'AI_95',
  horizon_days: 7,
  model_type: 'catboost',
  window_type: 'rolling',
  metrics: { mae: 412, rmse: 553, smape: 4.8 },
  comparison: {
    catboost: { mae: 412, rmse: 553, smape: 4.8 },
    seasonal_naive: { mae: 520, rmse: 690, smape: 5.8 },
  },
  trained_at: '2026-04-06T10:00:00+00:00',
  model_version: '20260406100000',
};

describe('BacktestMetricsPanel', () => {
  it('explains forecast quality metrics without raw model labels', () => {
    const { container } = render(<BacktestMetricsPanel backtest={backtest} />);

    expect(screen.getByText('MAE: средняя ошибка 412.00 л')).toBeTruthy();
    expect(screen.getByText('RMSE: крупные промахи 553.00 л')).toBeTruthy();
    expect(screen.getByText('SMAPE: относительная ошибка 4.80%')).toBeTruthy();
    expect(screen.getByText(/Метод проверки: скользящая проверка/)).toBeTruthy();

    const text = container.textContent ?? '';
    expect(text).not.toContain('catboost');
    expect(text).not.toContain('rolling');
    expect(text).not.toContain('20260406100000');
    expect(text).not.toContain('n/a');
  });
});

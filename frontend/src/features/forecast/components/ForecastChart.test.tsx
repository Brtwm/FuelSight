/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ForecastChart } from './ForecastChart';

const useMediaQueryMock = vi.fn();

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => useMediaQueryMock(...args),
}));

vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: unknown }) => (
    <pre data-testid="forecast-option">{JSON.stringify(option)}</pre>
  ),
}));

describe('ForecastChart', () => {
  it('builds desktop legend and full labels', () => {
    useMediaQueryMock.mockReturnValue(false);
    render(
      <ForecastChart
        basePoints={[{ target_date: '2026-04-10', y_hat: 120, y_lo: 100, y_hi: 130 }]}
        scenarioPoints={[{ target_date: '2026-04-10', y_hat: 118, y_lo: 96, y_hi: 128 }]}
      />,
    );

    const option = JSON.parse(screen.getByTestId('forecast-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Base прогноз, л');
    expect(option.legend.data).toContain('Scenario прогноз, л');
    expect(option.legend.selected).toBeUndefined();
  });

  it('uses compact legend and hides interval series by default on mobile', () => {
    useMediaQueryMock.mockReturnValue(true);
    render(
      <ForecastChart
        basePoints={[{ target_date: '2026-04-10', y_hat: 120, y_lo: 100, y_hi: 130 }]}
        scenarioPoints={[{ target_date: '2026-04-10', y_hat: 118, y_lo: 96, y_hi: 128 }]}
      />,
    );

    const option = JSON.parse(screen.getByTestId('forecast-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Base');
    expect(option.legend.data).toContain('Scn');
    expect(option.legend.selected).toEqual({ Lo: false, Hi: false });
    expect(screen.getByText(/Сначала сравните base\/scenario/)).toBeTruthy();
  });
});

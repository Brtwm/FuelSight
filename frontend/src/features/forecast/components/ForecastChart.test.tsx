/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ForecastChart } from './ForecastChart';

const mediaQueryMock = vi.fn();

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

vi.mock('echarts-for-react', () => ({
  default: ({ option, style }: { option: { tooltip?: { formatter?: (params: unknown[]) => string } }; style?: { height?: number } }) => {
    const sampleTooltip = option.tooltip?.formatter?.([
      {
        seriesName: 'Базовый прогноз, л',
        value: 120,
        marker: '●',
        axisValueLabel: '2026-04-10',
        dataIndex: 0,
      },
      {
        seriesName: 'Доверительный интервал',
        value: 30,
        marker: '●',
        axisValueLabel: '2026-04-10',
        dataIndex: 0,
      },
      {
        seriesName: '_lo_band',
        value: 100,
        marker: '●',
        axisValueLabel: '2026-04-10',
        dataIndex: 0,
      },
    ]);
    return (
      <>
        <pre data-testid="forecast-option">{JSON.stringify(option)}</pre>
        <span data-testid="forecast-height">{style?.height}</span>
        <span data-testid="forecast-tooltip">{sampleTooltip}</span>
      </>
    );
  },
}));

describe('ForecastChart', () => {
  it('builds desktop legend and full labels', () => {
    mediaQueryMock.mockReturnValue(false);
    render(
      <ForecastChart
        basePoints={[{ target_date: '2026-04-10', y_hat: 120, y_lo: 100, y_hi: 130 }]}
        scenarioPoints={[{ target_date: '2026-04-10', y_hat: 118, y_lo: 96, y_hi: 128 }]}
      />,
    );

    const option = JSON.parse(screen.getByTestId('forecast-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Базовый прогноз, л');
    expect(option.legend.data).toContain('Сценарный прогноз, л');
    expect(option.legend.data).toContain('Доверительный интервал');
    expect(option.legend.data).not.toContain('_lo_band');
    expect(option.legend.selected).toBeUndefined();
    expect(option.dataZoom).toHaveLength(1);
    expect(option.series.find((item: { name: string }) => item.name === 'Доверительный интервал')?.areaStyle).toBeTruthy();
    expect(option.series.find((item: { name: string }) => item.name === 'Сценарный прогноз, л')?.lineStyle.type).toBe('dashed');
    expect(screen.getByTestId('forecast-height').textContent).toBe('400');
    expect(screen.getByTestId('forecast-tooltip').innerHTML).toContain('120 л');
    expect(screen.getByTestId('forecast-tooltip').innerHTML).toContain('100-130 л');
    expect(screen.getByTestId('forecast-tooltip').innerHTML).not.toContain('_lo_band');
  });

  it('uses compact legend and hides interval series by default on mobile', () => {
    mediaQueryMock.mockReturnValue(true);
    render(
      <ForecastChart
        basePoints={[{ target_date: '2026-04-10', y_hat: 120, y_lo: 100, y_hi: 130 }]}
        scenarioPoints={[{ target_date: '2026-04-10', y_hat: 118, y_lo: 96, y_hi: 128 }]}
      />,
    );

    const option = JSON.parse(screen.getByTestId('forecast-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Базовый');
    expect(option.legend.data).toContain('Сценарий');
    expect(option.legend.selected).toEqual({ 'Доверительный интервал': false });
    expect(option.dataZoom).toEqual([]);
    expect(screen.getByTestId('forecast-height').textContent).toBe('300');
    expect(screen.getByText(/Базовый и сценарный прогнозы/)).toBeTruthy();
  });
});

/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DemandSnapshotChart } from './DemandSnapshotChart';

const mediaQueryMock = vi.fn();

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

vi.mock('echarts-for-react', () => ({
  default: ({ option, style }: { option: { tooltip?: { formatter?: (params: unknown[]) => string } }; style?: { height?: number } }) => {
    const sampleTooltip = option.tooltip?.formatter?.([
      {
        seriesName: 'Продажи, л',
        value: 12400,
        marker: '●',
        axisValueLabel: '2026-04-06',
      },
      {
        seriesName: 'Розничная цена, ₽',
        value: 59.9,
        marker: '●',
        axisValueLabel: '2026-04-06',
      },
    ]);
    return (
      <>
        <pre data-testid="snapshot-option">{JSON.stringify(option)}</pre>
        <span data-testid="snapshot-height">{style?.height}</span>
        <span data-testid="snapshot-tooltip">{sampleTooltip}</span>
      </>
    );
  },
}));

describe('DemandSnapshotChart', () => {
  const baseProps = {
    points: [{ date: '2026-04-06', volume_liters: 12400, avg_retail_price_rub: 59.9 }],
    annotations: [],
    overlays: [
      {
        code: 'usd_rub',
        label: 'USD/RUB',
        points: [{ date: '2026-04-06', value: 89.7 }],
      },
    ],
    dataFreshness: 'fresh' as const,
    providerMode: 'cached' as const,
  };

  it('renders full legend labels on desktop', () => {
    mediaQueryMock.mockReturnValue(false);
    render(<DemandSnapshotChart {...baseProps} />);
    const option = JSON.parse(screen.getByTestId('snapshot-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Продажи, л');
    expect(option.legend.data).toContain('Розничная цена, ₽');
    expect(option.legend.selected).toBeUndefined();
    expect(option.dataZoom).toHaveLength(1);
    expect(option.series.find((item: { name: string }) => item.name === 'Продажи, л')?.itemStyle.color.type).toBe('linear');
    expect(option.series.find((item: { name: string }) => item.name === 'Розничная цена, ₽')?.areaStyle).toBeTruthy();
    expect(screen.getByTestId('snapshot-height').textContent).toBe('400');
    expect(screen.getByTestId('snapshot-tooltip').innerHTML).toContain('12&nbsp;400 л');
    expect(screen.getByTestId('snapshot-tooltip').innerHTML).toContain('59,9 ₽');
  });

  it('compresses legend and hides overlays by default on mobile', () => {
    mediaQueryMock.mockReturnValue(true);
    render(<DemandSnapshotChart {...baseProps} />);
    const option = JSON.parse(screen.getByTestId('snapshot-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Объём');
    expect(option.legend.data).toContain('Цена');
    expect(option.legend.data).toContain('Инд 1');
    expect(option.legend.selected).toEqual({ 'Инд 1': false });
    expect(option.dataZoom).toEqual([]);
    expect(screen.getByTestId('snapshot-height').textContent).toBe('300');
    expect(screen.getByText(/Ключевой сигнал/)).toBeTruthy();
  });
});

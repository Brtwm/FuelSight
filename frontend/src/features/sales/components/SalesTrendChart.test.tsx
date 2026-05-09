/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SalesTrendChart } from './SalesTrendChart';

vi.mock('echarts-for-react', () => ({
  default: ({ option, style }: { option: { tooltip?: { formatter?: (params: unknown[]) => string } }; style?: { height?: number } }) => {
    const sampleTooltip = option.tooltip?.formatter?.([
      {
        seriesName: 'Продажи, л',
        value: 12000,
        marker: '●',
        axisValueLabel: '2026-04-06',
      },
      {
        seriesName: 'Розничная цена, ₽',
        value: 59.8,
        marker: '●',
        axisValueLabel: '2026-04-06',
      },
    ]);
    return (
      <>
        <pre data-testid="sales-chart-option">{JSON.stringify(option)}</pre>
        <span data-testid="sales-chart-height">{style?.height}</span>
        <span data-testid="sales-chart-tooltip">{sampleTooltip}</span>
      </>
    );
  },
}));

describe('SalesTrendChart', () => {
  it('aligns overlay values by date labels instead of index', () => {
    render(
      <SalesTrendChart
        series={[
          { period_start: '2026-04-06', volume_liters: 12000, avg_retail_price_rub: 59.8 },
          { period_start: '2026-04-07', volume_liters: 12200, avg_retail_price_rub: 60.1 },
        ]}
        annotations={[{ id: 'a1', date: '2026-04-07', label: 'Аномалия спроса' }]}
        overlays={[
          {
            code: 'usd_rub',
            label: 'USD/RUB',
            provider_mode: 'cached',
            points: [
              { date: '2026-04-07', value: 90.2 },
            ],
          },
        ]}
      />,
    );

    const optionDump = screen.getByTestId('sales-chart-option').textContent ?? '';
    const option = JSON.parse(optionDump);
    const overlay = option.series.find((item: { name: string }) => item.name === 'USD/RUB');
    expect(overlay?.data).toEqual([null, 90.2]);
    expect(option.dataZoom).toHaveLength(1);
    expect(option.series.find((item: { name: string }) => item.name === 'Продажи, л')?.itemStyle.color.type).toBe('linear');
    expect(option.series.find((item: { name: string }) => item.name === 'Розничная цена, ₽')?.areaStyle).toBeTruthy();
    expect(screen.getByTestId('sales-chart-height').textContent).toBe('400');
    expect(screen.getByTestId('sales-chart-tooltip').innerHTML).toContain('12&nbsp;000 л');
    expect(screen.getByTestId('sales-chart-tooltip').innerHTML).toContain('59,8 ₽');
    expect(optionDump).toContain('USD/RUB');
    expect(optionDump).toContain('Аномалия спроса');
  });
});

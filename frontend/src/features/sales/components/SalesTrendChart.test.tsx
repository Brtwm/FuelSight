/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SalesTrendChart } from './SalesTrendChart';

vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: unknown }) => (
    <pre data-testid="sales-chart-option">{JSON.stringify(option)}</pre>
  ),
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
    expect(optionDump).toContain('USD/RUB');
    expect(optionDump).toContain('Аномалия спроса');
  });
});

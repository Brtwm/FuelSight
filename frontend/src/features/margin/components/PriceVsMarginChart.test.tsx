/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PriceVsMarginChart } from './PriceVsMarginChart';

vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: unknown }) => (
    <pre data-testid="margin-chart-option">{JSON.stringify(option)}</pre>
  ),
}));

describe('PriceVsMarginChart', () => {
  it('renders risk threshold band and supporting overlays', () => {
    render(
      <PriceVsMarginChart
        series={[
          {
            period_start: '2026-04-06',
            avg_purchase_price_rub: 55.1,
            avg_retail_price_rub: 60.0,
            gross_margin_rub: 47200,
            gross_margin_rub_per_liter: 4.9,
            gross_margin_pct: 8.2,
            purchase_data_missing: false,
          },
        ]}
        thresholdRubPerLiter={3}
        annotations={[{ id: 'm1', date: '2026-04-06', label: 'Ниже порога' }]}
        overlays={[
          {
            code: 'wholesale_gasoline_index',
            label: 'Оптовый индекс бензина',
            provider_mode: 'manual_snapshot',
            points: [{ date: '2026-04-06', value: 103.4 }],
          },
        ]}
      />,
    );

    const optionDump = screen.getByTestId('margin-chart-option').textContent ?? '';
    expect(optionDump).toContain('Порог 3.00');
    expect(optionDump).toContain('Оптовый индекс бензина');
  });
});

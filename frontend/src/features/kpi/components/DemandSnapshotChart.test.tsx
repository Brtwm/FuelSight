/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DemandSnapshotChart } from './DemandSnapshotChart';

const mediaQueryMock = vi.fn();

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: unknown }) => (
    <pre data-testid="snapshot-option">{JSON.stringify(option)}</pre>
  ),
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
    expect(option.legend.data).toContain('Розничная цена, руб');
    expect(option.legend.selected).toBeUndefined();
  });

  it('compresses legend and hides overlays by default on mobile', () => {
    mediaQueryMock.mockReturnValue(true);
    render(<DemandSnapshotChart {...baseProps} />);
    const option = JSON.parse(screen.getByTestId('snapshot-option').textContent ?? '{}');
    expect(option.legend.data).toContain('Объём');
    expect(option.legend.data).toContain('Цена');
    expect(option.legend.data).toContain('OV1');
    expect(option.legend.selected).toEqual({ OV1: false });
    expect(screen.getByText(/Ключевой сигнал/)).toBeTruthy();
  });
});

/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ComparisonsPanel } from './ComparisonsPanel';

describe('ComparisonsPanel', () => {
  it('renders YoY N/A explanation when yoy is null', () => {
    render(
      <ComparisonsPanel
        comparisons={{ mom_pct: 2.4, yoy_pct: null }}
        dataMode="cached"
      />,
    );

    expect(screen.getByText('YoY: N/A (недостаточно истории)')).toBeTruthy();
    expect(screen.getByText('Режим данных: cached')).toBeTruthy();
  });
});

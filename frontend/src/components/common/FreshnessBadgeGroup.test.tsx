/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FreshnessBadgeGroup, resolveFreshnessBadge } from './FreshnessBadgeGroup';

describe('FreshnessBadgeGroup', () => {
  it('maps freshness status to label', () => {
    expect(resolveFreshnessBadge('fresh').label).toBe('fresh');
    expect(resolveFreshnessBadge('warning').label).toBe('warning');
    expect(resolveFreshnessBadge('degraded').label).toBe('degraded');
    expect(resolveFreshnessBadge(null).label).toBe('n/a');
  });

  it('renders fallback badges', () => {
    render(
      <FreshnessBadgeGroup
        dataFreshness={null}
        modelFreshness={null}
        newsFreshness={null}
        showFallback
      />,
    );
    expect(screen.getByText('Data: n/a')).toBeTruthy();
    expect(screen.getByText('Model: n/a')).toBeTruthy();
    expect(screen.getByText('News: n/a')).toBeTruthy();
  });
});

/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FreshnessBadgeGroup, resolveFreshnessBadge } from './FreshnessBadgeGroup';

describe('FreshnessBadgeGroup', () => {
  it('maps freshness status to label', () => {
    expect(resolveFreshnessBadge('fresh').label).toBe('свежие');
    expect(resolveFreshnessBadge('warning').label).toBe('проверить');
    expect(resolveFreshnessBadge('degraded').label).toBe('устарели');
    expect(resolveFreshnessBadge(null).label).toBe('нет данных');
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
    expect(screen.getByText('Данные: нет данных')).toBeTruthy();
    expect(screen.getByText('Модель: нет данных')).toBeTruthy();
    expect(screen.getByText('Новости: нет данных')).toBeTruthy();
  });

  it('renders compact badges', () => {
    render(
      <FreshnessBadgeGroup
        dataFreshness="fresh"
        modelFreshness="warning"
        newsFreshness="degraded"
        compact
      />,
    );
    expect(screen.getByText('Д:ок')).toBeTruthy();
    expect(screen.getByText('М:пров.')).toBeTruthy();
    expect(screen.getByText('Н:уст.')).toBeTruthy();
  });
});

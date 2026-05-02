/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SourceModeBadge, resolveSourceModeBadge } from './SourceModeBadge';

describe('SourceModeBadge', () => {
  it('maps provider modes to labels', () => {
    expect(resolveSourceModeBadge('live').label).toBe('live');
    expect(resolveSourceModeBadge('cached').label).toBe('cache');
    expect(resolveSourceModeBadge('manual_snapshot').label).toBe('snapshot');
    expect(resolveSourceModeBadge('retrieval_only').label).toBe('По источникам');
    expect(resolveSourceModeBadge(null).label).toBe('n/a');
  });

  it('renders badge with title', () => {
    render(<SourceModeBadge title="LLM" mode="cloud_llm" />);
    expect(screen.getByText('LLM: Облако')).toBeTruthy();
  });

  it('renders compact badge variant', () => {
    render(<SourceModeBadge title="Indicators" compactTitle="Ind" mode="manual_snapshot" compact />);
    expect(screen.getByText('Ind: snap')).toBeTruthy();
  });
});

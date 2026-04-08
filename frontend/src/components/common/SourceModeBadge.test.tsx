/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SourceModeBadge, resolveSourceModeBadge } from './SourceModeBadge';

describe('SourceModeBadge', () => {
  it('maps provider modes to labels', () => {
    expect(resolveSourceModeBadge('live').label).toBe('live');
    expect(resolveSourceModeBadge('cached').label).toBe('cached');
    expect(resolveSourceModeBadge('manual_snapshot').label).toBe('manual snapshot');
    expect(resolveSourceModeBadge('retrieval_only').label).toBe('retrieval only');
    expect(resolveSourceModeBadge(null).label).toBe('n/a');
  });

  it('renders badge with title', () => {
    render(<SourceModeBadge title="LLM" mode="cloud_llm" />);
    expect(screen.getByText('LLM: cloud llm')).toBeTruthy();
  });
});

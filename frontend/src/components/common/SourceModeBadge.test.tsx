/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SourceModeBadge, resolveSourceModeBadge } from './SourceModeBadge';

describe('SourceModeBadge', () => {
  it('maps provider modes to labels', () => {
    expect(resolveSourceModeBadge('live').label).toBe('актуально');
    expect(resolveSourceModeBadge('cached').label).toBe('сохранённые данные');
    expect(resolveSourceModeBadge('manual_snapshot').label).toBe('проверено');
    expect(resolveSourceModeBadge('retrieval_only').label).toBe('по источникам');
    expect(resolveSourceModeBadge(null).label).toBe('нет данных');
  });

  it('renders badge with title', () => {
    render(<SourceModeBadge title="Генерация ответа" mode="cloud_llm" />);
    expect(screen.getByText('Генерация ответа: с генерацией')).toBeTruthy();
  });

  it('renders compact badge variant', () => {
    render(<SourceModeBadge title="Индикаторы" compactTitle="Инд." mode="manual_snapshot" compact />);
    expect(screen.getByText('Инд.: пров.')).toBeTruthy();
  });
});

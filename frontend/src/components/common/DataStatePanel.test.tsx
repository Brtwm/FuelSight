/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DataStatePanel } from './DataStatePanel';

describe('DataStatePanel', () => {
  it('renders loading state', () => {
    render(<DataStatePanel state="loading" loadingLabel="Загружаем..." />);
    expect(screen.getByText('Загружаем...')).toBeTruthy();
  });

  it('renders empty state', () => {
    render(
      <DataStatePanel
        state="empty"
        emptyTitle="Пусто"
        emptyDescription="Нет доступных данных"
      />,
    );
    expect(screen.getByText('Пусто')).toBeTruthy();
    expect(screen.getByText('Нет доступных данных')).toBeTruthy();
  });

  it('renders error state and retry action', () => {
    const onRetry = vi.fn();
    render(
      <DataStatePanel
        state="error"
        errorMessage="Ошибка загрузки"
        onRetry={onRetry}
      />,
    );
    expect(screen.getByText('Ошибка загрузки')).toBeTruthy();
    screen.getByRole('button', { name: 'Повторить' }).click();
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('renders ready state children', () => {
    render(
      <DataStatePanel state="ready">
        <div>READY_CONTENT</div>
      </DataStatePanel>,
    );
    expect(screen.getByText('READY_CONTENT')).toBeTruthy();
  });
});

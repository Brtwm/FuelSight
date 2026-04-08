/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ChartCard } from './ChartCard';

describe('ChartCard', () => {
  it('renders loading state', () => {
    render(<ChartCard title="График" state="loading" loadingLabel="Идёт загрузка" />);
    expect(screen.getByText('График')).toBeTruthy();
    expect(screen.getByText('Идёт загрузка')).toBeTruthy();
  });

  it('renders empty state', () => {
    render(
      <ChartCard
        title="График"
        state="empty"
        emptyTitle="Данные отсутствуют"
        emptyDescription="Проверьте фильтры"
      />,
    );
    expect(screen.getByText('Данные отсутствуют')).toBeTruthy();
    expect(screen.getByText('Проверьте фильтры')).toBeTruthy();
  });

  it('renders error state', () => {
    render(
      <ChartCard title="График" state="error" errorMessage="Ошибка загрузки данных" />,
    );
    expect(screen.getByText('Ошибка загрузки данных')).toBeTruthy();
  });

  it('renders ready state with children and slots', () => {
    render(
      <ChartCard
        title="График"
        subtitle="Подзаголовок"
        state="ready"
        badgeSlot={<div>BADGE_SLOT</div>}
        summarySlot={<div>SUMMARY_SLOT</div>}
      >
        <div>CHART_CONTENT</div>
      </ChartCard>,
    );
    expect(screen.getByText('Подзаголовок')).toBeTruthy();
    expect(screen.getByText('BADGE_SLOT')).toBeTruthy();
    expect(screen.getByText('SUMMARY_SLOT')).toBeTruthy();
    expect(screen.getByText('CHART_CONTENT')).toBeTruthy();
  });
});

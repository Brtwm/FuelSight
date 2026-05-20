/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShell } from './AppShell';
import type { UserRole } from '../../lib/api/auth.types';

const { mediaQueryMock, logoutMock, authState } = vi.hoisted(() => ({
  mediaQueryMock: vi.fn(),
  logoutMock: vi.fn(),
  authState: { role: 'admin' },
}));

vi.mock('../../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    user: { role: authState.role },
    logout: logoutMock,
    authFetch: vi.fn(),
  }),
}));

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

function renderShell(initialEntry = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route path="dashboard" element={<div>DASHBOARD_PAGE</div>} />
          <Route path="forecast" element={<div>FORECAST_PAGE</div>} />
          <Route path="import" element={<div>IMPORT_PAGE</div>} />
          <Route path="news" element={<div>NEWS_PAGE</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('AppShell', () => {
  beforeEach(() => {
    mediaQueryMock.mockReset();
    mediaQueryMock.mockReturnValue(false);
    logoutMock.mockReset();
    logoutMock.mockResolvedValue(undefined);
    authState.role = 'admin' satisfies UserRole;
  });

  it('renders a clean desktop app bar without status or provider badges', () => {
    renderShell('/dashboard');

    expect(screen.getByText('DASHBOARD_PAGE')).toBeTruthy();
    expect(screen.getByText('Системный администратор')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Выйти' })).toBeTruthy();
    expect(screen.queryByText(/^Защита:/)).toBeNull();
    expect(screen.queryByText(/^Данные:/)).toBeNull();
    expect(screen.queryByText(/^Модель:/)).toBeNull();
    expect(screen.queryByText(/^Новости:/)).toBeNull();
    expect(screen.queryByText(/^LLM:/)).toBeNull();
    expect(screen.queryByText(/^Индикаторы:/)).toBeNull();
  });

  it('logs out from the clean app bar action', async () => {
    const user = userEvent.setup();
    renderShell('/dashboard');

    await user.click(screen.getByRole('button', { name: 'Выйти' }));

    expect(logoutMock).toHaveBeenCalledOnce();
  });

  it('navigates between desktop drawer routes', async () => {
    const user = userEvent.setup();
    renderShell('/dashboard');

    await user.click(screen.getByRole('button', { name: 'Прогноз спроса' }));

    expect(await screen.findByText('FORECAST_PAGE')).toBeTruthy();
  });

  it('shows all main navigation items for admin', () => {
    renderShell('/dashboard');

    expect(screen.getByRole('button', { name: 'KPI' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Импорт данных' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Аналитика продаж' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Аналитика маржи' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Прогноз спроса' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Новости' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Отчеты' })).toBeTruthy();
  });

  it('shows sales navigation without purchase import', () => {
    authState.role = 'sales' satisfies UserRole;

    renderShell('/dashboard');

    expect(screen.getByText('Отдел продаж')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Импорт продаж' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Аналитика продаж' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Прогноз спроса' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Импорт закупок' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Финансовая сводка' })).toBeNull();
  });

  it('shows accounting navigation without sales import', () => {
    authState.role = 'accounting' satisfies UserRole;

    renderShell('/dashboard');

    expect(screen.getByText('Бухгалтерия')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Импорт закупок' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Финансовая сводка' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Импорт продаж' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Продажи' })).toBeNull();
  });

  it('shows analyst analytics, RAG chat, and reports without import history', () => {
    authState.role = 'analyst' satisfies UserRole;

    renderShell('/dashboard');

    expect(screen.getByText('Аналитик')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Импорт/ })).toBeNull();
    expect(screen.getByRole('button', { name: 'Аналитика продаж' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Аналитика маржи' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Прогноз спроса' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Новости и RAG-чат' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Отчеты' })).toBeTruthy();
  });

  it('shows director executive navigation without import', () => {
    authState.role = 'director' satisfies UserRole;

    renderShell('/dashboard');

    expect(screen.getByText('Генеральный директор')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Панель руководителя' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Риски маржи' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Сводка прогноза' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Новостная сводка' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Отчет руководителя' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Импорт/ })).toBeNull();
  });

  it('renders mobile navigation from the same role-aware items', async () => {
    mediaQueryMock.mockReturnValue(true);
    const user = userEvent.setup();
    renderShell('/dashboard');

    expect(screen.getByRole('button', { name: 'Прогноз спроса' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Импорт данных' })).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Прогноз спроса' }));
    expect(await screen.findByText('FORECAST_PAGE')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Импорт данных' }));
    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });
});

/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShell } from './AppShell';

const { mediaQueryMock, logoutMock } = vi.hoisted(() => ({
  mediaQueryMock: vi.fn(),
  logoutMock: vi.fn(),
}));

vi.mock('../../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    user: { role: 'admin' },
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
  });

  it('renders a clean desktop app bar without status or provider badges', () => {
    renderShell('/dashboard');

    expect(screen.getByText('DASHBOARD_PAGE')).toBeTruthy();
    expect(screen.getByText('Администратор')).toBeTruthy();
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

    await user.click(screen.getByRole('button', { name: 'Прогноз' }));

    expect(await screen.findByText('FORECAST_PAGE')).toBeTruthy();
  });

  it('renders hybrid mobile navigation with bottom nav and drawer overflow', async () => {
    mediaQueryMock.mockReturnValue(true);
    const user = userEvent.setup();
    renderShell('/dashboard');

    expect(screen.getByRole('button', { name: 'Прогноз' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Импорт' })).toBeNull();

    await user.click(screen.getByRole('button', { name: 'Прогноз' }));
    expect(await screen.findByText('FORECAST_PAGE')).toBeTruthy();

    await user.click(screen.getByLabelText('Открыть меню'));
    await user.click(await screen.findByRole('button', { name: 'Импорт' }));
    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });
});

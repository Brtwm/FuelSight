/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { UserRole } from '../../lib/api/auth.types';
import { AppRouter } from './AppRouter';

const { authState } = vi.hoisted(() => ({
  authState: { role: 'director' },
}));

vi.mock('../../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    status: 'authenticated',
    isAuthenticated: true,
    user: { role: authState.role },
    logout: vi.fn(),
    authFetch: vi.fn(),
  }),
}));

vi.mock('@mui/material/useMediaQuery', () => ({
  default: () => false,
}));

vi.mock('../../pages/DashboardPage', () => ({
  DashboardPage: () => <div>DASHBOARD_PAGE</div>,
}));

function renderRouter(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRouter />
    </MemoryRouter>,
  );
}

describe('AppRouter role guards', () => {
  beforeEach(() => {
    authState.role = 'director' satisfies UserRole;
  });

  it('blocks direct director access to import route', async () => {
    renderRouter('/import');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.getByText('У вашей роли нет доступа к этому разделу (HTTP 403).')).toBeTruthy();
  });

  it('allows director executive dashboard alias', async () => {
    renderRouter('/executive/dashboard');

    expect(await screen.findByText('DASHBOARD_PAGE')).toBeTruthy();
  });

  it('allows analyst access to reports route', async () => {
    authState.role = 'analyst' satisfies UserRole;

    renderRouter('/reports');

    expect(await screen.findByText('Управленческие отчёты')).toBeTruthy();
  });
});

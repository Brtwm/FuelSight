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

vi.mock('../../pages/ImportPage', () => ({
  ImportPage: () => <div>IMPORT_PAGE</div>,
}));

vi.mock('../../pages/ReportsPage', () => ({
  ReportsPage: () => <div>REPORTS_PAGE</div>,
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

  it('blocks director access to split import routes', async () => {
    renderRouter('/import/sales');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('IMPORT_PAGE')).toBeNull();
  });

  it('blocks analyst access to import history route', async () => {
    authState.role = 'analyst' satisfies UserRole;

    renderRouter('/import/history');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('IMPORT_PAGE')).toBeNull();
  });

  it('blocks sales direct access to purchase import route', async () => {
    authState.role = 'sales' satisfies UserRole;

    renderRouter('/import/purchases');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('IMPORT_PAGE')).toBeNull();
  });

  it('blocks accounting direct access to sales import route', async () => {
    authState.role = 'accounting' satisfies UserRole;

    renderRouter('/import/sales');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('IMPORT_PAGE')).toBeNull();
  });

  it('allows accounting direct access to purchase import route', async () => {
    authState.role = 'accounting' satisfies UserRole;

    renderRouter('/import/purchases');

    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });

  it('redirects sales from base import route to sales import', async () => {
    authState.role = 'sales' satisfies UserRole;

    renderRouter('/import');

    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });

  it('redirects accounting from base import route to purchase import', async () => {
    authState.role = 'accounting' satisfies UserRole;

    renderRouter('/import');

    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });

  it('allows director executive dashboard alias', async () => {
    renderRouter('/executive/dashboard');

    expect(await screen.findByText('DASHBOARD_PAGE')).toBeTruthy();
  });

  it('allows analyst access to reports route', async () => {
    authState.role = 'analyst' satisfies UserRole;

    renderRouter('/reports');

    expect(await screen.findByText('REPORTS_PAGE')).toBeTruthy();
  });

  it('allows director access to executive reports route', async () => {
    authState.role = 'director' satisfies UserRole;

    renderRouter('/reports/executive');

    expect(await screen.findByText('REPORTS_PAGE')).toBeTruthy();
  });

  it('blocks sales direct access to executive reports route', async () => {
    authState.role = 'sales' satisfies UserRole;

    renderRouter('/reports/executive');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('REPORTS_PAGE')).toBeNull();
  });

  it('blocks accounting direct access to executive reports route', async () => {
    authState.role = 'accounting' satisfies UserRole;

    renderRouter('/reports/executive');

    expect(await screen.findByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('REPORTS_PAGE')).toBeNull();
  });
});

/** @vitest-environment jsdom */

import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import { ProtectedRoute } from './ProtectedRoute';

const useAuthMock = vi.fn();

vi.mock('../AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

describe('ProtectedRoute', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it('renders 403 access denied state for forbidden role', () => {
    useAuthMock.mockReturnValue({
      status: 'authenticated',
      isAuthenticated: true,
      user: { role: 'analyst' },
    });

    render(
      <MemoryRouter>
        <ProtectedRoute allowedRoles={['admin']}>
          <div>secret</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.getByText('Доступ ограничен')).toBeTruthy();
    expect(screen.getByText('У вашей роли нет доступа к этому разделу (HTTP 403).')).toBeTruthy();
  });

  it('renders 403 access denied state for forbidden route key', () => {
    useAuthMock.mockReturnValue({
      status: 'authenticated',
      isAuthenticated: true,
      user: { role: 'director' },
    });

    render(
      <MemoryRouter>
        <ProtectedRoute routeKey="import">
          <div>secret</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.getByText('Доступ ограничен')).toBeTruthy();
    expect(screen.queryByText('secret')).toBeNull();
  });

  it('allows permitted route key access', () => {
    useAuthMock.mockReturnValue({
      status: 'authenticated',
      isAuthenticated: true,
      user: { role: 'director' },
    });

    render(
      <MemoryRouter>
        <ProtectedRoute routeKey="forecast">
          <div>forecast</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.getByText('forecast')).toBeTruthy();
  });

  it('redirects unauthenticated user to /login', () => {
    useAuthMock.mockReturnValue({
      status: 'unauthenticated',
      isAuthenticated: false,
      user: null,
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>secret</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>LOGIN_PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('LOGIN_PAGE')).toBeTruthy();
  });
});

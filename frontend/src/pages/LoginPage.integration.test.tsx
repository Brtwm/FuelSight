/** @vitest-environment jsdom */

import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ApiHttpError } from '../lib/api/http';
import { LoginPage } from './LoginPage';

const useAuthMock = vi.fn();

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it('shows invalid credentials message when login fails with invalid_credentials', async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockRejectedValue(
      new ApiHttpError({
        status: 401,
        code: 'invalid_credentials',
        message: 'Invalid credentials',
      }),
    );

    useAuthMock.mockReturnValue({
      status: 'unauthenticated',
      isAuthenticated: false,
      user: null,
      login: loginMock,
      sessionExpired: false,
      clearSessionExpired: vi.fn(),
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: 'Войти' }));

    expect(await screen.findByText('Неверный email или пароль')).toBeTruthy();
    expect(loginMock).toHaveBeenCalledOnce();
  });

  it('shows session expired warning', () => {
    useAuthMock.mockReturnValue({
      status: 'unauthenticated',
      isAuthenticated: false,
      user: null,
      login: vi.fn(),
      sessionExpired: true,
      clearSessionExpired: vi.fn(),
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Сессия истекла. Выполните вход повторно.')).toBeTruthy();
  });

  it('shows analyst-first business copy', () => {
    useAuthMock.mockReturnValue({
      status: 'unauthenticated',
      isAuthenticated: false,
      user: null,
      login: vi.fn(),
      sessionExpired: false,
      clearSessionExpired: vi.fn(),
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Analyst mode по умолчанию')).toBeTruthy();
    expect(screen.getByText('Аналитика спроса, маржи и внешнего контекста для нефтепродуктов')).toBeTruthy();
  });

  it('uses analyst credentials as default form values', () => {
    useAuthMock.mockReturnValue({
      status: 'unauthenticated',
      isAuthenticated: false,
      user: null,
      login: vi.fn(),
      sessionExpired: false,
      clearSessionExpired: vi.fn(),
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('analyst@fuelsight.local');
    expect((screen.getByLabelText('Пароль') as HTMLInputElement).value).toBe('analyst12345');
  });

  it('redirects to preferred landing route for authenticated user', () => {
    useAuthMock.mockReturnValue({
      status: 'authenticated',
      isAuthenticated: true,
      user: {
        preferred_landing_route: '/dashboard',
      },
      login: vi.fn(),
      sessionExpired: false,
      clearSessionExpired: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.queryByText('Вход в систему')).toBeNull();
  });
});

/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('keeps demo analyst credentials by default', () => {
    render(<LoginForm loading={false} onSubmit={vi.fn()} />);

    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe(
      'analyst@fuelsight.local',
    );
    expect((screen.getByLabelText('Пароль') as HTMLInputElement).value).toBe('analyst12345');
  });

  it('renders empty credentials when demo credentials are disabled', () => {
    render(<LoginForm loading={false} onSubmit={vi.fn()} demoCredentialsEnabled={false} />);

    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText('Пароль') as HTMLInputElement).value).toBe('');
  });
});

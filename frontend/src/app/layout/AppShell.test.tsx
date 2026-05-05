/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useEffect } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAppShellSlots } from './AppShellSlotsContext';
import { AppShell } from './AppShell';

const useQueryMock = vi.fn();
const mediaQueryMock = vi.fn();

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: (...args: unknown[]) => useQueryMock(...args),
  };
});

vi.mock('../../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    user: { role: 'admin' },
    logout: vi.fn().mockResolvedValue(undefined),
    authFetch: vi.fn(),
  }),
}));

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

function queryState(overrides: Record<string, unknown> = {}) {
  return {
    isLoading: false,
    isError: false,
    data: null,
    ...overrides,
  };
}

function SlotSetterPage() {
  const { patchSlots } = useAppShellSlots();
  useEffect(() => {
    patchSlots({
      dataFreshness: 'fresh',
      modelFreshness: 'warning',
      llmMode: 'retrieval_only',
      newsFreshness: 'degraded',
      externalIndicatorsMode: 'cached',
    });
  }, [patchSlots]);
  return <div>DASHBOARD_PAGE</div>;
}

describe('AppShell slots', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    mediaQueryMock.mockReset();
    mediaQueryMock.mockReturnValue(false);
    useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
      const queryKey = options.queryKey ?? [];
      if (queryKey[0] === 'backend-health') {
        return queryState({ data: { ok: true } });
      }
      if (queryKey[0] === 'auth-session') {
        return queryState({ data: { role: 'admin' } });
      }
      return queryState();
    });
  });

  it('renders fallback slot badges when route does not provide values', () => {
    render(
      <MemoryRouter initialEntries={['/forecast']}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route path="dashboard" element={<SlotSetterPage />} />
            <Route path="forecast" element={<div>FORECAST_PAGE</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Data: n/a')).toBeTruthy();
    expect(screen.getByText('Model: n/a')).toBeTruthy();
    expect(screen.getByText('News: n/a')).toBeTruthy();
    expect(screen.getByText('LLM: n/a')).toBeTruthy();
    expect(screen.getByText('Indicators: n/a')).toBeTruthy();
  });

  it('renders defense and provider badges from backend health when route slots are empty', () => {
    useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
      const queryKey = options.queryKey ?? [];
      if (queryKey[0] === 'backend-health') {
        return queryState({
          data: {
            ok: true,
            defense_profile: 'cloud-enhanced',
            external_indicators_mode: 'manual_snapshot',
            llm_active: {
              provider: 'neuraldeep',
              mode: 'cloud_llm',
              model: 'gpt-oss-120b',
              degradation_reason: null,
            },
          },
        });
      }
      if (queryKey[0] === 'auth-session') {
        return queryState({ data: { role: 'admin' } });
      }
      return queryState();
    });

    render(
      <MemoryRouter initialEntries={['/forecast']}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route path="forecast" element={<div>FORECAST_PAGE</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Defense: cloud-enhanced')).toBeTruthy();
    expect(screen.getByText('LLM: Облако')).toBeTruthy();
    expect(screen.getByText('Indicators: snapshot')).toBeTruthy();
  });

  it('renders route slots and resets them on route change', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route path="dashboard" element={<SlotSetterPage />} />
            <Route path="forecast" element={<div>FORECAST_PAGE</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText('Data: fresh')).toBeTruthy();
    expect(screen.getByText('Model: warning')).toBeTruthy();
    expect(screen.getByText('News: degraded')).toBeTruthy();
    expect(screen.getByText('LLM: По источникам')).toBeTruthy();
    expect(screen.getByText('Indicators: cache')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Прогноз' }));

    expect(await screen.findByText('FORECAST_PAGE')).toBeTruthy();
    expect(await screen.findByText('Data: n/a')).toBeTruthy();
    expect(screen.getByText('LLM: n/a')).toBeTruthy();
  });

  it('renders hybrid mobile navigation with bottom nav and drawer overflow', async () => {
    mediaQueryMock.mockReturnValue(true);
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route path="dashboard" element={<SlotSetterPage />} />
            <Route path="forecast" element={<div>FORECAST_PAGE</div>} />
            <Route path="import" element={<div>IMPORT_PAGE</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('button', { name: 'Прогноз' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Импорт' })).toBeNull();

    await user.click(screen.getByRole('button', { name: 'Прогноз' }));
    expect(await screen.findByText('FORECAST_PAGE')).toBeTruthy();

    await user.click(screen.getByLabelText('Открыть меню'));
    await user.click(await screen.findByRole('button', { name: 'Импорт' }));
    expect(await screen.findByText('IMPORT_PAGE')).toBeTruthy();
  });
});

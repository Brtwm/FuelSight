/** @vitest-environment jsdom */

import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NewsPage } from './NewsPage';

const { mediaQueryMock, useQueryMock, useMutationMock } = vi.hoisted(() => ({
  mediaQueryMock: vi.fn(),
  useQueryMock: vi.fn(),
  useMutationMock: vi.fn(),
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: (...args: unknown[]) => useQueryMock(...args),
    useMutation: (...args: unknown[]) => useMutationMock(...args),
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
      fetchQuery: vi.fn(),
    }),
  };
});

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => mediaQueryMock(...args),
}));

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    authFetch: vi.fn(),
    user: { role: 'analyst' },
  }),
}));

vi.mock('../features/news/components/NewsDigestPanel', () => ({
  NewsDigestPanel: () => <div>NEWS_DIGEST_PANEL</div>,
}));

vi.mock('../features/news/components/NewsSearchDrawer', () => ({
  NewsSearchDrawer: () => <div>NEWS_SEARCH_DRAWER</div>,
}));

vi.mock('../features/news/components/ChatThread', () => ({
  ChatThread: () => <div>CHAT_THREAD</div>,
}));

function queryState(overrides: Record<string, unknown> = {}) {
  return {
    isLoading: false,
    isError: false,
    data: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

function mockNewsQueries(healthMode: 'cloud_llm' | 'retrieval_only') {
  useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
    const queryKey = options?.queryKey ?? [];
    if (queryKey[0] === 'backend-health') {
      return queryState({
        data: {
          ok: true,
          enable_llm: healthMode !== 'retrieval_only',
          llm_active: {
            provider: healthMode === 'cloud_llm' ? 'neuraldeep' : 'none',
            mode: healthMode,
            model: healthMode === 'cloud_llm' ? 'gpt-oss-120b' : null,
            degradation_reason: null,
          },
        },
      });
    }
    if (queryKey[0] === 'news' && queryKey[1] === 'digest') {
      return queryState({
        data: {
          data: {
            llm_mode: 'off',
            news_freshness: 'fresh',
          },
          meta: {
            llm_mode: 'retrieval_only',
            news_freshness: 'fresh',
          },
        },
      });
    }
    if (queryKey[0] === 'news' && queryKey[1] === 'search') {
      return queryState({ data: { data: [], meta: {} } });
    }
    if (queryKey[0] === 'chat') {
      return queryState({ data: [] });
    }
    return queryState();
  });
}

function renderNewsPage() {
  render(
    <MemoryRouter initialEntries={['/news']}>
      <NewsPage />
    </MemoryRouter>,
  );
}

describe('NewsPage LLM status', () => {
  beforeEach(() => {
    mediaQueryMock.mockReset();
    mediaQueryMock.mockReturnValue(false);
    useQueryMock.mockReset();
    useMutationMock.mockReset();
    useMutationMock.mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      data: null,
    });
  });

  it('uses backend health to keep generation enabled on the news page', () => {
    mockNewsQueries('cloud_llm');

    renderNewsPage();

    expect(screen.getByRole('heading', { name: 'Сводка и чат' })).toBeTruthy();
    expect(screen.queryByText('без генерации')).toBeNull();
  });

  it('shows a page-level generation fallback badge for retrieval-only mode', () => {
    mockNewsQueries('retrieval_only');

    renderNewsPage();

    expect(screen.getByText('без генерации')).toBeTruthy();
  });

  it('renders digest, search and sticky chat together on desktop', () => {
    mediaQueryMock.mockReturnValue(false);
    mockNewsQueries('cloud_llm');

    renderNewsPage();

    expect(screen.queryByRole('tab', { name: 'Сводка' })).toBeNull();
    expect(screen.getByText('NEWS_DIGEST_PANEL')).toBeTruthy();
    expect(screen.getByText('NEWS_SEARCH_DRAWER')).toBeTruthy();
    expect(screen.getByText('CHAT_THREAD')).toBeTruthy();
    expect(screen.getByTestId('news-desktop-chat-pane')).toBeTruthy();
  });

  it('uses mobile tabs to switch between digest, search and chat panes', () => {
    mediaQueryMock.mockReturnValue(true);
    mockNewsQueries('retrieval_only');

    renderNewsPage();

    expect(screen.getByRole('tab', { name: 'Сводка' })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Поиск' })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Чат' })).toBeTruthy();
    expect(screen.getByText('NEWS_DIGEST_PANEL')).toBeTruthy();
    expect(screen.queryByText('NEWS_SEARCH_DRAWER')).toBeNull();
    expect(screen.queryByText('CHAT_THREAD')).toBeNull();

    fireEvent.click(screen.getByRole('tab', { name: 'Поиск' }));
    expect(screen.getByText('NEWS_SEARCH_DRAWER')).toBeTruthy();
    expect(screen.queryByText('NEWS_DIGEST_PANEL')).toBeNull();
    expect(screen.queryByText('CHAT_THREAD')).toBeNull();

    fireEvent.click(screen.getByRole('tab', { name: 'Чат' }));
    expect(screen.getByText('CHAT_THREAD')).toBeTruthy();
    expect(screen.getByTestId('news-mobile-chat-pane')).toBeTruthy();
    expect(screen.queryByText('NEWS_DIGEST_PANEL')).toBeNull();
    expect(screen.queryByText('NEWS_SEARCH_DRAWER')).toBeNull();
  });
});

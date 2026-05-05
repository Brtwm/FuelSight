/** @vitest-environment jsdom */

import { render, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NewsPage } from './NewsPage';

const useQueryMock = vi.fn();
const useMutationMock = vi.fn();
const patchSlotsMock = vi.fn();

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

vi.mock('../app/layout/AppShellSlotsContext', () => ({
  useAppShellSlots: () => ({
    patchSlots: patchSlotsMock,
  }),
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

describe('NewsPage LLM status', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    useMutationMock.mockReset();
    patchSlotsMock.mockReset();
    useMutationMock.mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
    });
  });

  it('uses health llm_active as the global shell LLM status', async () => {
    useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
      const queryKey = options?.queryKey ?? [];
      if (queryKey[0] === 'backend-health') {
        return queryState({
          data: {
            ok: true,
            enable_llm: true,
            llm_active: {
              provider: 'neuraldeep',
              mode: 'cloud_llm',
              model: 'gpt-oss-120b',
              degradation_reason: null,
            },
          },
        });
      }
      if (queryKey[0] === 'news' && queryKey[1] === 'digest') {
        return queryState({
          data: {
            data: {
              llm_mode: 'template_rag',
              news_freshness: 'fresh',
            },
            meta: {
              llm_mode: 'local_llm',
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

    render(
      <MemoryRouter initialEntries={['/news']}>
        <NewsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(patchSlotsMock).toHaveBeenCalledWith(
        expect.objectContaining({
          llmMode: 'cloud_llm',
        }),
      );
    });
  });
});

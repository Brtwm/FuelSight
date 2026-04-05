import { Alert, Chip, Grid, Stack, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { checkBackendHealth } from '../lib/api/client';
import { ChatThread } from '../features/news/components/ChatThread';
import { NewsDigestPanel } from '../features/news/components/NewsDigestPanel';
import { NewsSearchDrawer } from '../features/news/components/NewsSearchDrawer';
import { buildDefaultNewsRange, resolveNewsFilters, toSearchParams } from '../features/news/urlFilters';
import { useAuth } from '../features/auth/AuthProvider';
import { askChatQuestion, createChatSession, fetchChatMessages } from '../lib/api/chat';
import type { ChatScope } from '../lib/api/chat.types';
import { fetchLatestNewsDigest, refreshNews, searchNews } from '../lib/api/news';
import { ENABLE_LLM } from '../lib/config/env';

export function NewsPage() {
  const queryClient = useQueryClient();
  const { authFetch, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [sessionId, setSessionId] = useState<string | null>(null);

  const defaults = useMemo(() => buildDefaultNewsRange(), []);
  const filters = useMemo(() => resolveNewsFilters(searchParams, defaults), [defaults, searchParams]);

  useEffect(() => {
    const normalized = toSearchParams(filters).toString();
    if (searchParams.toString() !== normalized) {
      setSearchParams(toSearchParams(filters), { replace: true });
    }
  }, [filters, searchParams, setSearchParams]);

  const digestQuery = useQuery({
    queryKey: ['news', 'digest', filters.period_type],
    queryFn: () => fetchLatestNewsDigest(authFetch, filters.period_type),
  });

  const healthQuery = useQuery({
    queryKey: ['backend-health'],
    queryFn: checkBackendHealth,
  });

  const searchQuery = useQuery({
    queryKey: ['news', 'search', filters],
    queryFn: () =>
      searchNews(authFetch, {
        q: filters.q || undefined,
        topic: filters.topic || undefined,
        date_from: filters.date_from,
        date_to: filters.date_to,
        limit: 25,
      }),
  });

  const refreshMutation = useMutation({
    mutationFn: () => refreshNews(authFetch),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['news', 'digest'] }),
        queryClient.invalidateQueries({ queryKey: ['news', 'search'] }),
      ]);
    },
  });

  const createSessionMutation = useMutation({
    mutationFn: (title: string) => createChatSession(authFetch, { title }),
  });

  const messagesQuery = useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: () => fetchChatMessages(authFetch, sessionId ?? ''),
    enabled: Boolean(sessionId),
  });

  const askMutation = useMutation({
    mutationFn: (params: { sessionId: string; question: string; context_scope: ChatScope[] }) =>
      askChatQuestion(authFetch, params.sessionId, {
        question: params.question,
        context_scope: params.context_scope,
      }),
  });

  const updateFilter = (patch: Partial<typeof filters>) => {
    setSearchParams(toSearchParams({ ...filters, ...patch }));
  };

  const sendQuestion = async (payload: { question: string; context_scope: ChatScope[] }) => {
    let activeSessionId = sessionId;
    if (!activeSessionId) {
      const shortTitle =
        payload.question.length > 64 ? `${payload.question.slice(0, 61)}...` : payload.question;
      const session = await createSessionMutation.mutateAsync(shortTitle);
      activeSessionId = session.id;
      setSessionId(activeSessionId);
    }

    await askMutation.mutateAsync({
      sessionId: activeSessionId,
      question: payload.question,
      context_scope: payload.context_scope,
    });
    await queryClient.fetchQuery({
      queryKey: ['chat', 'messages', activeSessionId],
      queryFn: () => fetchChatMessages(authFetch, activeSessionId),
    });
  };

  const chatError = createSessionMutation.isError || askMutation.isError || messagesQuery.isError;
  const isLlmEnabled =
    healthQuery.data?.enable_llm ?? (digestQuery.data ? digestQuery.data.llm_mode !== 'off' : ENABLE_LLM);
  const onSelectSource = (sourceId: string) => {
    updateFilter({ q: sourceId });
  };

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="h4" fontWeight={700}>
            Сводка новостей и чат
          </Typography>
          {!isLlmEnabled ? <Chip size="small" color="warning" label="LLM off" /> : null}
        </Stack>
        <Typography color="text.secondary">
          Digest и поиск остаются доступными всегда. Для чата требуются retrieval и генерация с источниками.
        </Typography>
        <Stack direction="row" spacing={1}>
          <Chip
            size="small"
            label="Дневная сводка"
            color={filters.period_type === 'daily' ? 'primary' : 'default'}
            onClick={() => updateFilter({ period_type: 'daily' })}
          />
          <Chip
            size="small"
            label="Недельная сводка"
            color={filters.period_type === 'weekly' ? 'primary' : 'default'}
            onClick={() => updateFilter({ period_type: 'weekly' })}
          />
        </Stack>
      </Stack>

      {askMutation.isError && isLlmEnabled ? (
        <Alert severity="error">Не удалось получить ответ чата. Проверьте backend и повторите запрос.</Alert>
      ) : null}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Stack spacing={2}>
            <NewsDigestPanel
              digest={digestQuery.data ?? null}
              isLoading={digestQuery.isLoading}
              hasError={digestQuery.isError}
              onRetry={() => void digestQuery.refetch()}
              canRefresh={user?.role === 'admin'}
              isRefreshing={refreshMutation.isPending}
              onRefresh={() => refreshMutation.mutate()}
              onSelectSource={onSelectSource}
            />

            <NewsSearchDrawer
              q={filters.q}
              topic={filters.topic}
              dateFrom={filters.date_from}
              dateTo={filters.date_to}
              isLoading={searchQuery.isLoading}
              hasError={searchQuery.isError}
              results={searchQuery.data ?? []}
              onQChange={(value) => updateFilter({ q: value })}
              onTopicChange={(value) => updateFilter({ topic: value })}
              onDateFromChange={(value) => updateFilter({ date_from: value })}
              onDateToChange={(value) => updateFilter({ date_to: value })}
              onRetry={() => void searchQuery.refetch()}
            />
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <ChatThread
            messages={messagesQuery.data ?? []}
            isLoading={messagesQuery.isLoading}
            isSending={createSessionMutation.isPending || askMutation.isPending}
            isLlmEnabled={isLlmEnabled}
            hasError={chatError}
            onRetry={() => {
              if (sessionId) {
                void messagesQuery.refetch();
              }
            }}
            onNewsCitationClick={onSelectSource}
            onSend={sendQuestion}
          />
        </Grid>
      </Grid>
    </Stack>
  );
}

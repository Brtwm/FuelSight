import { Alert, Chip, Grid, Stack, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAppShellSlots } from '../app/layout/AppShellSlotsContext';
import { checkBackendHealth } from '../lib/api/client';
import { ChatThread } from '../features/news/components/ChatThread';
import { NewsDigestPanel } from '../features/news/components/NewsDigestPanel';
import { NewsSearchDrawer } from '../features/news/components/NewsSearchDrawer';
import { buildDefaultNewsRange, resolveNewsFilters, toSearchParams } from '../features/news/urlFilters';
import { useAuth } from '../features/auth/AuthProvider';
import { askChatQuestion, createChatSession, fetchChatMessages } from '../lib/api/chat';
import type { ChatScope } from '../lib/api/chat.types';
import {
  fetchLatestNewsDigestWithMeta,
  refreshNewsWithMeta,
  searchNewsWithMeta,
} from '../lib/api/news';
import { ENABLE_LLM } from '../lib/config/env';

export function NewsPage() {
  const theme = useTheme();
  const isMobileReadingOrder = useMediaQuery(theme.breakpoints.down('md'));
  const queryClient = useQueryClient();
  const { patchSlots } = useAppShellSlots();
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
    queryFn: () => fetchLatestNewsDigestWithMeta(authFetch, filters.period_type),
  });

  const healthQuery = useQuery({
    queryKey: ['backend-health'],
    queryFn: checkBackendHealth,
  });

  const searchQuery = useQuery({
    queryKey: ['news', 'search', filters],
    queryFn: () =>
      searchNewsWithMeta(authFetch, {
        q: filters.q || undefined,
        topic: filters.topic || undefined,
        date_from: filters.date_from,
        date_to: filters.date_to,
        limit: 25,
      }),
  });

  const refreshMutation = useMutation({
    mutationFn: () => refreshNewsWithMeta(authFetch),
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
  const digest = digestQuery.data?.data ?? null;
  const digestMeta = digestQuery.data?.meta;
  const searchResults = searchQuery.data?.data ?? [];
  const mapDigestLlmMode = (value: string | null | undefined) => {
    if (!value) {
      return null;
    }
    if (value === 'off') {
      return 'retrieval_only' as const;
    }
    if (value === 'template_rag') {
      return 'local_llm' as const;
    }
    return null;
  };
  const llmMode = digestMeta?.llm_mode ?? mapDigestLlmMode(digest?.llm_mode) ?? 'retrieval_only';
  const dataFreshness = digestMeta?.data_freshness ?? null;
  const modelFreshness = digestMeta?.model_freshness ?? null;
  const newsFreshness = digestMeta?.news_freshness ?? digest?.news_freshness ?? null;
  const externalIndicatorsMode =
    digestMeta?.external_indicators_mode
    ?? digest?.context_story?.external_context?.provider_mode
    ?? null;

  useEffect(() => {
    patchSlots({
      dataFreshness,
      modelFreshness,
      llmMode,
      newsFreshness,
      externalIndicatorsMode,
    });
  }, [
    dataFreshness,
    externalIndicatorsMode,
    llmMode,
    modelFreshness,
    newsFreshness,
    patchSlots,
  ]);

  const isLlmEnabled =
    healthQuery.data?.enable_llm ?? (digest ? digest.llm_mode !== 'off' : ENABLE_LLM);
  const onSelectSource = (sourceId: string) => {
    updateFilter({ q: sourceId });
  };

  return (
    <Stack spacing={3} sx={{ minWidth: 0, overflowX: 'hidden' }}>
      <Stack spacing={1}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1}
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          useFlexGap
          flexWrap="wrap"
        >
          <Typography variant="h4" fontWeight={700} sx={{ minWidth: 0 }}>
            Сводка новостей и чат
          </Typography>
          {!isLlmEnabled ? <Chip size="small" color="warning" label="retrieval only" /> : null}
        </Stack>
        <Typography color="text.secondary">
          Digest, поиск и чат работают по сохранённым источникам; генерация подключается только поверх citations.
        </Typography>
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
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

      {askMutation.isError ? (
        <Alert severity="error">Не удалось получить ответ чата. Проверьте backend и повторите запрос.</Alert>
      ) : null}

      {isMobileReadingOrder ? (
        <Stack spacing={2}>
          <NewsDigestPanel
            digest={digest}
            isLoading={digestQuery.isLoading}
            hasError={digestQuery.isError}
            onRetry={() => void digestQuery.refetch()}
            canRefresh={user?.role === 'admin'}
            isRefreshing={refreshMutation.isPending}
            onRefresh={() => refreshMutation.mutate()}
            onSelectSource={onSelectSource}
          />
          <ChatThread
            messages={messagesQuery.data ?? []}
            isLoading={messagesQuery.isLoading}
            isSending={createSessionMutation.isPending || askMutation.isPending}
            isLlmEnabled={isLlmEnabled}
            llmProvider={askMutation.data?.llm_provider ?? null}
            hasError={chatError}
            onRetry={() => {
              if (sessionId) {
                void messagesQuery.refetch();
              }
            }}
            onNewsCitationClick={onSelectSource}
            onSend={sendQuestion}
          />
          <NewsSearchDrawer
            q={filters.q}
            topic={filters.topic}
            dateFrom={filters.date_from}
            dateTo={filters.date_to}
            isLoading={searchQuery.isLoading}
            hasError={searchQuery.isError}
            results={searchResults}
            onQChange={(value) => updateFilter({ q: value })}
            onTopicChange={(value) => updateFilter({ topic: value })}
            onDateFromChange={(value) => updateFilter({ date_from: value })}
            onDateToChange={(value) => updateFilter({ date_to: value })}
            onRetry={() => void searchQuery.refetch()}
          />
        </Stack>
      ) : (
        <Grid container spacing={2} sx={{ minWidth: 0 }}>
          <Grid size={{ xs: 12, lg: 7 }} sx={{ minWidth: 0 }}>
            <Stack spacing={2}>
              <NewsDigestPanel
                digest={digest}
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
                results={searchResults}
                onQChange={(value) => updateFilter({ q: value })}
                onTopicChange={(value) => updateFilter({ topic: value })}
                onDateFromChange={(value) => updateFilter({ date_from: value })}
                onDateToChange={(value) => updateFilter({ date_to: value })}
                onRetry={() => void searchQuery.refetch()}
              />
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, lg: 5 }} sx={{ minWidth: 0 }}>
            <ChatThread
              messages={messagesQuery.data ?? []}
              isLoading={messagesQuery.isLoading}
              isSending={createSessionMutation.isPending || askMutation.isPending}
              isLlmEnabled={isLlmEnabled}
              llmProvider={askMutation.data?.llm_provider ?? null}
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
      )}
    </Stack>
  );
}

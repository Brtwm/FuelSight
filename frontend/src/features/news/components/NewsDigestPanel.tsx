import { Alert, Button, Card, CardContent, Chip, Skeleton, Stack, Typography } from '@mui/material';
import { useState } from 'react';
import { ExternalContextPanel, SourceModeBadge, resolveFreshnessBadge } from '../../../components/common';
import type { NewsDigestData } from '../../../lib/api/news.types';

type Props = {
  digest: NewsDigestData | null;
  isLoading: boolean;
  isRefreshing: boolean;
  canRefresh: boolean;
  onRefresh: () => void;
  onRetry: () => void;
  onSelectSource: (sourceId: string) => void;
  hasError: boolean;
};

export function NewsDigestPanel({
  digest,
  isLoading,
  isRefreshing,
  canRefresh,
  onRefresh,
  onRetry,
  onSelectSource,
  hasError,
}: Props) {
  const [isSourcesVisible, setIsSourcesVisible] = useState(false);
  const refreshLabelDate = digest?.created_at ?? digest?.digest_date ?? null;

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
            <Typography variant="h6" fontWeight={700}>
              Сводка
            </Typography>
            {digest ? (
              <Chip
                size="small"
                label={
                  refreshLabelDate
                    ? `Обновлено · ${new Date(refreshLabelDate).toLocaleString('ru-RU', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}`
                    : 'Сводка обновлена'
                }
              />
            ) : null}
          </Stack>

          {isLoading ? (
            <>
              <Skeleton variant="rounded" height={24} />
              <Skeleton variant="rounded" height={24} />
              <Skeleton variant="rounded" height={24} />
            </>
          ) : null}

          {!isLoading && hasError ? (
            <Alert
              severity="error"
              action={
                <Button color="inherit" size="small" onClick={onRetry}>
                  Повторить
                </Button>
              }
            >
              Не удалось загрузить сводку.
            </Alert>
          ) : null}

          {!isLoading && !hasError && !digest ? (
            <Alert severity="info">Сводка пока отсутствует. Нажмите «Обновить» для генерации.</Alert>
          ) : null}

          {!isLoading && digest ? (
            <Stack spacing={1}>
              <Typography>{digest.summary_text}</Typography>
              {digest.bullet_points.map((point, index) => (
                <Typography key={index} variant="body2" color="text.secondary">
                  • {point}
                </Typography>
              ))}
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                <SourceModeBadge mode={digest.provider_mode} title="Контур новостей" />
                {digest.news_freshness ? (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={`Новости: ${resolveFreshnessBadge(digest.news_freshness).label}`}
                  />
                ) : null}
              </Stack>
              <ExternalContextPanel
                context={digest.context_story?.external_context ?? null}
                title="Контекст периода"
                refsLimit={4}
                extraLines={(digest.context_story?.event_context ?? [])
                  .slice(0, 3)
                  .map((item) => `${item.title}: ${item.start_date} - ${item.end_date}`)}
                emptyMessage="Контекст периода пока не собран."
              />
              {digest.context_story ? (
                <Typography variant="caption" color="text.secondary">
                  Ссылки на индикаторы: {digest.context_story.indicator_refs.length}; события: {digest.context_story.event_refs.length}
                </Typography>
              ) : null}
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Button
                  size="small"
                  onClick={() => setIsSourcesVisible((previousValue) => !previousValue)}
                >
                  {isSourcesVisible
                    ? 'Скрыть источники'
                    : `Показать источники (${digest.source_ids.length})`}
                </Button>
                <Typography variant="caption" color="text.secondary">
                  Откройте источник в поиске и перейдите к материалу.
                </Typography>
              </Stack>
              {isSourcesVisible ? (
                <Stack spacing={0.5}>
                  {digest.source_ids.map((sourceId) => (
                    <Button
                      key={sourceId}
                      size="small"
                      variant="text"
                      sx={{ justifyContent: 'flex-start' }}
                      onClick={() => onSelectSource(sourceId)}
                    >
                      {sourceId}
                    </Button>
                  ))}
                </Stack>
              ) : null}
            </Stack>
          ) : null}

          {canRefresh ? (
            <Stack direction="row" justifyContent="flex-end">
              <Button variant="outlined" onClick={onRefresh} disabled={isRefreshing}>
                {isRefreshing ? 'Обновление...' : 'Обновить'}
              </Button>
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

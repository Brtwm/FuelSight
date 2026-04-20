import { Alert, Button, Card, CardContent, Chip, Skeleton, Stack, Typography } from '@mui/material';
import { useState } from 'react';
import { ExternalContextPanel } from '../../../components/common';
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
                  digest.period_type === 'daily'
                    ? `Дневная · ${new Date(digest.digest_date).toLocaleDateString('ru-RU')}`
                    : `Недельная · ${new Date(digest.digest_date).toLocaleDateString('ru-RU')}`
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
              Не удалось загрузить digest.
            </Alert>
          ) : null}

          {!isLoading && !hasError && !digest ? (
            <Alert severity="info">Digest пока отсутствует. Нажмите «Обновить» для генерации.</Alert>
          ) : null}

          {!isLoading && digest ? (
            <Stack spacing={1}>
              <Typography>{digest.summary_text}</Typography>
              {digest.bullet_points.map((point, index) => (
                <Typography key={index} variant="body2" color="text.secondary">
                  • {point}
                </Typography>
              ))}
              <ExternalContextPanel
                context={digest.context_story?.external_context ?? null}
                title="Контекст периода"
                refsLimit={4}
                extraLines={(digest.context_story?.event_context ?? [])
                  .slice(0, 3)
                  .map((item) => `${item.title}: ${item.start_date} - ${item.end_date}`)}
                emptyMessage="Контекстный story для digest пока не собран."
              />
              {digest.context_story ? (
                <Typography variant="caption" color="text.secondary">
                  indicator refs: {digest.context_story.indicator_refs.length}, event refs: {digest.context_story.event_refs.length}
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

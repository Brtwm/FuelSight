import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

export type DataState = 'loading' | 'empty' | 'degraded' | 'error' | 'ready';

type DataStatePanelProps = {
  state: DataState;
  loadingLabel?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  degradedTitle?: string;
  degradedDescription?: string;
  errorMessage?: string;
  retryLabel?: string;
  onRetry?: () => void;
  actionLabel?: string;
  onAction?: () => void;
  children?: ReactNode;
};

export function DataStatePanel({
  state,
  loadingLabel = 'Загрузка данных...',
  emptyTitle = 'Данные отсутствуют',
  emptyDescription = 'Загрузите начальные данные или обновите фильтры.',
  degradedTitle = 'Данные частично ограничены',
  degradedDescription = 'Показываем доступную аналитику, но часть контекста может быть неполной.',
  errorMessage = 'Не удалось загрузить данные.',
  retryLabel = 'Повторить',
  onRetry,
  actionLabel,
  onAction,
  children,
}: DataStatePanelProps) {
  if (state === 'loading') {
    return (
      <Stack spacing={1.5} alignItems="center" justifyContent="center" sx={{ minHeight: 220 }}>
        <CircularProgress size={28} />
        <Typography color="text.secondary">{loadingLabel}</Typography>
      </Stack>
    );
  }

  if (state === 'empty') {
    return (
      <Stack spacing={1} sx={{ minHeight: 160, justifyContent: 'center' }}>
        <Typography variant="h6" fontWeight={700}>
          {emptyTitle}
        </Typography>
        <Typography color="text.secondary">{emptyDescription}</Typography>
        {actionLabel && onAction ? (
          <Stack direction="row" sx={{ pt: 0.5 }}>
            <Button variant="contained" size="small" onClick={onAction}>
              {actionLabel}
            </Button>
          </Stack>
        ) : null}
      </Stack>
    );
  }

  if (state === 'degraded') {
    return (
      <Stack spacing={1.5}>
        <Alert severity="warning">{degradedTitle}</Alert>
        <Typography color="text.secondary">{degradedDescription}</Typography>
        {actionLabel && onAction ? (
          <Stack direction="row" sx={{ pt: 0.5 }}>
            <Button variant="outlined" size="small" onClick={onAction}>
              {actionLabel}
            </Button>
          </Stack>
        ) : null}
        {children}
      </Stack>
    );
  }

  if (state === 'error') {
    return (
      <Alert
        severity="error"
        action={
          onRetry ? (
            <Button color="inherit" size="small" onClick={onRetry}>
              {retryLabel}
            </Button>
          ) : undefined
        }
      >
        {errorMessage}
      </Alert>
    );
  }

  return <Box>{children}</Box>;
}

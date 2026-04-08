import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

export type DataState = 'loading' | 'empty' | 'error' | 'ready';

type DataStatePanelProps = {
  state: DataState;
  loadingLabel?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  errorMessage?: string;
  retryLabel?: string;
  onRetry?: () => void;
  children?: ReactNode;
};

export function DataStatePanel({
  state,
  loadingLabel = 'Загрузка данных...',
  emptyTitle = 'Данные отсутствуют',
  emptyDescription = 'Загрузите начальные данные или обновите фильтры.',
  errorMessage = 'Не удалось загрузить данные.',
  retryLabel = 'Повторить',
  onRetry,
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

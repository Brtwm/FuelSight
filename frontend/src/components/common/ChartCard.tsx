import { Card, CardContent, Divider, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';
import { DataStatePanel, type DataState } from './DataStatePanel';

type ChartCardProps = {
  title: string;
  subtitle?: string;
  state: DataState;
  badgeSlot?: ReactNode;
  summarySlot?: ReactNode;
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

export function ChartCard({
  title,
  subtitle,
  state,
  badgeSlot,
  summarySlot,
  loadingLabel,
  emptyTitle,
  emptyDescription,
  degradedTitle,
  degradedDescription,
  errorMessage,
  retryLabel,
  onRetry,
  actionLabel,
  onAction,
  children,
}: ChartCardProps) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={1}
            alignItems={{ xs: 'flex-start', md: 'center' }}
            justifyContent="space-between"
          >
            <Stack spacing={0.5}>
              <Typography variant="h6" fontWeight={700}>
                {title}
              </Typography>
              {subtitle ? <Typography color="text.secondary">{subtitle}</Typography> : null}
            </Stack>
            {badgeSlot}
          </Stack>

          {summarySlot ? (
            <>
              <Divider />
              {summarySlot}
            </>
          ) : null}

          <DataStatePanel
            state={state}
            loadingLabel={loadingLabel}
            emptyTitle={emptyTitle}
            emptyDescription={emptyDescription}
            degradedTitle={degradedTitle}
            degradedDescription={degradedDescription}
            errorMessage={errorMessage}
            retryLabel={retryLabel}
            onRetry={onRetry}
            actionLabel={actionLabel}
            onAction={onAction}
          >
            {children}
          </DataStatePanel>
        </Stack>
      </CardContent>
    </Card>
  );
}

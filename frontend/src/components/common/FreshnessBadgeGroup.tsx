/* eslint-disable react-refresh/only-export-components */
import { Chip, Stack } from '@mui/material';
import type { ChipProps } from '@mui/material';
import type { FreshnessStatus } from '../../lib/api/common.types';

const FRESHNESS_LABELS: Record<FreshnessStatus, string> = {
  fresh: 'fresh',
  warning: 'warning',
  degraded: 'degraded',
};

const FRESHNESS_COLORS: Record<FreshnessStatus, ChipProps['color']> = {
  fresh: 'success',
  warning: 'warning',
  degraded: 'error',
};

export function resolveFreshnessBadge(status: FreshnessStatus | null | undefined): {
  label: string;
  color: ChipProps['color'];
} {
  if (!status) {
    return { label: 'n/a', color: 'default' };
  }
  return {
    label: FRESHNESS_LABELS[status],
    color: FRESHNESS_COLORS[status],
  };
}

type FreshnessBadgeGroupProps = {
  dataFreshness: FreshnessStatus | null | undefined;
  modelFreshness: FreshnessStatus | null | undefined;
  newsFreshness: FreshnessStatus | null | undefined;
  showFallback?: boolean;
  compact?: boolean;
};

export function FreshnessBadgeGroup({
  dataFreshness,
  modelFreshness,
  newsFreshness,
  showFallback = true,
  compact = false,
}: FreshnessBadgeGroupProps) {
  const entries = [
    { title: 'Data', status: dataFreshness },
    { title: 'Model', status: modelFreshness },
    { title: 'News', status: newsFreshness },
  ].filter((item) => showFallback || item.status);

  if (entries.length === 0) {
    return null;
  }

  return (
    <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
      {entries.map((item) => {
        const resolved = resolveFreshnessBadge(item.status);
        const compactLabel = resolved.label
          .replace('fresh', 'ok')
          .replace('warning', 'warn')
          .replace('degraded', 'deg');
        return (
          <Chip
            key={item.title}
            size="small"
            variant="outlined"
            color={resolved.color}
            label={compact ? `${item.title[0]}:${compactLabel}` : `${item.title}: ${resolved.label}`}
            sx={
              compact
                ? {
                    height: 22,
                    '& .MuiChip-label': {
                      px: 0.75,
                      fontSize: '0.68rem',
                      fontWeight: 600,
                    },
                  }
                : undefined
            }
          />
        );
      })}
    </Stack>
  );
}

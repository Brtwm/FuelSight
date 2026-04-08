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
};

export function FreshnessBadgeGroup({
  dataFreshness,
  modelFreshness,
  newsFreshness,
  showFallback = true,
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
        return (
          <Chip
            key={item.title}
            size="small"
            variant="outlined"
            color={resolved.color}
            label={`${item.title}: ${resolved.label}`}
          />
        );
      })}
    </Stack>
  );
}

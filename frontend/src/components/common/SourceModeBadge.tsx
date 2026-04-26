/* eslint-disable react-refresh/only-export-components */
import { Chip } from '@mui/material';
import type { ChipProps } from '@mui/material';
import type { ProviderMode } from '../../lib/api/common.types';

const MODE_LABELS: Record<ProviderMode, string> = {
  live: 'live',
  cached: 'cached',
  manual_snapshot: 'manual snapshot',
  cloud_llm: 'cloud llm',
  local_llm: 'local llm',
  retrieval_only: 'retrieval only',
};

const MODE_COLORS: Record<ProviderMode, ChipProps['color']> = {
  live: 'success',
  cached: 'info',
  manual_snapshot: 'warning',
  cloud_llm: 'success',
  local_llm: 'info',
  retrieval_only: 'warning',
};

export function resolveSourceModeBadge(mode: ProviderMode | null | undefined): {
  label: string;
  color: ChipProps['color'];
} {
  if (!mode) {
    return { label: 'n/a', color: 'default' };
  }
  return {
    label: MODE_LABELS[mode],
    color: MODE_COLORS[mode],
  };
}

type SourceModeBadgeProps = {
  mode: ProviderMode | null | undefined;
  title: string;
  showFallback?: boolean;
  compact?: boolean;
  compactTitle?: string;
};

export function SourceModeBadge({
  mode,
  title,
  showFallback = true,
  compact = false,
  compactTitle,
}: SourceModeBadgeProps) {
  if (!mode && !showFallback) {
    return null;
  }
  const resolved = resolveSourceModeBadge(mode);
  const compactLabel = resolved.label
    .replace('manual snapshot', 'snap')
    .replace('retrieval only', 'retr')
    .replace('cloud llm', 'cloud')
    .replace('local llm', 'local')
    .replace('cached', 'cache');
  return (
    <Chip
      size="small"
      variant="outlined"
      color={resolved.color}
      label={`${compact ? (compactTitle ?? title) : title}: ${compact ? compactLabel : resolved.label}`}
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
}

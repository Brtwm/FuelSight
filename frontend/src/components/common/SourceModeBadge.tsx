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
};

export function SourceModeBadge({
  mode,
  title,
  showFallback = true,
}: SourceModeBadgeProps) {
  if (!mode && !showFallback) {
    return null;
  }
  const resolved = resolveSourceModeBadge(mode);
  return (
    <Chip
      size="small"
      variant="outlined"
      color={resolved.color}
      label={`${title}: ${resolved.label}`}
    />
  );
}

/* eslint-disable react-refresh/only-export-components */
import { Chip } from '@mui/material';
import type { ChipProps } from '@mui/material';
import type { ProviderMode } from '../../lib/api/common.types';

const MODE_LABELS: Record<ProviderMode, string> = {
  live: 'актуально',
  cached: 'сохранённые данные',
  manual_snapshot: 'проверено',
  cloud_llm: 'с генерацией',
  local_llm: 'локальная генерация',
  retrieval_only: 'по источникам',
};

const MODE_COLORS: Record<ProviderMode, ChipProps['color']> = {
  live: 'success',
  cached: 'info',
  manual_snapshot: 'success',
  cloud_llm: 'success',
  local_llm: 'info',
  retrieval_only: 'warning',
};

export function resolveSourceModeBadge(mode: ProviderMode | null | undefined): {
  label: string;
  color: ChipProps['color'];
} {
  if (!mode) {
    return { label: 'нет данных', color: 'default' };
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
    .replace('актуально', 'акт.')
    .replace('проверено', 'пров.')
    .replace('сохранённые данные', 'сохр.')
    .replace('по источникам', 'ист.')
    .replace('с генерацией', 'ген.')
    .replace('локальная генерация', 'лок.');
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

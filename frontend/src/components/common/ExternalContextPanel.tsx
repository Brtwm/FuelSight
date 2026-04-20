import { Alert, Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { ChipProps } from '@mui/material';
import type { ExternalContextQuality, SupportingRef, QualityStatus } from '../../lib/api/common.types';
import { SourceModeBadge } from './SourceModeBadge';

const QUALITY_COLORS: Record<QualityStatus, ChipProps['color']> = {
  ok: 'success',
  warning: 'warning',
  degraded: 'error',
  failed: 'error',
};

type Props = {
  context: ExternalContextQuality | null | undefined;
  title?: string;
  emptyMessage?: string;
  refsLimit?: number;
  extraLines?: string[];
};

function formatRatio(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a';
  }
  return `${(value * 100).toFixed(1)}%`;
}

function qualityLabel(value: QualityStatus | null | undefined): string {
  if (!value) {
    return 'n/a';
  }
  return value;
}

function safeRefs(value: SupportingRef[] | undefined, refsLimit: number): SupportingRef[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, Math.max(refsLimit, 1));
}

export function ExternalContextPanel({
  context,
  title = 'Внешний контекст',
  emptyMessage = 'Контекст внешних индикаторов пока недоступен.',
  refsLimit = 3,
  extraLines = [],
}: Props) {
  if (!context) {
    return <Alert severity="info">{emptyMessage}</Alert>;
  }

  const qualityStatus = context.quality_status ?? null;
  const qualityColor = qualityStatus ? QUALITY_COLORS[qualityStatus] : 'default';
  const reasonLines = context.reasons ?? [];
  const refs = safeRefs(context.source_refs, refsLimit);

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={1.2}>
          <Typography variant="subtitle2" fontWeight={700}>
            {title}
          </Typography>
          <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
            <Chip size="small" color={qualityColor} variant="outlined" label={`quality: ${qualityLabel(qualityStatus)}`} />
            <Chip size="small" variant="outlined" label={`coverage: ${formatRatio(context.coverage_ratio)}`} />
            <Chip size="small" variant="outlined" label={`fallback: ${formatRatio(context.fallback_ratio)}`} />
            <SourceModeBadge mode={context.provider_mode ?? null} title="mode" compact />
          </Stack>
          {context.manifest_run_date ? (
            <Typography variant="caption" color="text.secondary">
              Последний валидный контекст: {new Date(context.manifest_run_date).toLocaleDateString('ru-RU')}
            </Typography>
          ) : null}
          {reasonLines.length > 0 ? (
            <Stack spacing={0.25}>
              {reasonLines.slice(0, 3).map((reason) => (
                <Typography key={reason} variant="caption" color="text.secondary">
                  - {reason}
                </Typography>
              ))}
            </Stack>
          ) : null}
          {extraLines.length > 0 ? (
            <Stack spacing={0.25}>
              {extraLines.map((line) => (
                <Typography key={line} variant="caption" color="text.secondary">
                  - {line}
                </Typography>
              ))}
            </Stack>
          ) : null}
          {refs.length > 0 ? (
            <Stack spacing={0.25}>
              {refs.map((ref) => (
                <Typography key={ref.ref_id} variant="caption" color="text.secondary">
                  - {ref.title}
                </Typography>
              ))}
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

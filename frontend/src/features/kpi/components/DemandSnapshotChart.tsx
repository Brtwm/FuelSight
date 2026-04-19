import ReactECharts from 'echarts-for-react';
import { Stack, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import {
  ChartCard,
  FreshnessBadgeGroup,
  SourceModeBadge,
  type DataState,
} from '../../../components/common';
import type { ChartAnnotation, ReferenceOverlay, FreshnessStatus, ProviderMode } from '../../../lib/api/common.types';
import type { KpiSnapshotPoint } from '../../../lib/api/kpi.types';

type Props = {
  points: KpiSnapshotPoint[];
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
  state?: DataState;
  dataFreshness?: FreshnessStatus | null;
  providerMode?: ProviderMode | null;
  emptyTitle?: string;
  emptyDescription?: string;
  onRetry?: () => void;
};

export function DemandSnapshotChart({
  points,
  annotations = [],
  overlays = [],
  state = 'ready',
  dataFreshness = null,
  providerMode = null,
  emptyTitle,
  emptyDescription,
  onRetry,
}: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));
  const formatDateLabel = (value: string) =>
    new Date(value).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: isCompact ? 'numeric' : '2-digit',
    });
  const labels = points.map((item) => formatDateLabel(item.date));
  const volumeLabel = isCompact ? 'Объём' : 'Продажи, л';
  const priceLabel = isCompact ? 'Цена' : 'Розничная цена, руб';
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: formatDateLabel(item.date as string),
      yAxis: points.find((point) => point.date === item.date)?.volume_liters ?? null,
      value: item.label,
    }));

  const overlaySeries = overlays.map((overlay, index) => {
    const overlayLabel = isCompact ? `OV${index + 1}` : overlay.label;
    const valuesByLabel = new Map(
      (overlay.points ?? [])
        .filter((point) => point.date)
        .map((point) => [formatDateLabel(point.date as string), point.value ?? null]),
    );
    return {
      name: overlayLabel,
      type: 'line',
      yAxisIndex: 1,
      data: labels.map((label) => valuesByLabel.get(label) ?? null),
      lineStyle: { type: 'dashed', width: 1.5 },
      symbol: 'none',
    };
  });

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: [volumeLabel, priceLabel, ...overlaySeries.map((item) => item.name)],
      selected: isCompact
        ? Object.fromEntries(overlaySeries.map((item) => [item.name, false]))
        : undefined,
    },
    grid: {
      left: isCompact ? 8 : 24,
      right: isCompact ? 8 : 24,
      top: isCompact ? 34 : 40,
      bottom: isCompact ? 16 : 24,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        hideOverlap: true,
        fontSize: isCompact ? 10 : 12,
      },
    },
    yAxis: [
      { type: 'value', name: 'Литры' },
      { type: 'value', name: 'Цена', position: 'right' },
    ],
    series: [
      {
        name: volumeLabel,
        type: 'bar',
        yAxisIndex: 0,
        data: points.map((item) => item.volume_liters),
        itemStyle: { color: '#0a4e8a' },
        markPoint: annotationPoints.length > 0 ? { data: annotationPoints } : undefined,
      },
      {
        name: priceLabel,
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: points.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#9b6a00' },
      },
      ...overlaySeries,
    ],
  };

  return (
    <ChartCard
      title="Динамика спроса"
      state={state}
      emptyTitle={emptyTitle}
      emptyDescription={emptyDescription}
      onRetry={onRetry}
      badgeSlot={(
        <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={null}
            newsFreshness={null}
            showFallback={false}
          />
          <SourceModeBadge mode={providerMode} title="Indicators" showFallback={false} />
        </Stack>
      )}
    >
      <Typography variant="body2" color="text.secondary">
        {isCompact
          ? 'Ключевой сигнал: объём и цена. Дополнительные overlays можно включить в legend.'
          : 'Спрос и цена показаны совместно, overlays помогают объяснить внешний контекст.'}
      </Typography>
      <ReactECharts option={option} style={{ height: isCompact ? 264 : 320 }} />
    </ChartCard>
  );
}

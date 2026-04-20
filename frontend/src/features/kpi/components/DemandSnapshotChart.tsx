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
  const timeline = points.map((item) => item.date);
  const eventOverlays = overlays.filter((overlay) => overlay.code.startsWith('event:'));
  const indicatorOverlays = overlays.filter((overlay) => !overlay.code.startsWith('event:'));
  const volumeLabel = isCompact ? 'Объём' : 'Продажи, л';
  const priceLabel = isCompact ? 'Цена' : 'Розничная цена, руб';
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: item.date,
      yAxis: points.find((point) => point.date === item.date)?.volume_liters ?? null,
      value: item.label,
    }));

  const indicatorSeries = indicatorOverlays.map((overlay, index) => {
    const overlayLabel = isCompact ? `OV${index + 1}` : overlay.label;
    const valuesByLabel = new Map(
      (overlay.points ?? [])
        .filter((point) => point.date)
        .map((point) => [point.date as string, point.value ?? null]),
    );
    return {
      name: overlayLabel,
      type: 'line',
      yAxisIndex: 1,
      data: timeline.map((day) => valuesByLabel.get(day) ?? null),
      lineStyle: { type: 'dashed', width: 1.5 },
      symbol: 'none',
    };
  });
  const eventBands = eventOverlays
    .map((overlay, index) => {
      const pointsWithDate = (overlay.points ?? []).filter((point) => Boolean(point.date));
      if (pointsWithDate.length === 0) {
        return null;
      }
      const startDate = pointsWithDate[0]?.date as string;
      const endDate = pointsWithDate[pointsWithDate.length - 1]?.date as string;
      return [
        {
          name: isCompact ? `EV${index + 1}` : overlay.label,
          xAxis: startDate,
          itemStyle: { color: 'rgba(14, 116, 144, 0.08)' },
        },
        {
          xAxis: endDate,
        },
      ];
    })
    .filter((item): item is [{ name: string; xAxis: string; itemStyle: { color: string } }, { xAxis: string }] => Boolean(item));
  const eventMarkers = eventOverlays
    .map((overlay) => {
      const firstPoint = (overlay.points ?? []).find((item) => item.date);
      if (!firstPoint?.date) {
        return null;
      }
      return {
        name: isCompact ? 'EV' : overlay.label,
        xAxis: firstPoint.date,
        yAxis: points.find((point) => point.date === firstPoint.date)?.volume_liters ?? null,
        value: isCompact ? 'EV' : overlay.label,
      };
    })
    .filter((item): item is { name: string; xAxis: string; yAxis: number | null; value: string } => Boolean(item));
  const overlaySummary = overlays
    .map((overlay, index) => {
      const datedPoints = (overlay.points ?? []).filter((item) => item.date);
      const lastPoint = datedPoints.length > 0 ? datedPoints[datedPoints.length - 1] : undefined;
      const lastDate = lastPoint?.date ? formatDateLabel(lastPoint.date) : 'n/a';
      const shortLabel = isCompact ? (overlay.code.startsWith('event:') ? `EV${index + 1}` : `OV${index + 1}`) : overlay.label;
      return `${shortLabel}: ${overlay.provider_mode ?? 'n/a'} · ${lastDate}`;
    });

  const option = {
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number | null) => (typeof value === 'number' ? String(value) : 'n/a'),
    },
    legend: {
      data: [volumeLabel, priceLabel, ...indicatorSeries.map((item) => item.name)],
      ...(isCompact
        ? { selected: Object.fromEntries(indicatorSeries.map((item) => [item.name, false])) }
        : {}),
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
      data: timeline,
      axisLabel: {
        hideOverlap: true,
        fontSize: isCompact ? 10 : 12,
        formatter: (value: string) => formatDateLabel(value),
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
        markArea: eventBands.length > 0 ? { data: eventBands } : undefined,
        markPoint: annotationPoints.length > 0 || eventMarkers.length > 0
          ? { data: [...annotationPoints, ...eventMarkers] }
          : undefined,
      },
      {
        name: priceLabel,
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: points.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#9b6a00' },
      },
      ...indicatorSeries,
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
      {overlaySummary.length > 0 ? (
        <Typography variant="caption" color="text.secondary">
          {overlaySummary.join(' | ')}
        </Typography>
      ) : null}
      <ReactECharts option={option} style={{ height: isCompact ? 264 : 320 }} />
    </ChartCard>
  );
}

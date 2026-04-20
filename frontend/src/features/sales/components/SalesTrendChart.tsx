import ReactECharts from 'echarts-for-react';
import { Stack, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { ChartCard } from '../../../components/common';
import {
  FreshnessBadgeGroup,
  SourceModeBadge,
  type DataState,
} from '../../../components/common';
import type {
  ChartAnnotation,
  DataProviderMode,
  FreshnessStatus,
  ReferenceOverlay,
} from '../../../lib/api/common.types';
import type { SalesSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: SalesSeriesPoint[];
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
  state?: DataState;
  dataFreshness?: FreshnessStatus | null;
  providerMode?: DataProviderMode | null;
  emptyTitle?: string;
  emptyDescription?: string;
  degradedTitle?: string;
  degradedDescription?: string;
  onRetry?: () => void;
  actionLabel?: string;
  onAction?: () => void;
};

export function SalesTrendChart({
  series,
  annotations = [],
  overlays = [],
  state = 'ready',
  dataFreshness = null,
  providerMode = null,
  emptyTitle,
  emptyDescription,
  degradedTitle,
  degradedDescription,
  onRetry,
  actionLabel,
  onAction,
}: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));
  const formatDateLabel = (value: string) =>
    new Date(value).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: isCompact ? 'numeric' : '2-digit',
    });
  const timeline = series.map((item) => item.period_start);
  const eventOverlays = overlays.filter((overlay) => overlay.code.startsWith('event:'));
  const indicatorOverlays = overlays.filter((overlay) => !overlay.code.startsWith('event:'));
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: item.date,
      yAxis: series.find((point) => point.period_start === item.date)?.volume_liters ?? null,
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
        yAxis: series.find((point) => point.period_start === firstPoint.date)?.volume_liters ?? null,
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
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['Продажи, л', 'Розничная цена, руб', ...indicatorSeries.map((item) => item.name)],
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
        name: 'Продажи, л',
        type: 'bar',
        yAxisIndex: 0,
        data: series.map((item) => item.volume_liters),
        itemStyle: { color: '#0a4e8a' },
        markArea: eventBands.length > 0 ? { data: eventBands } : undefined,
        markPoint: annotationPoints.length > 0 || eventMarkers.length > 0
          ? { data: [...annotationPoints, ...eventMarkers] }
          : undefined,
      },
      {
        name: 'Розничная цена, руб',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: series.map((item) => item.avg_retail_price_rub),
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
      degradedTitle={degradedTitle}
      degradedDescription={degradedDescription}
      onRetry={onRetry}
      actionLabel={actionLabel}
      onAction={onAction}
      badgeSlot={(
        <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={null}
            newsFreshness={null}
            showFallback={false}
            compact={isCompact}
          />
          <SourceModeBadge
            mode={providerMode}
            title="Indicators"
            compactTitle="Ind"
            showFallback={false}
            compact={isCompact}
          />
        </Stack>
      )}
    >
      {overlaySummary.length > 0 ? (
        <Stack sx={{ px: 1, pt: 0.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: isCompact ? '0.68rem' : '0.74rem' }}>
            {overlaySummary.join(' | ')}
          </Typography>
        </Stack>
      ) : null}
      <ReactECharts option={option} style={{ height: isCompact ? 264 : 320 }} />
    </ChartCard>
  );
}

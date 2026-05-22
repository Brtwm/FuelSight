import ReactECharts from 'echarts-for-react';
import { Stack } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { ChartCard } from '../../../components/common';
import {
  FreshnessBadgeGroup,
  SourceModeBadge,
  type DataState,
} from '../../../components/common';
import { chartPalette } from '../../../theme/theme';
import {
  buildAxisTooltip,
  buildCategoryAxis,
  buildChartGrid,
  buildDataZoom,
  buildLegend,
  buildValueAxis,
  formatLiters,
  formatRub,
  formatTooltipDate,
  getResponsiveChartHeight,
  renderTooltip,
  type ChartTooltipParam,
} from '../../../lib/charts/chartOptions';
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
    const overlayLabel = isCompact ? `Инд ${index + 1}` : overlay.label;
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
      lineStyle: { type: 'dashed' as const, width: 1.5, color: chartPalette.series[index + 2] ?? chartPalette.accent },
      itemStyle: { color: chartPalette.series[index + 2] ?? chartPalette.accent },
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
          itemStyle: { color: 'rgba(56, 213, 255, 0.05)' },
        },
        { xAxis: endDate },
      ];
    })
    .filter((item): item is [{ name: string; xAxis: string; itemStyle: { color: string } }, { xAxis: string }] => Boolean(item));

  const option = {
    tooltip: buildAxisTooltip(
      (params: ChartTooltipParam[]) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const dateLabel = formatTooltipDate(params[0].axisValueLabel);
        const lines = params
          .filter((p) => p.value != null)
          .map((p) => {
            const formatted = p.seriesName.includes('цена') || p.seriesName.includes('Цена')
              ? formatRub(Number(p.value))
              : formatLiters(Number(p.value));
            return `${p.marker} ${p.seriesName}: <b>${formatted}</b>`;
          });
        return renderTooltip(dateLabel, lines);
      },
    ),
    legend: buildLegend(
      ['Продажи, л', 'Розничная цена, ₽', ...indicatorSeries.map((item) => item.name)],
      isCompact,
      indicatorSeries.map((item) => item.name),
    ),
    grid: buildChartGrid(isCompact),
    dataZoom: buildDataZoom(isCompact),
    xAxis: buildCategoryAxis(timeline, isCompact),
    yAxis: [
      buildValueAxis('Литры'),
      buildValueAxis('Цена', false, 'right'),
    ],
    series: [
      {
        name: 'Продажи, л',
        type: 'bar',
        yAxisIndex: 0,
        data: series.map((item) => item.volume_liters),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: chartPalette.primary },
              { offset: 1, color: 'rgba(56, 213, 255, 0.3)' },
            ],
          },
          borderRadius: [3, 3, 0, 0],
        },
        markArea: eventBands.length > 0 ? { data: eventBands } : undefined,
        markPoint: annotationPoints.length > 0
          ? { data: annotationPoints }
          : undefined,
      },
      {
        name: 'Розничная цена, ₽',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: series.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: chartPalette.warning, width: 2 },
        itemStyle: { color: chartPalette.warning },
        areaStyle: { color: `rgba(245, 158, 11, ${chartPalette.areaOpacity})` },
        symbol: 'none',
      },
      ...indicatorSeries,
    ],
    animation: true,
    animationDuration: 600,
    animationEasing: 'cubicOut',
  };

  return (
    <ChartCard
      title="Динамика реализации"
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
            title="Индикаторы"
            compactTitle="Инд"
            showFallback={false}
            compact={isCompact}
          />
        </Stack>
      )}
    >
      <ReactECharts option={option} style={{ height: getResponsiveChartHeight(isCompact) }} />
    </ChartCard>
  );
}

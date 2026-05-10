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
  const timeline = points.map((item) => item.date);
  const eventOverlays = overlays.filter((overlay) => overlay.code.startsWith('event:'));
  const indicatorOverlays = overlays.filter((overlay) => !overlay.code.startsWith('event:'));
  const volumeLabel = isCompact ? 'Объём' : 'Продажи, л';
  const priceLabel = isCompact ? 'Цена' : 'Розничная цена, ₽';
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: item.date,
      yAxis: points.find((point) => point.date === item.date)?.volume_liters ?? null,
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
        {
          xAxis: endDate,
        },
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
      [volumeLabel, priceLabel, ...indicatorSeries.map((item) => item.name)],
      isCompact,
      indicatorSeries.map((item) => item.name),
    ),
    grid: buildChartGrid(isCompact),
    dataZoom: buildDataZoom(isCompact, 'rgba(59,130,246,0.12)'),
    xAxis: buildCategoryAxis(timeline, isCompact),
    yAxis: [
      buildValueAxis('Литры'),
      buildValueAxis('Цена', false, 'right'),
    ],
    series: [
      {
        name: volumeLabel,
        type: 'bar',
        yAxisIndex: 0,
        data: points.map((item) => item.volume_liters),
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
        name: priceLabel,
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: points.map((item) => item.avg_retail_price_rub),
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
          <SourceModeBadge mode={providerMode} title="Индикаторы" showFallback={false} />
        </Stack>
      )}
      summarySlot={isCompact ? (
        <Typography variant="body2" color="text.secondary">
          Ключевой сигнал: сравните объём спроса и розничную цену, дополнительные индикаторы доступны через легенду.
        </Typography>
      ) : undefined}
    >
      <ReactECharts option={option} style={{ height: getResponsiveChartHeight(isCompact) }} />
    </ChartCard>
  );
}

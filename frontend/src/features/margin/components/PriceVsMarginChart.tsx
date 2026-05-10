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
  formatChartNumber,
  formatRub,
  formatRubPerLiter,
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
import type { MarginSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: MarginSeriesPoint[];
  thresholdRubPerLiter: number;
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
  highlightDate?: string | null;
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

export function PriceVsMarginChart({
  series,
  thresholdRubPerLiter,
  annotations = [],
  overlays = [],
  highlightDate,
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
  const highlightedIndex = highlightDate
    ? series.findIndex((item) => item.period_start === highlightDate)
    : -1;
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: item.date,
      yAxis: series.find((point) => point.period_start === item.date)?.gross_margin_rub_per_liter ?? null,
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
      yAxisIndex: 0,
      data: timeline.map((day) => valuesByLabel.get(day) ?? null),
      lineStyle: { type: 'dashed' as const, width: 1.2, color: chartPalette.series[index + 3] ?? chartPalette.accent },
      itemStyle: { color: chartPalette.series[index + 3] ?? chartPalette.accent },
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

  // Gradient for margin bars: green for healthy, red tint below threshold
  const marginBarData = series.map((item) => {
    const marginValue = item.gross_margin_rub_per_liter;
    return {
      value: marginValue,
      itemStyle: {
        color: marginValue != null && marginValue < thresholdRubPerLiter
          ? {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: chartPalette.error },
                { offset: 1, color: 'rgba(239, 68, 68, 0.3)' },
              ],
            }
          : {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: chartPalette.success },
                { offset: 1, color: 'rgba(16, 185, 129, 0.3)' },
              ],
            },
        borderRadius: [3, 3, 0, 0],
      },
    };
  });

  const option = {
    tooltip: buildAxisTooltip(
      (params: ChartTooltipParam[]) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const dateLabel = formatTooltipDate(params[0].axisValueLabel);
        const lines = params
          .filter((p) => p.value != null)
          .map((p) => {
            const value = Number(p.value);
            const formatted = p.seriesName.includes('Маржа')
              ? formatRubPerLiter(value)
              : p.seriesName.includes('цена')
                ? formatRub(value)
                : formatChartNumber(value, 2);
            return `${p.marker} ${p.seriesName}: <b>${formatted}</b>`;
          });
        return renderTooltip(dateLabel, lines);
      },
    ),
    legend: buildLegend(
      [
        'Закупочная цена',
        'Розничная цена',
        'Маржа, ₽/л',
        ...indicatorSeries.map((item) => item.name),
      ],
      isCompact,
      indicatorSeries.map((item) => item.name),
    ),
    grid: buildChartGrid(isCompact),
    dataZoom: buildDataZoom(isCompact),
    xAxis: buildCategoryAxis(timeline, isCompact),
    yAxis: [
      buildValueAxis('Цена, ₽', true, 'left'),
      buildValueAxis('Маржа, ₽/л', false, 'right'),
    ],
    series: [
      {
        name: 'Закупочная цена',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: series.map((item) => item.avg_purchase_price_rub),
        lineStyle: { color: chartPalette.warning, width: 2 },
        itemStyle: { color: chartPalette.warning },
        symbol: 'none',
      },
      {
        name: 'Розничная цена',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: series.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: chartPalette.primary, width: 2 },
        itemStyle: { color: chartPalette.primary },
        symbol: 'none',
      },
      {
        name: 'Маржа, ₽/л',
        type: 'bar',
        yAxisIndex: 1,
        data: marginBarData,
        markLine: {
          symbol: 'none',
          lineStyle: { type: 'dashed', color: chartPalette.error, width: 2 },
          label: {
            color: chartPalette.error,
            formatter: `Порог ${thresholdRubPerLiter.toFixed(2)} ₽`,
            fontSize: 11,
            backgroundColor: 'rgba(5, 7, 11, 0.78)',
            borderColor: 'rgba(255, 93, 93, 0.28)',
            borderWidth: 1,
            borderRadius: 4,
            padding: [2, 4],
          },
          data: [{ yAxis: thresholdRubPerLiter, name: `Порог` }],
        },
        markArea: {
          itemStyle: { color: 'rgba(239, 68, 68, 0.04)' },
          data: [
            [{ yAxis: 0 }, { yAxis: thresholdRubPerLiter }],
            ...eventBands,
          ],
        },
        markPoint:
          highlightedIndex >= 0
            ? {
                data: [
                  {
                    coord: [
                      timeline[highlightedIndex],
                      series[highlightedIndex]?.gross_margin_rub_per_liter ?? 0,
                    ],
                    value: 'выбрано',
                  },
                ],
              }
            : annotationPoints.length > 0
              ? { data: annotationPoints }
              : undefined,
      },
      ...indicatorSeries,
    ],
    animation: true,
    animationDuration: 600,
    animationEasing: 'cubicOut',
  };

  return (
    <ChartCard
      title="Закупочная vs розничная цена + маржа"
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

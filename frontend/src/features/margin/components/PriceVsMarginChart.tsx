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
  const formatDateLabel = (value: string) =>
    new Date(value).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: isCompact ? 'numeric' : '2-digit',
    });
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
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartPalette.tooltipBg,
      borderColor: chartPalette.tooltipBorder,
      textStyle: { color: '#e2e8f0', fontSize: 13 },
      formatter: (params: Array<{ seriesName: string; value: number | null; marker: string; axisValueLabel: string }>) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const dateLabel = new Date(params[0].axisValueLabel).toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: 'long',
          year: 'numeric',
        });
        const lines = params
          .filter((p) => p.value != null)
          .map((p) => {
            const val = Number(p.value).toLocaleString('ru-RU', { maximumFractionDigits: 2 });
            const unit = p.seriesName.includes('Маржа') ? '₽/л' : p.seriesName.includes('цена') ? '₽' : '';
            return `${p.marker} ${p.seriesName}: <b>${val}${unit ? ` ${unit}` : ''}</b>`;
          });
        return `<div style="font-family:'IBM Plex Sans',sans-serif">${dateLabel}<br/>${lines.join('<br/>')}</div>`;
      },
    },
    legend: {
      data: [
        'Закупочная цена',
        'Розничная цена',
        'Маржа, ₽/л',
        ...indicatorSeries.map((item) => item.name),
      ],
      textStyle: { color: chartPalette.axisLabel },
      ...(isCompact
        ? { selected: Object.fromEntries(indicatorSeries.map((item) => [item.name, false])) }
        : {}),
    },
    grid: {
      left: isCompact ? 8 : 24,
      right: isCompact ? 8 : 24,
      top: isCompact ? 38 : 44,
      bottom: isCompact ? 44 : 48,
      containLabel: true,
    },
    dataZoom: isCompact
      ? []
      : [
          {
            type: 'slider',
            height: 20,
            bottom: 4,
            borderColor: 'transparent',
            backgroundColor: 'rgba(255,255,255,0.03)',
            fillerColor: 'rgba(56,213,255,0.14)',
            handleStyle: { color: chartPalette.primary },
            textStyle: { color: chartPalette.axisLabel },
            dataBackground: {
              lineStyle: { color: 'rgba(255,255,255,0.08)' },
              areaStyle: { color: 'rgba(255,255,255,0.04)' },
            },
          },
        ],
    xAxis: {
      type: 'category',
      data: timeline,
      axisLabel: {
        hideOverlap: true,
        fontSize: isCompact ? 10 : 12,
        color: chartPalette.axisLabel,
        formatter: (value: string) => formatDateLabel(value),
      },
      axisLine: { lineStyle: { color: chartPalette.axisLine } },
      splitLine: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: 'Цена, ₽',
        position: 'left',
        nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
        axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
        splitLine: { lineStyle: { color: chartPalette.gridLine } },
      },
      {
        type: 'value',
        name: 'Маржа, ₽/л',
        position: 'right',
        nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
        axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
        splitLine: { show: false },
      },
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
      <ReactECharts option={option} style={{ height: isCompact ? 300 : 400 }} />
    </ChartCard>
  );
}

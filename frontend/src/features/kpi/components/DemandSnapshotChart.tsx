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
          itemStyle: { color: 'rgba(59, 130, 246, 0.06)' },
        },
        {
          xAxis: endDate,
        },
      ];
    })
    .filter((item): item is [{ name: string; xAxis: string; itemStyle: { color: string } }, { xAxis: string }] => Boolean(item));

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
            const formatted = p.seriesName.includes('цена') || p.seriesName.includes('Цена')
              ? `${Number(p.value).toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽`
              : `${Number(p.value).toLocaleString('ru-RU', { maximumFractionDigits: 0 })} л`;
            return `${p.marker} ${p.seriesName}: <b>${formatted}</b>`;
          });
        return `<div style="font-family:Inter,sans-serif">${dateLabel}<br/>${lines.join('<br/>')}</div>`;
      },
    },
    legend: {
      data: [volumeLabel, priceLabel, ...indicatorSeries.map((item) => item.name)],
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
            fillerColor: 'rgba(59,130,246,0.12)',
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
        name: 'Литры',
        nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
        axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
        splitLine: { lineStyle: { color: chartPalette.gridLine } },
      },
      {
        type: 'value',
        name: 'Цена',
        position: 'right',
        nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
        axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
        splitLine: { show: false },
      },
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
              { offset: 1, color: 'rgba(59, 130, 246, 0.3)' },
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
    >
      <ReactECharts option={option} style={{ height: isCompact ? 300 : 400 }} />
    </ChartCard>
  );
}

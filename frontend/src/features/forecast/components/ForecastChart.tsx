import { Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import ReactECharts from 'echarts-for-react';
import { chartPalette } from '../../../theme/theme';
import type { ReferenceOverlay } from '../../../lib/api/common.types';
import type { ForecastEventContext, ForecastPoint } from '../../../lib/api/forecast.types';

type Props = {
  basePoints: ForecastPoint[];
  scenarioPoints?: ForecastPoint[] | null;
  overlays?: ReferenceOverlay[];
  eventContext?: ForecastEventContext[];
};

export function ForecastChart({
  basePoints,
  scenarioPoints,
  overlays = [],
  eventContext = [],
}: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));
  const formatDateLabel = (value: string) =>
    new Date(value).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: isCompact ? 'numeric' : '2-digit',
    });
  const timeline = basePoints.map((item) => item.target_date);
  const hasScenario = Boolean(scenarioPoints && scenarioPoints.length > 0);
  const scenarioSeries = scenarioPoints ?? [];
  const indicatorOverlays = overlays.filter((overlay) => !overlay.code.startsWith('event:'));
  const baseLabel = isCompact ? 'Базовый' : 'Базовый прогноз, л';
  const scenarioLabel = isCompact ? 'Сценарий' : 'Сценарный прогноз, л';
  const indicatorSeries = indicatorOverlays.map((overlay, index) => {
    const overlayLabel = isCompact ? `Инд ${index + 1}` : overlay.label;
    const valuesByDate = new Map(
      (overlay.points ?? [])
        .filter((point) => point.date)
        .map((point) => [point.date as string, point.value ?? null]),
    );
    return {
      name: overlayLabel,
      type: 'line',
      yAxisIndex: 1,
      data: timeline.map((day) => valuesByDate.get(day) ?? null),
      lineStyle: { type: 'dashed' as const, width: 1.2, color: chartPalette.series[index + 3] ?? chartPalette.accent },
      itemStyle: { color: chartPalette.series[index + 3] ?? chartPalette.accent },
      symbol: 'none',
    };
  });
  const forecastByDate = new Map(basePoints.map((point) => [point.target_date, point.y_hat]));
  const eventBands = eventContext
    .map((event, index) => {
      const inWindow = timeline.some((day) => day >= event.start_date && day <= event.end_date);
      if (!inWindow) {
        return null;
      }
      return [
        {
          name: isCompact ? `EV${index + 1}` : event.title,
          xAxis: event.start_date,
          itemStyle: { color: 'rgba(56, 213, 255, 0.05)' },
        },
        { xAxis: event.end_date },
      ];
    })
    .filter((item): item is [{ name: string; xAxis: string; itemStyle: { color: string } }, { xAxis: string }] => Boolean(item));
  const eventMarkers = eventContext
    .map((event) => {
      const target = timeline.find((day) => day >= event.start_date && day <= event.end_date);
      if (!target) {
        return null;
      }
      return {
        name: isCompact ? 'Событие' : event.title,
        xAxis: target,
        yAxis: forecastByDate.get(target) ?? null,
        value: isCompact ? 'событие' : event.title,
        symbolSize: isCompact ? 28 : 34,
        label: {
          formatter: isCompact ? 'Событие' : event.title,
          position: 'top' as const,
          distance: 8,
          color: chartPalette.axisLabel,
          fontSize: isCompact ? 10 : 11,
        },
      };
    })
    .filter((item): item is {
      name: string;
      xAxis: string;
      yAxis: number | null;
      value: string;
      symbolSize: number;
      label: { formatter: string; position: 'top'; distance: number; color: string; fontSize: number };
    } => Boolean(item));

  // Legend items
  const legendData = [baseLabel];
  if (hasScenario) {
    legendData.push(scenarioLabel);
  }
  legendData.push('Доверительный интервал');
  legendData.push(...indicatorSeries.map((item) => item.name));

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartPalette.tooltipBg,
      borderColor: chartPalette.tooltipBorder,
      textStyle: { color: '#e2e8f0', fontSize: 13 },
      formatter: (params: Array<{ seriesName: string; value: number | null; marker: string; axisValueLabel: string; dataIndex: number }>) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const dateLabel = new Date(params[0].axisValueLabel).toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: 'long',
          year: 'numeric',
        });
        const lines = params
          .filter((p) => p.value != null && !p.seriesName.includes('_lo_band') && !p.seriesName.includes('_hi_band'))
          .map((p) => {
            if (p.seriesName === 'Доверительный интервал') {
              const point = basePoints[p.dataIndex];
              if (point?.y_lo == null || point.y_hi == null) {
                return null;
              }
              const lo = Number(point.y_lo).toLocaleString('ru-RU', { maximumFractionDigits: 0 });
              const hi = Number(point.y_hi).toLocaleString('ru-RU', { maximumFractionDigits: 0 });
              return `${p.marker} ${p.seriesName}: <b>${lo}-${hi} л</b>`;
            }
            const val = Number(p.value).toLocaleString('ru-RU', { maximumFractionDigits: 0 });
            return `${p.marker} ${p.seriesName}: <b>${val} л</b>`;
          })
          .filter((line): line is string => Boolean(line));
        return `<div style="font-family:'IBM Plex Sans',sans-serif">${dateLabel}<br/>${lines.join('<br/>')}</div>`;
      },
    },
    legend: {
      data: legendData,
      textStyle: { color: chartPalette.axisLabel },
      ...(isCompact
        ? {
            selected: {
              'Доверительный интервал': false,
              ...Object.fromEntries(indicatorSeries.map((item) => [item.name, false])),
            },
          }
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
        name: 'Литры',
        nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
        axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
        splitLine: { lineStyle: { color: chartPalette.gridLine } },
      },
      {
        type: 'value',
        name: 'Индикаторы',
        position: 'right',
        nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
        axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
        splitLine: { show: false },
      },
    ],
    series: [
      // Confidence interval as stacked area band
      {
        name: '_lo_band',
        type: 'line',
        yAxisIndex: 0,
        data: basePoints.map((item) => item.y_lo),
        lineStyle: { opacity: 0 },
        stack: 'confidence',
        symbol: 'none',
        silent: true,
        tooltip: { show: false },
      },
      {
        name: 'Доверительный интервал',
        type: 'line',
        yAxisIndex: 0,
        data: basePoints.map((item, i) => {
          const lo = basePoints[i].y_lo;
          const hi = item.y_hi;
          return (lo != null && hi != null) ? hi - lo : null;
        }),
        lineStyle: { opacity: 0 },
        stack: 'confidence',
        symbol: 'none',
        areaStyle: {
          color: 'rgba(56, 213, 255, 0.13)',
        },
      },
      // Main forecast line
      {
        name: baseLabel,
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: basePoints.map((item) => item.y_hat),
        lineStyle: { color: chartPalette.primary, width: 2.5 },
        itemStyle: { color: chartPalette.primary },
        symbol: 'circle',
        symbolSize: 4,
        markArea: eventBands.length > 0 ? { data: eventBands } : undefined,
        markPoint: eventMarkers.length > 0 ? { data: eventMarkers } : undefined,
      },
      // Scenario line (dashed)
      ...(hasScenario
        ? [
            {
              name: scenarioLabel,
              type: 'line',
              smooth: true,
              yAxisIndex: 0,
              data: scenarioSeries.map((item) => item.y_hat),
              lineStyle: { color: chartPalette.secondary, width: 2, type: 'dashed' as const },
              itemStyle: { color: chartPalette.secondary },
              symbol: 'diamond',
              symbolSize: 5,
            },
          ]
        : []),
      ...indicatorSeries,
    ],
    animation: true,
    animationDuration: 600,
    animationEasing: 'cubicOut',
  };

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {isCompact
          ? 'Базовый и сценарный прогнозы. Полосой обозначен доверительный интервал.'
          : 'Базовый прогноз отображается вместе со сценарным, доверительный интервал — полосой.'}
      </Typography>
      <ReactECharts option={option} style={{ height: isCompact ? 300 : 400 }} />
    </>
  );
}

import { Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import ReactECharts from 'echarts-for-react';
import type { ProviderMode, ReferenceOverlay } from '../../../lib/api/common.types';
import type { ForecastEventContext, ForecastPoint } from '../../../lib/api/forecast.types';

type Props = {
  basePoints: ForecastPoint[];
  scenarioPoints?: ForecastPoint[] | null;
  overlays?: ReferenceOverlay[];
  eventContext?: ForecastEventContext[];
  providerMode?: ProviderMode | null;
  manifestRunDate?: string | null;
};

export function ForecastChart({
  basePoints,
  scenarioPoints,
  overlays = [],
  eventContext = [],
  providerMode = null,
  manifestRunDate = null,
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
  const baseLabel = isCompact ? 'Base' : 'Base прогноз, л';
  const scenarioLabel = isCompact ? 'Scn' : 'Scenario прогноз, л';
  const lowLabel = isCompact ? 'Lo' : 'Нижняя граница';
  const highLabel = isCompact ? 'Hi' : 'Верхняя граница';
  const indicatorSeries = indicatorOverlays.map((overlay, index) => {
    const overlayLabel = isCompact ? `OV${index + 1}` : overlay.label;
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
      lineStyle: { type: 'dashed', width: 1.2 },
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
          itemStyle: { color: 'rgba(14, 116, 144, 0.08)' },
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
        name: isCompact ? 'EV' : event.title,
        xAxis: target,
        yAxis: forecastByDate.get(target) ?? null,
        value: isCompact ? 'EV' : event.title,
      };
    })
    .filter((item): item is { name: string; xAxis: string; yAxis: number | null; value: string } => Boolean(item));
  const overlaySummary = [
    ...indicatorOverlays.map((overlay, index) => {
      const datedPoints = (overlay.points ?? []).filter((item) => item.date);
      const lastPoint = datedPoints.length > 0 ? datedPoints[datedPoints.length - 1] : undefined;
      const lastDate = lastPoint?.date ? formatDateLabel(lastPoint.date) : 'n/a';
      const shortLabel = isCompact ? `OV${index + 1}` : overlay.label;
      return `${shortLabel}: ${overlay.provider_mode ?? 'n/a'} · ${lastDate}`;
    }),
    ...eventContext.slice(0, 3).map((event) => `${event.title} (${formatDateLabel(event.start_date)}-${formatDateLabel(event.end_date)})`),
  ];
  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: hasScenario
        ? [baseLabel, scenarioLabel, lowLabel, highLabel, ...indicatorSeries.map((item) => item.name)]
        : [baseLabel, lowLabel, highLabel, ...indicatorSeries.map((item) => item.name)],
      ...(isCompact
        ? {
          selected: {
            [lowLabel]: false,
            [highLabel]: false,
            ...Object.fromEntries(indicatorSeries.map((item) => [item.name, false])),
          },
        }
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
      { type: 'value', name: 'Индикаторы', position: 'right' },
    ],
    series: [
      {
        name: baseLabel,
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: basePoints.map((item) => item.y_hat),
        lineStyle: { color: '#0a4e8a', width: 2 },
        itemStyle: { color: '#0a4e8a' },
        markArea: eventBands.length > 0 ? { data: eventBands } : undefined,
        markPoint: eventMarkers.length > 0 ? { data: eventMarkers } : undefined,
      },
      ...(hasScenario
        ? [
            {
              name: scenarioLabel,
              type: 'line',
              smooth: true,
              yAxisIndex: 0,
              data: scenarioSeries.map((item) => item.y_hat),
              lineStyle: { color: '#0e7490', width: 2 },
              itemStyle: { color: '#0e7490' },
            },
          ]
        : []),
      {
        name: lowLabel,
        type: 'line',
        yAxisIndex: 0,
        data: basePoints.map((item) => item.y_lo),
        lineStyle: { color: '#b35f00', type: 'dashed' },
      },
      {
        name: highLabel,
        type: 'line',
        yAxisIndex: 0,
        data: basePoints.map((item) => item.y_hi),
        lineStyle: { color: '#2e7d32', type: 'dashed' },
      },
      ...indicatorSeries,
    ],
  };

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {isCompact
          ? 'Сначала сравните base/scenario, затем при необходимости включите границы через legend.'
          : 'Base и scenario отображаются вместе, чтобы сразу видеть влияние ценового сценария.'}
      </Typography>
      {overlaySummary.length > 0 ? (
        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          {overlaySummary.join(' | ')}
        </Typography>
      ) : null}
      {(providerMode || manifestRunDate) ? (
        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          mode: {providerMode ?? 'n/a'}
          {manifestRunDate ? ` · контекст: ${formatDateLabel(manifestRunDate)}` : ''}
        </Typography>
      ) : null}
      <ReactECharts option={option} style={{ height: isCompact ? 264 : 320 }} />
    </>
  );
}

import { Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import ReactECharts from 'echarts-for-react';
import type { ForecastPoint } from '../../../lib/api/forecast.types';

type Props = {
  basePoints: ForecastPoint[];
  scenarioPoints?: ForecastPoint[] | null;
};

export function ForecastChart({ basePoints, scenarioPoints }: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));
  const labels = basePoints.map((item) =>
    new Date(item.target_date).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: isCompact ? 'numeric' : '2-digit',
    }),
  );
  const hasScenario = Boolean(scenarioPoints && scenarioPoints.length > 0);
  const scenarioSeries = scenarioPoints ?? [];
  const baseLabel = isCompact ? 'Base' : 'Base прогноз, л';
  const scenarioLabel = isCompact ? 'Scn' : 'Scenario прогноз, л';
  const lowLabel = isCompact ? 'Lo' : 'Нижняя граница';
  const highLabel = isCompact ? 'Hi' : 'Верхняя граница';
  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: hasScenario
        ? [baseLabel, scenarioLabel, lowLabel, highLabel]
        : [baseLabel, lowLabel, highLabel],
      selected: isCompact
        ? {
            [lowLabel]: false,
            [highLabel]: false,
          }
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
    yAxis: [{ type: 'value', name: 'Литры' }],
    series: [
      {
        name: baseLabel,
        type: 'line',
        smooth: true,
        data: basePoints.map((item) => item.y_hat),
        lineStyle: { color: '#0a4e8a', width: 2 },
        itemStyle: { color: '#0a4e8a' },
      },
      ...(hasScenario
        ? [
            {
              name: scenarioLabel,
              type: 'line',
              smooth: true,
              data: scenarioSeries.map((item) => item.y_hat),
              lineStyle: { color: '#0e7490', width: 2 },
              itemStyle: { color: '#0e7490' },
            },
          ]
        : []),
      {
        name: lowLabel,
        type: 'line',
        data: basePoints.map((item) => item.y_lo),
        lineStyle: { color: '#b35f00', type: 'dashed' },
      },
      {
        name: highLabel,
        type: 'line',
        data: basePoints.map((item) => item.y_hi),
        lineStyle: { color: '#2e7d32', type: 'dashed' },
      },
    ],
  };

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {isCompact
          ? 'Сначала сравните base/scenario, затем при необходимости включите границы через legend.'
          : 'Base и scenario отображаются вместе, чтобы сразу видеть влияние ценового сценария.'}
      </Typography>
      <ReactECharts option={option} style={{ height: isCompact ? 264 : 320 }} />
    </>
  );
}

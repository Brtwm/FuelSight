import { Typography } from '@mui/material';
import ReactECharts from 'echarts-for-react';
import type { ForecastPoint } from '../../../lib/api/forecast.types';

type Props = {
  basePoints: ForecastPoint[];
  scenarioPoints?: ForecastPoint[] | null;
};

export function ForecastChart({ basePoints, scenarioPoints }: Props) {
  const labels = basePoints.map((item) => new Date(item.target_date).toLocaleDateString('ru-RU'));
  const hasScenario = Boolean(scenarioPoints && scenarioPoints.length > 0);
  const scenarioSeries = scenarioPoints ?? [];
  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: hasScenario
        ? ['Base прогноз, л', 'Scenario прогноз, л', 'Нижняя граница', 'Верхняя граница']
        : ['Base прогноз, л', 'Нижняя граница', 'Верхняя граница'],
    },
    grid: { left: 24, right: 24, top: 40, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: [{ type: 'value', name: 'Литры' }],
    series: [
      {
        name: 'Base прогноз, л',
        type: 'line',
        smooth: true,
        data: basePoints.map((item) => item.y_hat),
        lineStyle: { color: '#0a4e8a', width: 2 },
        itemStyle: { color: '#0a4e8a' },
      },
      ...(hasScenario
        ? [
            {
              name: 'Scenario прогноз, л',
              type: 'line',
              smooth: true,
              data: scenarioSeries.map((item) => item.y_hat),
              lineStyle: { color: '#0e7490', width: 2 },
              itemStyle: { color: '#0e7490' },
            },
          ]
        : []),
      {
        name: 'Нижняя граница',
        type: 'line',
        data: basePoints.map((item) => item.y_lo),
        lineStyle: { color: '#b35f00', type: 'dashed' },
      },
      {
        name: 'Верхняя граница',
        type: 'line',
        data: basePoints.map((item) => item.y_hi),
        lineStyle: { color: '#2e7d32', type: 'dashed' },
      },
    ],
  };

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Base и scenario отображаются вместе, чтобы сразу видеть влияние ценового сценария.
      </Typography>
      <ReactECharts option={option} style={{ height: 320 }} />
    </>
  );
}

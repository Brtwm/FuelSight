import { Card, CardContent, Typography } from '@mui/material';
import ReactECharts from 'echarts-for-react';
import type { ForecastPoint } from '../../../lib/api/forecast.types';

type Props = {
  points: ForecastPoint[];
};

export function ForecastChart({ points }: Props) {
  const labels = points.map((item) => new Date(item.target_date).toLocaleDateString('ru-RU'));
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Прогноз, л', 'Нижняя граница', 'Верхняя граница'] },
    grid: { left: 24, right: 24, top: 40, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: [{ type: 'value', name: 'Литры' }],
    series: [
      {
        name: 'Прогноз, л',
        type: 'line',
        smooth: true,
        data: points.map((item) => item.y_hat),
        lineStyle: { color: '#0a4e8a', width: 2 },
      },
      {
        name: 'Нижняя граница',
        type: 'line',
        data: points.map((item) => item.y_lo),
        lineStyle: { color: '#b35f00', type: 'dashed' },
      },
      {
        name: 'Верхняя граница',
        type: 'line',
        data: points.map((item) => item.y_hi),
        lineStyle: { color: '#2e7d32', type: 'dashed' },
      },
    ],
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Прогноз спроса и интервалы
        </Typography>
        <ReactECharts option={option} style={{ height: 320 }} />
      </CardContent>
    </Card>
  );
}


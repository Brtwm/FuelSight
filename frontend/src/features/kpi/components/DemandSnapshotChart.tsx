import { Card, CardContent, Typography } from '@mui/material';
import ReactECharts from 'echarts-for-react';
import type { KpiSnapshotPoint } from '../../../lib/api/kpi.types';

type Props = {
  points: KpiSnapshotPoint[];
};

export function DemandSnapshotChart({ points }: Props) {
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Продажи, л', 'Розничная цена, руб'] },
    grid: { left: 24, right: 24, top: 40, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: points.map((item) => new Date(item.date).toLocaleDateString('ru-RU')),
    },
    yAxis: [
      { type: 'value', name: 'Литры' },
      { type: 'value', name: 'Цена', position: 'right' },
    ],
    series: [
      {
        name: 'Продажи, л',
        type: 'bar',
        yAxisIndex: 0,
        data: points.map((item) => item.volume_liters),
        itemStyle: { color: '#0a4e8a' },
      },
      {
        name: 'Розничная цена, руб',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: points.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#9b6a00' },
      },
    ],
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Динамика спроса
        </Typography>
        <ReactECharts option={option} style={{ height: 320 }} />
      </CardContent>
    </Card>
  );
}


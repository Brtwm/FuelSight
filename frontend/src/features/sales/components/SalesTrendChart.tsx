import ReactECharts from 'echarts-for-react';
import { ChartCard } from '../../../components/common';
import type { SalesSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: SalesSeriesPoint[];
};

export function SalesTrendChart({ series }: Props) {
  const labels = series.map((item) => new Date(item.period_start).toLocaleDateString('ru-RU'));
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Продажи, л', 'Розничная цена, руб'] },
    grid: { left: 24, right: 24, top: 40, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
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
        data: series.map((item) => item.volume_liters),
        itemStyle: { color: '#0a4e8a' },
      },
      {
        name: 'Розничная цена, руб',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: series.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#9b6a00' },
      },
    ],
  };

  return (
    <ChartCard title="Динамика спроса" state="ready">
      <ReactECharts option={option} style={{ height: 320 }} />
    </ChartCard>
  );
}

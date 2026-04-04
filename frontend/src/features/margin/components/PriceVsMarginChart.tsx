import { Card, CardContent, Typography } from '@mui/material';
import ReactECharts from 'echarts-for-react';
import type { MarginSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: MarginSeriesPoint[];
  highlightDate?: string | null;
};

export function PriceVsMarginChart({ series, highlightDate }: Props) {
  const labels = series.map((item) => new Date(item.period_start).toLocaleDateString('ru-RU'));
  const highlightedIndex = highlightDate
    ? series.findIndex((item) => item.period_start === highlightDate)
    : -1;

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Закупочная цена', 'Розничная цена', 'Маржа, руб/л'] },
    grid: { left: 24, right: 24, top: 40, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
    },
    yAxis: [
      { type: 'value', name: 'Цена', position: 'left' },
      { type: 'value', name: 'Маржа', position: 'right' },
    ],
    series: [
      {
        name: 'Закупочная цена',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: series.map((item) => item.avg_purchase_price_rub),
        lineStyle: { color: '#b35f00' },
      },
      {
        name: 'Розничная цена',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: series.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#0a4e8a' },
      },
      {
        name: 'Маржа, руб/л',
        type: 'bar',
        yAxisIndex: 1,
        data: series.map((item) => item.gross_margin_rub_per_liter),
        itemStyle: { color: '#2e7d32' },
        markPoint:
          highlightedIndex >= 0
            ? {
                data: [
                  {
                    coord: [
                      labels[highlightedIndex],
                      series[highlightedIndex]?.gross_margin_rub_per_liter ?? 0,
                    ],
                    value: 'selected',
                  },
                ],
              }
            : undefined,
      },
    ],
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Закупочная vs розничная цена + маржа
        </Typography>
        <ReactECharts option={option} style={{ height: 340 }} />
      </CardContent>
    </Card>
  );
}

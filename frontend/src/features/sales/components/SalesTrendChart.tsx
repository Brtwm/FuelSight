import ReactECharts from 'echarts-for-react';
import { ChartCard } from '../../../components/common';
import type { ChartAnnotation, ReferenceOverlay } from '../../../lib/api/common.types';
import type { SalesSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: SalesSeriesPoint[];
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
};

export function SalesTrendChart({ series, annotations = [], overlays = [] }: Props) {
  const labels = series.map((item) => new Date(item.period_start).toLocaleDateString('ru-RU'));
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: new Date(item.date as string).toLocaleDateString('ru-RU'),
      yAxis: series.find((point) => point.period_start === item.date)?.volume_liters ?? null,
      value: item.label,
    }));

  const overlaySeries = overlays.map((overlay) => {
    const valuesByLabel = new Map(
      (overlay.points ?? [])
        .filter((point) => point.date)
        .map((point) => [new Date(point.date as string).toLocaleDateString('ru-RU'), point.value ?? null]),
    );
    return {
      name: overlay.label,
      type: 'line',
      yAxisIndex: 1,
      data: labels.map((label) => valuesByLabel.get(label) ?? null),
      lineStyle: { type: 'dashed', width: 1.5 },
      symbol: 'none',
    };
  });

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Продажи, л', 'Розничная цена, руб', ...overlays.map((item) => item.label)] },
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
        markPoint: annotationPoints.length > 0 ? { data: annotationPoints } : undefined,
      },
      {
        name: 'Розничная цена, руб',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: series.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#9b6a00' },
      },
      ...overlaySeries,
    ],
  };

  return (
    <ChartCard title="Динамика спроса" state="ready">
      <ReactECharts option={option} style={{ height: 320 }} />
    </ChartCard>
  );
}

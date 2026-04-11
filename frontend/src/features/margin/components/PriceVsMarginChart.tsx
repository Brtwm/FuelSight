import ReactECharts from 'echarts-for-react';
import { ChartCard } from '../../../components/common';
import type { ChartAnnotation, ReferenceOverlay } from '../../../lib/api/common.types';
import type { MarginSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: MarginSeriesPoint[];
  thresholdRubPerLiter: number;
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
  highlightDate?: string | null;
};

export function PriceVsMarginChart({
  series,
  thresholdRubPerLiter,
  annotations = [],
  overlays = [],
  highlightDate,
}: Props) {
  const labels = series.map((item) => new Date(item.period_start).toLocaleDateString('ru-RU'));
  const highlightedIndex = highlightDate
    ? series.findIndex((item) => item.period_start === highlightDate)
    : -1;
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: new Date(item.date as string).toLocaleDateString('ru-RU'),
      yAxis: series.find((point) => point.period_start === item.date)?.gross_margin_rub_per_liter ?? null,
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
      yAxisIndex: 0,
      data: labels.map((label) => valuesByLabel.get(label) ?? null),
      lineStyle: { type: 'dashed', width: 1.2 },
      symbol: 'none',
    };
  });

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: [
        'Закупочная цена',
        'Розничная цена',
        'Маржа, руб/л',
        ...overlays.map((item) => item.label),
      ],
    },
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
        markLine: {
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#c62828' },
          data: [{ yAxis: thresholdRubPerLiter, name: `Порог ${thresholdRubPerLiter.toFixed(2)}` }],
        },
        markArea: {
          itemStyle: { color: 'rgba(198, 40, 40, 0.08)' },
          data: [[{ yAxis: 0 }, { yAxis: thresholdRubPerLiter }]],
        },
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
            : annotationPoints.length > 0
              ? { data: annotationPoints }
              : undefined,
      },
      ...overlaySeries,
    ],
  };

  return (
    <ChartCard title="Закупочная vs розничная цена + маржа" state="ready">
      <ReactECharts option={option} style={{ height: 340 }} />
    </ChartCard>
  );
}

import ReactECharts from 'echarts-for-react';
import { Stack } from '@mui/material';
import {
  ChartCard,
  FreshnessBadgeGroup,
  SourceModeBadge,
  type DataState,
} from '../../../components/common';
import type { ChartAnnotation, ReferenceOverlay, FreshnessStatus, ProviderMode } from '../../../lib/api/common.types';
import type { KpiSnapshotPoint } from '../../../lib/api/kpi.types';

type Props = {
  points: KpiSnapshotPoint[];
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
  state?: DataState;
  dataFreshness?: FreshnessStatus | null;
  providerMode?: ProviderMode | null;
  emptyTitle?: string;
  emptyDescription?: string;
  onRetry?: () => void;
};

export function DemandSnapshotChart({
  points,
  annotations = [],
  overlays = [],
  state = 'ready',
  dataFreshness = null,
  providerMode = null,
  emptyTitle,
  emptyDescription,
  onRetry,
}: Props) {
  const labels = points.map((item) => new Date(item.date).toLocaleDateString('ru-RU'));
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: new Date(item.date as string).toLocaleDateString('ru-RU'),
      yAxis: points.find((point) => point.date === item.date)?.volume_liters ?? null,
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
        data: points.map((item) => item.volume_liters),
        itemStyle: { color: '#0a4e8a' },
        markPoint: annotationPoints.length > 0 ? { data: annotationPoints } : undefined,
      },
      {
        name: 'Розничная цена, руб',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: points.map((item) => item.avg_retail_price_rub),
        lineStyle: { color: '#9b6a00' },
      },
      ...overlaySeries,
    ],
  };

  return (
    <ChartCard
      title="Динамика спроса"
      state={state}
      emptyTitle={emptyTitle}
      emptyDescription={emptyDescription}
      onRetry={onRetry}
      badgeSlot={(
        <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={null}
            newsFreshness={null}
            showFallback={false}
          />
          <SourceModeBadge mode={providerMode} title="Indicators" showFallback={false} />
        </Stack>
      )}
    >
      <ReactECharts option={option} style={{ height: 320 }} />
    </ChartCard>
  );
}

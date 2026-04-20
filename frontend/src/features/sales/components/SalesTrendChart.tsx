import ReactECharts from 'echarts-for-react';
import { Stack } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { ChartCard } from '../../../components/common';
import {
  FreshnessBadgeGroup,
  SourceModeBadge,
  type DataState,
} from '../../../components/common';
import type {
  ChartAnnotation,
  DataProviderMode,
  FreshnessStatus,
  ReferenceOverlay,
} from '../../../lib/api/common.types';
import type { SalesSeriesPoint } from '../../../lib/api/analytics.types';

type Props = {
  series: SalesSeriesPoint[];
  annotations?: ChartAnnotation[];
  overlays?: ReferenceOverlay[];
  state?: DataState;
  dataFreshness?: FreshnessStatus | null;
  providerMode?: DataProviderMode | null;
  emptyTitle?: string;
  emptyDescription?: string;
  degradedTitle?: string;
  degradedDescription?: string;
  onRetry?: () => void;
  actionLabel?: string;
  onAction?: () => void;
};

export function SalesTrendChart({
  series,
  annotations = [],
  overlays = [],
  state = 'ready',
  dataFreshness = null,
  providerMode = null,
  emptyTitle,
  emptyDescription,
  degradedTitle,
  degradedDescription,
  onRetry,
  actionLabel,
  onAction,
}: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));
  const formatDateLabel = (value: string) =>
    new Date(value).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: isCompact ? 'numeric' : '2-digit',
    });
  const labels = series.map((item) => formatDateLabel(item.period_start));
  const annotationPoints = annotations
    .filter((item) => item.date)
    .map((item) => ({
      name: item.label,
      xAxis: formatDateLabel(item.date as string),
      yAxis: series.find((point) => point.period_start === item.date)?.volume_liters ?? null,
      value: item.label,
    }));

  const overlaySeries = overlays.map((overlay, index) => {
    const overlayLabel = isCompact ? `OV${index + 1}` : overlay.label;
    const valuesByLabel = new Map(
      (overlay.points ?? [])
        .filter((point) => point.date)
        .map((point) => [formatDateLabel(point.date as string), point.value ?? null]),
    );
    return {
      name: overlayLabel,
      type: 'line',
      yAxisIndex: 1,
      data: labels.map((label) => valuesByLabel.get(label) ?? null),
      lineStyle: { type: 'dashed', width: 1.5 },
      symbol: 'none',
    };
  });

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['Продажи, л', 'Розничная цена, руб', ...overlaySeries.map((item) => item.name)],
      selected: isCompact
        ? Object.fromEntries(overlaySeries.map((item) => [item.name, false]))
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
    <ChartCard
      title="Динамика спроса"
      state={state}
      emptyTitle={emptyTitle}
      emptyDescription={emptyDescription}
      degradedTitle={degradedTitle}
      degradedDescription={degradedDescription}
      onRetry={onRetry}
      actionLabel={actionLabel}
      onAction={onAction}
      badgeSlot={(
        <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={null}
            newsFreshness={null}
            showFallback={false}
            compact={isCompact}
          />
          <SourceModeBadge
            mode={providerMode}
            title="Indicators"
            compactTitle="Ind"
            showFallback={false}
            compact={isCompact}
          />
        </Stack>
      )}
    >
      <ReactECharts option={option} style={{ height: isCompact ? 264 : 320 }} />
    </ChartCard>
  );
}

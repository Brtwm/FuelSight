import { chartPalette } from '../../theme/theme';

export type ChartTooltipParam = {
  seriesName: string;
  value: number | null;
  marker: string;
  axisValueLabel: string;
  dataIndex?: number;
};

export const chartTextStyle = { color: '#e2e8f0', fontSize: 13 } as const;

export function formatChartDate(value: string, compact: boolean): string {
  return new Date(value).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: compact ? 'numeric' : '2-digit',
  });
}

export function formatTooltipDate(value: string): string {
  return new Date(value).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  });
}

export function formatChartNumber(value: number, maximumFractionDigits = 0): string {
  return Number(value).toLocaleString('ru-RU', { maximumFractionDigits });
}

export function formatLiters(value: number, maximumFractionDigits = 0): string {
  return `${formatChartNumber(value, maximumFractionDigits)} л`;
}

export function formatRub(value: number, maximumFractionDigits = 2): string {
  return `${formatChartNumber(value, maximumFractionDigits)} ₽`;
}

export function formatRubPerLiter(value: number, maximumFractionDigits = 2): string {
  return `${formatChartNumber(value, maximumFractionDigits)} ₽/л`;
}

export function getResponsiveChartHeight(compact: boolean): number {
  return compact ? 300 : 400;
}

export function buildAxisTooltip(formatter: (params: ChartTooltipParam[]) => string) {
  return {
    trigger: 'axis',
    backgroundColor: chartPalette.tooltipBg,
    borderColor: chartPalette.tooltipBorder,
    textStyle: chartTextStyle,
    formatter,
  };
}

export function renderTooltip(dateLabel: string, lines: string[]): string {
  return `<div style="font-family:'IBM Plex Sans',sans-serif">${dateLabel}<br/>${lines.join('<br/>')}</div>`;
}

export function buildLegend(data: string[], compact: boolean, hiddenSeries: string[] = []) {
  return {
    data,
    textStyle: { color: chartPalette.axisLabel },
    ...(compact && hiddenSeries.length > 0
      ? { selected: Object.fromEntries(hiddenSeries.map((item) => [item, false])) }
      : {}),
  };
}

export function buildChartGrid(compact: boolean) {
  return {
    left: compact ? 8 : 24,
    right: compact ? 8 : 24,
    top: compact ? 38 : 44,
    bottom: compact ? 44 : 48,
    containLabel: true,
  };
}

export function buildDataZoom(compact: boolean, fillerColor = 'rgba(56,213,255,0.14)') {
  if (compact) {
    return [];
  }
  return [
    {
      type: 'slider',
      height: 20,
      bottom: 4,
      borderColor: 'transparent',
      backgroundColor: 'rgba(255,255,255,0.03)',
      fillerColor,
      handleStyle: { color: chartPalette.primary },
      textStyle: { color: chartPalette.axisLabel },
      dataBackground: {
        lineStyle: { color: 'rgba(255,255,255,0.08)' },
        areaStyle: { color: 'rgba(255,255,255,0.04)' },
      },
    },
  ];
}

export function buildCategoryAxis(timeline: string[], compact: boolean) {
  return {
    type: 'category',
    data: timeline,
    axisLabel: {
      hideOverlap: true,
      fontSize: compact ? 10 : 12,
      color: chartPalette.axisLabel,
      formatter: (value: string) => formatChartDate(value, compact),
    },
    axisLine: { lineStyle: { color: chartPalette.axisLine } },
    splitLine: { show: false },
  };
}

export function buildValueAxis(name: string, splitLine = true, position?: 'left' | 'right') {
  return {
    type: 'value',
    name,
    ...(position ? { position } : {}),
    nameTextStyle: { color: chartPalette.axisLabel, fontSize: 11 },
    axisLabel: { color: chartPalette.axisLabel, fontSize: 11 },
    splitLine: splitLine ? { lineStyle: { color: chartPalette.gridLine } } : { show: false },
  };
}

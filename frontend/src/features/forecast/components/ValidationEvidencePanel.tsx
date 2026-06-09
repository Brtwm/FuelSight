import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import ReactECharts from 'echarts-for-react';
import { chartPalette } from '../../../theme/theme';
import {
  buildAxisTooltip,
  buildCategoryAxis,
  buildChartGrid,
  buildLegend,
  buildValueAxis,
  formatLiters,
  formatTooltipDate,
  renderTooltip,
  type ChartTooltipParam,
} from '../../../lib/charts/chartOptions';
import type {
  BacktestData,
  ValidationMetricValues,
  ValidationPeriod,
  ValidationSeriesPoint,
  ValidationStatus,
  ValidationSummary,
} from '../../../lib/api/forecast.types';

type Props = {
  backtest: BacktestData | null;
};

const DISCLAIMER = 'Прогноз является аналитической оценкой и не гарантирует точное значение будущего спроса или цены.';

const REASON_LABELS: Record<string, string> = {
  'CatBoost is evaluated on the test period and is not worse than Seasonal Naive by SMAPE.':
    'CatBoost проверен на тестовом периоде и не хуже сезонного ориентира по SMAPE.',
  'Backtest metrics are available, but dated test-period series is not persisted yet.':
    'Метрики backtest доступны, но датированный тестовый ряд пока не сохранён.',
  'Backtest comparison metrics are unavailable.':
    'Метрики сравнения backtest недоступны.',
  'CatBoost metrics are unavailable.':
    'Метрики CatBoost недоступны.',
  'Seasonal Naive metrics are unavailable.':
    'Метрики сезонного ориентира недоступны.',
  'CatBoost metrics are incomplete.':
    'Метрики CatBoost неполные.',
  'Seasonal Naive metrics are incomplete.':
    'Метрики сезонного ориентира неполные.',
  'Seasonal Naive SMAPE is zero, so comparison is limited.':
    'SMAPE сезонного ориентира равна нулю, поэтому сравнение ограничено.',
  'CatBoost is worse than Seasonal Naive by SMAPE.':
    'CatBoost хуже сезонного ориентира по SMAPE.',
  'Backtest metrics are available, but test observations are unknown.':
    'Метрики backtest доступны, но число наблюдений тестового периода неизвестно.',
  'Dated validation series is incomplete.':
    'Датированный тестовый ряд неполный.',
};

function normalizeStatus(value?: string | null): ValidationStatus {
  if (value === 'OK' || value === 'LIMITED' || value === 'UNKNOWN') {
    return value;
  }
  return 'UNKNOWN';
}

function fallbackSummary(backtest: BacktestData | null): ValidationSummary {
  return {
    status: 'UNKNOWN',
    status_reason: backtest
      ? 'Проверка качества пока недоступна'
      : 'Проверка качества пока недоступна',
    train_period: null,
    test_period: null,
    observations: null,
    metrics: null,
    series: [],
  };
}

function mapReason(status: ValidationStatus, reason?: string | null): string {
  if (reason && REASON_LABELS[reason]) {
    return REASON_LABELS[reason];
  }
  if (reason?.startsWith('Backtest has fewer than')) {
    return 'Недостаточно данных для уверенного вывода.';
  }
  if (reason && !/[A-Za-z]{3,}/.test(reason)) {
    return reason;
  }
  if (status === 'OK') {
    return 'Модель проверена на отложенном периоде.';
  }
  if (status === 'LIMITED') {
    return 'Недостаточно данных для уверенного вывода.';
  }
  return 'Проверка качества пока недоступна';
}

function formatDate(value?: string | null): string {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleDateString('ru-RU');
}

function formatPeriod(period?: ValidationPeriod | null): string {
  if (!period || (!period.start && !period.end)) {
    return 'Недоступно';
  }
  if (period.start && period.end) {
    return `${formatDate(period.start)} — ${formatDate(period.end)}`;
  }
  return `${formatDate(period.start)} — ${formatDate(period.end)}`;
}

function formatNumber(value?: number | null, suffix = ''): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return '—';
  }
  const formatted = new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 2,
  }).format(value);
  return `${formatted}${suffix}`;
}

function formatObservations(summary: ValidationSummary): string {
  const observations = summary.observations;
  if (
    !observations
    || (observations.total == null && observations.train == null && observations.test == null)
  ) {
    return 'Недоступно';
  }

  const parts = [
    typeof observations.total === 'number' ? `${formatNumber(observations.total)} всего` : null,
    typeof observations.train === 'number' ? `${formatNumber(observations.train)} обучение` : null,
    typeof observations.test === 'number' ? `${formatNumber(observations.test)} тест` : null,
  ].filter((item): item is string => Boolean(item));

  return parts.length > 0 ? parts.join(' / ') : 'Недоступно';
}

function formatImprovement(value?: number | null): string {
  return typeof value === 'number' && Number.isFinite(value) ? `${formatNumber(value, '%')}` : '—';
}

function formatSmapeImprovement(value?: number | null): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'SMAPE: улучшение недоступно';
  }
  const absoluteValue = formatNumber(Math.abs(value), '%');
  if (value > 0) {
    return `SMAPE: CatBoost лучше сезонного ориентира на ${absoluteValue}`;
  }
  if (value < 0) {
    return `SMAPE: CatBoost хуже сезонного ориентира на ${absoluteValue}`;
  }
  return 'SMAPE: CatBoost на уровне сезонного ориентира';
}

function hasMetrics(summary: ValidationSummary): boolean {
  return Boolean(summary.metrics?.catboost || summary.metrics?.seasonal_naive);
}

function MetricRow({
  label,
  metrics,
  improvement,
}: {
  label: string;
  metrics?: ValidationMetricValues | null;
  improvement: string;
}) {
  return (
    <TableRow>
      <TableCell>{label}</TableCell>
      <TableCell align="right">{formatNumber(metrics?.mae)}</TableCell>
      <TableCell align="right">{formatNumber(metrics?.rmse)}</TableCell>
      <TableCell align="right">{formatNumber(metrics?.smape, '%')}</TableCell>
      <TableCell align="right">{improvement}</TableCell>
    </TableRow>
  );
}

function ValidationChart({ series }: { series: ValidationSeriesPoint[] }) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));
  const timeline = series.map((point) => point.date);
  const option = {
    tooltip: buildAxisTooltip((params: ChartTooltipParam[]) => {
      if (!Array.isArray(params) || params.length === 0) return '';
      const dateLabel = formatTooltipDate(params[0].axisValueLabel);
      const lines = params
        .filter((point) => point.value != null)
        .map((point) => `${point.marker} ${point.seriesName}: <b>${formatLiters(Number(point.value))}</b>`);
      return renderTooltip(dateLabel, lines);
    }),
    legend: buildLegend(['Факт', 'CatBoost', 'Сезонный ориентир'], isCompact),
    grid: buildChartGrid(isCompact),
    xAxis: buildCategoryAxis(timeline, isCompact),
    yAxis: buildValueAxis('Литры'),
    series: [
      {
        name: 'Факт',
        type: 'line',
        smooth: true,
        data: series.map((point) => point.actual ?? null),
        lineStyle: { color: chartPalette.primary, width: 2.4 },
        itemStyle: { color: chartPalette.primary },
        symbol: 'circle',
        symbolSize: 4,
      },
      {
        name: 'CatBoost',
        type: 'line',
        smooth: true,
        data: series.map((point) => point.catboost_prediction ?? null),
        lineStyle: { color: chartPalette.secondary, width: 2 },
        itemStyle: { color: chartPalette.secondary },
        symbol: 'circle',
        symbolSize: 4,
      },
      {
        name: 'Сезонный ориентир',
        type: 'line',
        smooth: true,
        data: series.map((point) => point.seasonal_naive_prediction ?? null),
        lineStyle: { color: chartPalette.accent, width: 2, type: 'dashed' as const },
        itemStyle: { color: chartPalette.accent },
        symbol: 'diamond',
        symbolSize: 4,
      },
    ],
    animation: true,
    animationDuration: 500,
    animationEasing: 'cubicOut',
  };

  return (
    <Stack spacing={1}>
      <Typography variant="subtitle2" fontWeight={700}>
        Факт vs CatBoost vs простой сезонный ориентир
      </Typography>
      <ReactECharts option={option} style={{ height: isCompact ? 240 : 300 }} />
    </Stack>
  );
}

export function ValidationEvidencePanel({ backtest }: Props) {
  const summary = backtest?.validation_summary ?? fallbackSummary(backtest);
  const status = normalizeStatus(summary.status);
  const reason = mapReason(status, summary.status_reason);
  const series = summary.series ?? [];
  const hasSeries = series.length > 0;
  const smapeImprovement = summary.metrics?.improvement?.smape_pct;

  return (
    <Card>
      <CardContent>
        <Stack spacing={1.5}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            justifyContent="space-between"
          >
            <Stack spacing={0.4}>
              <Typography variant="h6" fontWeight={700}>
                Качество модели
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Проверка на отложенном периоде и сравнение с простым сезонным ориентиром
              </Typography>
            </Stack>
            <Chip
              label={status}
              size="small"
              color={status === 'OK' ? 'success' : status === 'LIMITED' ? 'warning' : 'default'}
            />
          </Stack>

          <Typography variant="body2" color="text.secondary">
            {reason}
          </Typography>

          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip size="small" variant="outlined" label={`Период обучения: ${formatPeriod(summary.train_period)}`} />
            <Chip size="small" variant="outlined" label={`Тестовый период: ${formatPeriod(summary.test_period)}`} />
            <Chip size="small" variant="outlined" label={`Наблюдения: ${formatObservations(summary)}`} />
          </Stack>

          {status === 'UNKNOWN' ? (
            <Alert severity="info">Недостаточно данных для уверенного вывода</Alert>
          ) : hasSeries ? (
            <ValidationChart series={series} />
          ) : (
            <Alert severity="warning">
              Backtest найден, но тестовый ряд недоступен для визуального сравнения
            </Alert>
          )}

          {hasMetrics(summary) && status !== 'UNKNOWN' ? (
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small" sx={{ minWidth: 560 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Модель</TableCell>
                    <TableCell align="right">MAE</TableCell>
                    <TableCell align="right">RMSE</TableCell>
                    <TableCell align="right">SMAPE</TableCell>
                    <TableCell align="right">Улучшение</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <MetricRow
                    label="CatBoost"
                    metrics={summary.metrics?.catboost}
                    improvement={formatImprovement(smapeImprovement)}
                  />
                  <MetricRow
                    label="Сезонный ориентир"
                    metrics={summary.metrics?.seasonal_naive}
                    improvement="база"
                  />
                </TableBody>
              </Table>
            </Box>
          ) : null}

          {hasMetrics(summary) && status !== 'UNKNOWN' ? (
            <Typography variant="body2" color="text.secondary">
              {formatSmapeImprovement(smapeImprovement)}
            </Typography>
          ) : null}

          <Typography variant="caption" color="text.secondary">
            {DISCLAIMER}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

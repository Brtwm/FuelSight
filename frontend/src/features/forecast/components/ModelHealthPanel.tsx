import { Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { BacktestData, ForecastData } from '../../../lib/api/forecast.types';

type Props = {
  forecast: ForecastData | null;
  backtest: BacktestData | null;
};

function formatDateRange(value: { start_date: string; end_date: string }): string {
  return `${new Date(value.start_date).toLocaleDateString('ru-RU')} — ${new Date(value.end_date).toLocaleDateString('ru-RU')}`;
}

function formatSmape(value?: number): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return '—';
  }
  return `${value.toFixed(2)}%`;
}

function mapFreshnessLabel(value: string | null): string | null {
  if (value === 'fresh') {
    return 'актуальна';
  }
  if (value === 'warning') {
    return 'требует проверки';
  }
  if (value === 'degraded') {
    return 'устарела';
  }
  return null;
}

function mapRetrainLabel(value: string | null): string | null {
  if (value === 'ok') {
    return 'в норме';
  }
  if (value === 'warning') {
    return 'скоро потребуется';
  }
  if (value === 'degraded') {
    return 'нужно обновить';
  }
  if (value === 'failed') {
    return 'требует ручного запуска';
  }
  return null;
}

function mapProviderLabel(value: string | null): string | null {
  if (value === 'manual_snapshot') {
    return 'Данные из локального проверенного источника';
  }
  if (value === 'live') {
    return 'актуальные данные';
  }
  if (value === 'cached') {
    return 'сохранённые данные';
  }
  return null;
}

function mapFeatureSourceLabel(value: string): string {
  const labels: Record<string, string> = {
    calendar: 'календарь',
    price: 'цены',
    lag: 'история спроса',
    rolling: 'динамика',
    external: 'внешние сигналы',
    news: 'новости',
    weather: 'погода',
  };
  return labels[value] ?? '';
}

function formatDeltaSmape(value?: number): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return '—';
  }
  const absValue = Math.abs(value).toFixed(2);
  if (value < 0) {
    return `лучше простого ориентира на ${absValue} п.п.`;
  }
  if (value > 0) {
    return `хуже простого ориентира на ${absValue} п.п.`;
  }
  return 'на уровне простого ориентира';
}

export function ModelHealthPanel({ forecast, backtest }: Props) {
  const modelFreshness = forecast?.model_freshness ?? backtest?.model_freshness ?? null;
  const retrainStatus = forecast?.retrain_status ?? backtest?.retrain_status ?? null;
  const providerMode = forecast?.provider_mode ?? backtest?.provider_mode ?? null;
  const trainingWindow = forecast?.training_window ?? backtest?.training_window ?? null;
  const baselineComparison = forecast?.baseline_comparison ?? backtest?.baseline_comparison ?? null;
  const winnerSmape = baselineComparison?.winner?.smape;
  const baselineSmape = baselineComparison?.seasonal_naive?.smape;
  const deltaSmape = baselineComparison?.delta_vs_baseline?.smape;
  const featureSources = forecast?.feature_sources ?? backtest?.feature_sources ?? [];

  const freshnessLabel = mapFreshnessLabel(modelFreshness);
  const retrainLabel = mapRetrainLabel(retrainStatus);
  const providerLabel = mapProviderLabel(providerMode);
  const hasChips = freshnessLabel || retrainLabel || providerLabel;
  const readableFeatureSources = featureSources.map(mapFeatureSourceLabel).filter(Boolean);

  return (
    <Card>
      <CardContent>
        <Stack spacing={1.2}>
          <Typography variant="h6" fontWeight={700}>
            Надёжность прогноза
          </Typography>
          {hasChips ? (
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              {freshnessLabel ? <Chip size="small" label={`Свежесть модели: ${freshnessLabel}`} /> : null}
              {retrainLabel ? <Chip size="small" label={`Последнее обновление модели: ${retrainLabel}`} /> : null}
              {providerLabel ? <Chip size="small" label={`Источник: ${providerLabel}`} /> : null}
            </Stack>
          ) : null}
          {trainingWindow ? (
            <Typography variant="body2" color="text.secondary">
              Период обучения: {formatDateRange(trainingWindow)}
            </Typography>
          ) : null}
          {typeof winnerSmape === 'number' || typeof baselineSmape === 'number' ? (
            <Typography variant="body2" color="text.secondary">
              Средняя относительная ошибка (основной расчёт / простой ориентир): {formatSmape(winnerSmape)} / {formatSmape(baselineSmape)}
            </Typography>
          ) : null}
          {typeof deltaSmape === 'number' ? (
            <Typography variant="body2" color="text.secondary">
              Качество относительно простого ориентира: {formatDeltaSmape(deltaSmape)}
            </Typography>
          ) : null}
          {readableFeatureSources.length > 0 ? (
            <Typography variant="body2" color="text.secondary">
              Группы факторов: {readableFeatureSources.join(', ')}
            </Typography>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

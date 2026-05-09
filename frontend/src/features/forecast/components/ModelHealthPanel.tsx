import { Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { BacktestData, ForecastData } from '../../../lib/api/forecast.types';

type Props = {
  forecast: ForecastData | null;
  backtest: BacktestData | null;
};

function formatDateRange(value?: { start_date: string; end_date: string } | null): string {
  if (!value) {
    return '—';
  }
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
    return 'свежая';
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
    return 'рекомендуется';
  }
  if (value === 'failed') {
    return 'нужно вручную запустить';
  }
  return null;
}

function mapProviderLabel(value: string | null): string | null {
  if (value === 'manual_snapshot') {
    return 'проверенный контур';
  }
  if (value === 'live') {
    return 'актуальные данные';
  }
  if (value === 'cached') {
    return 'кэш';
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
  return labels[value] ?? value.replaceAll('_', ' ');
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

  return (
    <Card>
      <CardContent>
        <Stack spacing={1.2}>
          <Typography variant="h6" fontWeight={700}>
            Здоровье модели
          </Typography>
          {hasChips ? (
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              {freshnessLabel ? <Chip size="small" label={`Модель: ${freshnessLabel}`} /> : null}
              {retrainLabel ? <Chip size="small" label={`Переобучение: ${retrainLabel}`} /> : null}
              {providerLabel ? <Chip size="small" label={`Источник: ${providerLabel}`} /> : null}
            </Stack>
          ) : null}
          <Typography variant="body2" color="text.secondary">
            Окно обучения: {formatDateRange(trainingWindow)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Средняя ошибка (модель / простой ориентир): {formatSmape(winnerSmape)} / {formatSmape(baselineSmape)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Качество относительно простого ориентира: {formatDeltaSmape(deltaSmape)}
          </Typography>
          {featureSources.length > 0 ? (
            <Typography variant="body2" color="text.secondary">
              Группы факторов: {featureSources.map(mapFeatureSourceLabel).join(', ')}
            </Typography>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

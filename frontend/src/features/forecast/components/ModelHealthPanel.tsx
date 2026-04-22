import { Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { BacktestData, ForecastData } from '../../../lib/api/forecast.types';

type Props = {
  forecast: ForecastData | null;
  backtest: BacktestData | null;
};

function formatDateRange(value?: { start_date: string; end_date: string } | null): string {
  if (!value) {
    return 'n/a';
  }
  return `${new Date(value.start_date).toLocaleDateString('ru-RU')} - ${new Date(value.end_date).toLocaleDateString('ru-RU')}`;
}

function formatSmape(value?: number): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'n/a';
  }
  return `${value.toFixed(2)}%`;
}

function mapFreshnessLabel(value: string | null): string {
  if (value === 'fresh') {
    return 'свежая';
  }
  if (value === 'warning') {
    return 'требует проверки';
  }
  if (value === 'degraded') {
    return 'устарела';
  }
  return 'n/a';
}

function mapRetrainLabel(value: string | null): string {
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
  return 'n/a';
}

function formatDeltaSmape(value?: number): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'n/a';
  }
  const absValue = Math.abs(value).toFixed(2);
  if (value < 0) {
    return `лучше baseline на ${absValue} п.п.`;
  }
  if (value > 0) {
    return `хуже baseline на ${absValue} п.п.`;
  }
  return 'на уровне baseline';
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

  return (
    <Card>
      <CardContent>
        <Stack spacing={1.2}>
          <Typography variant="h6" fontWeight={700}>
            Здоровье модели
          </Typography>
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            <Chip size="small" label={`Свежесть модели: ${mapFreshnessLabel(modelFreshness)}`} />
            <Chip size="small" label={`Переобучение: ${mapRetrainLabel(retrainStatus)}`} />
            <Chip size="small" label={`Контур данных: ${providerMode ?? 'n/a'}`} />
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Окно обучения: {formatDateRange(trainingWindow)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            SMAPE (модель / baseline): {formatSmape(winnerSmape)} / {formatSmape(baselineSmape)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Качество относительно baseline: {formatDeltaSmape(deltaSmape)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Используемые группы факторов: {featureSources.length > 0 ? featureSources.join(', ') : 'n/a'}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

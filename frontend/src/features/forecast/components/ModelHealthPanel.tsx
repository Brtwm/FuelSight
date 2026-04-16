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
            <Chip size="small" label={`Freshness: ${modelFreshness ?? 'n/a'}`} />
            <Chip size="small" label={`Retrain: ${retrainStatus ?? 'n/a'}`} />
            <Chip size="small" label={`Источник: ${providerMode ?? 'n/a'}`} />
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Окно обучения: {formatDateRange(trainingWindow)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            SMAPE winner/baseline: {formatSmape(winnerSmape)} / {formatSmape(baselineSmape)}
            {typeof deltaSmape === 'number' ? ` (Δ ${deltaSmape.toFixed(2)} п.п.)` : ''}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Источники признаков: {featureSources.length > 0 ? featureSources.join(', ') : 'n/a'}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}


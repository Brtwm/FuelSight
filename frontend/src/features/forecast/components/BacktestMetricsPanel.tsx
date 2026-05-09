import { Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { BacktestData } from '../../../lib/api/forecast.types';

type Props = {
  backtest: BacktestData | null;
};

function formatMetric(value: number): string {
  return Number.isFinite(value) ? value.toFixed(2) : '—';
}

function formatCheckDate(value: string): string {
  return new Date(value).toLocaleDateString('ru-RU');
}

function mapWindowType(value: BacktestData['window_type']): string {
  if (value === 'rolling') {
    return 'скользящая проверка';
  }
  return 'расширяющаяся проверка';
}

export function BacktestMetricsPanel({ backtest }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="h6" fontWeight={700}>
            Качество прогноза
          </Typography>

          {!backtest ? (
            <Typography color="text.secondary">
              Проверка качества ещё не запускалась для выбранного продукта и горизонта.
            </Typography>
          ) : (
            <>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Chip label={`MAE: средняя ошибка ${formatMetric(backtest.metrics.mae)} л`} size="small" />
                <Chip label={`RMSE: крупные промахи ${formatMetric(backtest.metrics.rmse)} л`} size="small" />
                <Chip label={`SMAPE: относительная ошибка ${formatMetric(backtest.metrics.smape)}%`} size="small" />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Метод проверки: {mapWindowType(backtest.window_type)}, последняя проверка:{' '}
                {formatCheckDate(backtest.trained_at)}
              </Typography>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

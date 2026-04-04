import { Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { BacktestData } from '../../../lib/api/forecast.types';

type Props = {
  backtest: BacktestData | null;
};

function formatMetric(value: number): string {
  return Number.isFinite(value) ? value.toFixed(2) : 'n/a';
}

export function BacktestMetricsPanel({ backtest }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="h6" fontWeight={700}>
            Метрики backtest
          </Typography>

          {!backtest ? (
            <Typography color="text.secondary">
              Backtest ещё не запускался для выбранного продукта и горизонта.
            </Typography>
          ) : (
            <>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Chip label={`MAE: ${formatMetric(backtest.metrics.mae)}`} size="small" />
                <Chip label={`RMSE: ${formatMetric(backtest.metrics.rmse)}`} size="small" />
                <Chip label={`SMAPE: ${formatMetric(backtest.metrics.smape)}%`} size="small" />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Модель: {backtest.model_type}, окно: {backtest.window_type}, версия:{' '}
                {backtest.model_version ?? 'n/a'}
              </Typography>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}


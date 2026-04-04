import {
  Button,
  Card,
  CardContent,
  FormControlLabel,
  Grid,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import type { ForecastHorizonDays } from '../../../lib/api/forecast.types';

type Props = {
  productCode: string;
  horizonDays: ForecastHorizonDays;
  scenarioEnabled: boolean;
  retailPriceDeltaPct: number;
  isRunningForecast: boolean;
  isRunningBacktest: boolean;
  canRunBacktest: boolean;
  onProductCodeChange: (value: string) => void;
  onHorizonDaysChange: (value: ForecastHorizonDays) => void;
  onScenarioEnabledChange: (value: boolean) => void;
  onRetailPriceDeltaPctChange: (value: number) => void;
  onRunForecast: () => void;
  onRunBacktest: () => void;
};

const PRODUCT_OPTIONS = ['AI_92', 'AI_95', 'DT_S', 'DT_W'] as const;

export function ForecastControlPanel({
  productCode,
  horizonDays,
  scenarioEnabled,
  retailPriceDeltaPct,
  isRunningForecast,
  isRunningBacktest,
  canRunBacktest,
  onProductCodeChange,
  onHorizonDaysChange,
  onScenarioEnabledChange,
  onRetailPriceDeltaPctChange,
  onRunForecast,
  onRunBacktest,
}: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            Параметры прогноза
          </Typography>

          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                select
                label="Продукт"
                value={productCode}
                onChange={(event) => onProductCodeChange(event.target.value)}
              >
                {PRODUCT_OPTIONS.map((item) => (
                  <MenuItem key={item} value={item}>
                    {item}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                select
                label="Горизонт"
                value={String(horizonDays)}
                onChange={(event) => onHorizonDaysChange(Number(event.target.value) as ForecastHorizonDays)}
              >
                <MenuItem value="1">1 день</MenuItem>
                <MenuItem value="7">7 дней</MenuItem>
                <MenuItem value="30">30 дней</MenuItem>
              </TextField>
            </Grid>

            <Grid size={{ xs: 12, md: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={scenarioEnabled}
                    onChange={(event) => onScenarioEnabledChange(event.target.checked)}
                  />
                }
                label="Scenario mode"
              />
            </Grid>

            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                label="Δ розничной цены, %"
                type="number"
                value={retailPriceDeltaPct}
                inputProps={{ min: -40, max: 40, step: 0.1 }}
                disabled={!scenarioEnabled}
                onChange={(event) => onRetailPriceDeltaPctChange(Number(event.target.value))}
              />
            </Grid>
          </Grid>

          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={onRunForecast} disabled={isRunningForecast}>
              {isRunningForecast ? 'Считаем прогноз...' : 'Запустить прогноз'}
            </Button>
            {canRunBacktest ? (
              <Button variant="outlined" onClick={onRunBacktest} disabled={isRunningBacktest}>
                {isRunningBacktest ? 'Считаем backtest...' : 'Обновить backtest'}
              </Button>
            ) : null}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}


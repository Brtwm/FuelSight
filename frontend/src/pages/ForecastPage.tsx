import {
  Alert,
  Button,
  Card,
  CardContent,
  Grid,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthProvider';
import { BacktestMetricsPanel } from '../features/forecast/components/BacktestMetricsPanel';
import { ForecastChart } from '../features/forecast/components/ForecastChart';
import { ForecastControlPanel } from '../features/forecast/components/ForecastControlPanel';
import { ForecastDriversPanel } from '../features/forecast/components/ForecastDriversPanel';
import { resolveForecastFilters, toSearchParams } from '../features/forecast/urlFilters';
import { fetchLatestBacktest, fetchLatestForecast, runBacktest, runForecast } from '../lib/api/forecast';
import { ApiHttpError } from '../lib/api/http';
import { DEFAULT_PRODUCT } from '../lib/config/env';
import type { BacktestData, ForecastData } from '../lib/api/forecast.types';

function formatNumber(value: number | null): string {
  if (value === null) {
    return 'n/a';
  }
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(value);
}

export function ForecastPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { authFetch, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [runForecastData, setRunForecastData] = useState<ForecastData | null>(null);
  const [runBacktestData, setRunBacktestData] = useState<BacktestData | null>(null);

  const defaults = useMemo(
    () => ({
      product_code: DEFAULT_PRODUCT,
      horizon_days: 7 as const,
    }),
    [],
  );

  const filters = useMemo(
    () => resolveForecastFilters(searchParams, defaults),
    [defaults, searchParams],
  );

  useEffect(() => {
    const normalized = toSearchParams(filters).toString();
    if (searchParams.toString() !== normalized) {
      setSearchParams(toSearchParams(filters), { replace: true });
    }
  }, [filters, searchParams, setSearchParams]);

  const latestForecastQuery = useQuery({
    queryKey: ['forecast', 'latest', filters.product_code, filters.horizon_days],
    queryFn: () =>
      fetchLatestForecast(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
      }),
  });

  const latestBacktestQuery = useQuery({
    queryKey: ['backtests', 'latest', filters.product_code, filters.horizon_days],
    queryFn: () =>
      fetchLatestBacktest(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
      }),
  });

  const runForecastMutation = useMutation({
    mutationFn: () =>
      runForecast(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
        scenario: filters.scenario_enabled
          ? { retail_price_delta_pct: filters.retail_price_delta_pct }
          : undefined,
      }),
    onSuccess: async (payload) => {
      setRunForecastData(payload);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['forecast'] }),
        queryClient.invalidateQueries({ queryKey: ['backtests'] }),
      ]);
    },
  });

  const runBacktestMutation = useMutation({
    mutationFn: () =>
      runBacktest(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
        window_type: 'rolling',
      }),
    onSuccess: async (payload) => {
      setRunBacktestData(payload);
      await queryClient.invalidateQueries({ queryKey: ['backtests'] });
    },
  });

  const isLoading = latestForecastQuery.isLoading || latestBacktestQuery.isLoading;
  const isMutating = runForecastMutation.isPending || runBacktestMutation.isPending;
  const activeError =
    runForecastMutation.error ??
    runBacktestMutation.error ??
    latestForecastQuery.error ??
    latestBacktestQuery.error;

  const forecastData = runForecastData ?? latestForecastQuery.data ?? null;
  const backtestData = runBacktestData ?? latestBacktestQuery.data ?? null;

  const isInsufficientHistory =
    activeError instanceof ApiHttpError &&
    activeError.code === 'validation_error' &&
    /insufficient history/i.test(activeError.message);

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          Прогноз спроса
        </Typography>
        <Skeleton variant="rounded" height={72} />
        <Skeleton variant="rounded" height={320} />
        <Skeleton variant="rounded" height={220} />
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="h4" fontWeight={700}>
          Прогноз спроса
        </Typography>
        <Typography color="text.secondary">
          Прогноз на 1/7/30 дней с интервалами, метриками backtest и сценарным what-if по цене.
        </Typography>
      </Stack>

      <ForecastControlPanel
        productCode={filters.product_code}
        horizonDays={filters.horizon_days}
        scenarioEnabled={filters.scenario_enabled}
        retailPriceDeltaPct={filters.retail_price_delta_pct}
        isRunningForecast={runForecastMutation.isPending}
        isRunningBacktest={runBacktestMutation.isPending}
        canRunBacktest={user?.role === 'admin'}
        onProductCodeChange={(value) =>
          setSearchParams(
            toSearchParams({
              ...filters,
              product_code: value,
            }),
          )
        }
        onHorizonDaysChange={(value) =>
          setSearchParams(
            toSearchParams({
              ...filters,
              horizon_days: value,
            }),
          )
        }
        onScenarioEnabledChange={(value) =>
          setSearchParams(
            toSearchParams({
              ...filters,
              scenario_enabled: value,
            }),
          )
        }
        onRetailPriceDeltaPctChange={(value) =>
          setSearchParams(
            toSearchParams({
              ...filters,
              retail_price_delta_pct: value,
            }),
          )
        }
        onRunForecast={() => runForecastMutation.mutate()}
        onRunBacktest={() => runBacktestMutation.mutate()}
      />

      {isInsufficientHistory ? (
        <Alert
          severity="warning"
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/import')}>
              Загрузить демо-данные
            </Button>
          }
        >
          Истории недостаточно для расчёта прогноза и backtest. Загрузите данные или сгенерируйте демо-набор.
        </Alert>
      ) : null}

      {activeError && !isInsufficientHistory ? (
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                void latestForecastQuery.refetch();
                void latestBacktestQuery.refetch();
              }}
            >
              Повторить
            </Button>
          }
        >
          Не удалось загрузить прогноз или backtest. Проверьте backend и повторите запрос.
        </Alert>
      ) : null}

      {!forecastData && !isMutating ? (
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>
                Прогноз пока не запускался
              </Typography>
              <Typography color="text.secondary">
                Выберите продукт и горизонт, затем нажмите «Запустить прогноз».
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      ) : null}

      {forecastData ? (
        <>
          {forecastData.model_status === 'baseline_fallback' ? (
            <Alert severity="info">
              Для выбранного горизонта нет активной модели, используется baseline_fallback.
            </Alert>
          ) : null}

          <ForecastChart points={forecastData.forecast_points} />

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 5 }}>
              <BacktestMetricsPanel backtest={backtestData} />
            </Grid>
            <Grid size={{ xs: 12, md: 7 }}>
              <ForecastDriversPanel drivers={forecastData.drivers} />
            </Grid>
          </Grid>

          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
                Таблица прогноза
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell align="right">Прогноз, л</TableCell>
                    <TableCell align="right">Нижняя граница</TableCell>
                    <TableCell align="right">Верхняя граница</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {forecastData.forecast_points.map((point) => (
                    <TableRow key={point.target_date}>
                      <TableCell>{new Date(point.target_date).toLocaleDateString('ru-RU')}</TableCell>
                      <TableCell align="right">{formatNumber(point.y_hat)}</TableCell>
                      <TableCell align="right">{formatNumber(point.y_lo)}</TableCell>
                      <TableCell align="right">{formatNumber(point.y_hi)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      ) : null}
    </Stack>
  );
}


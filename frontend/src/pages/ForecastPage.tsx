import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
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
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppShellSlots } from '../app/layout/AppShellSlotsContext';
import { ChartCard, ExternalContextPanel, FreshnessBadgeGroup } from '../components/common';
import { useAuth } from '../features/auth/AuthProvider';
import { BacktestMetricsPanel } from '../features/forecast/components/BacktestMetricsPanel';
import { ForecastChart } from '../features/forecast/components/ForecastChart';
import { ForecastControlPanel } from '../features/forecast/components/ForecastControlPanel';
import { ForecastDriversPanel } from '../features/forecast/components/ForecastDriversPanel';
import { ModelHealthPanel } from '../features/forecast/components/ModelHealthPanel';
import { resolveForecastFilters, toSearchParams } from '../features/forecast/urlFilters';
import {
  fetchLatestBacktestWithMeta,
  fetchLatestForecastWithMeta,
  runBacktestWithMeta,
  runForecastWithMeta,
} from '../lib/api/forecast';
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
  const theme = useTheme();
  const isMobileReadingOrder = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const { patchSlots } = useAppShellSlots();
  const queryClient = useQueryClient();
  const { authFetch, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [runBaseForecastData, setRunBaseForecastData] = useState<ForecastData | null>(null);
  const [runScenarioForecastData, setRunScenarioForecastData] = useState<ForecastData | null>(null);
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
      fetchLatestForecastWithMeta(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
      }),
  });

  const latestBacktestQuery = useQuery({
    queryKey: ['backtests', 'latest', filters.product_code, filters.horizon_days],
    queryFn: () =>
      fetchLatestBacktestWithMeta(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
      }),
  });

  const runForecastMutation = useMutation({
    mutationFn: async () => {
      const shouldRunScenario = filters.scenario_enabled && filters.retail_price_delta_pct !== 0;
      const base = await runForecastWithMeta(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
      });
      let scenario: Awaited<ReturnType<typeof runForecastWithMeta>> | null = null;
      if (shouldRunScenario) {
        scenario = await runForecastWithMeta(authFetch, {
          product_code: filters.product_code,
          horizon_days: filters.horizon_days,
          scenario: { retail_price_delta_pct: filters.retail_price_delta_pct },
        });
      }
      return { base, scenario };
    },
    onSuccess: async ({ base, scenario }) => {
      setRunBaseForecastData(base.data);
      setRunScenarioForecastData(scenario?.data ?? null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['forecast'] }),
        queryClient.invalidateQueries({ queryKey: ['backtests'] }),
      ]);
    },
  });

  const runBacktestMutation = useMutation({
    mutationFn: () =>
      runBacktestWithMeta(authFetch, {
        product_code: filters.product_code,
        horizon_days: filters.horizon_days,
        window_type: 'rolling',
      }),
    onSuccess: async (payload) => {
      setRunBacktestData(payload.data);
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

  const latestForecastData = latestForecastQuery.data?.data ?? null;
  const latestBaseForecastData = latestForecastData?.scenario_name === 'base'
    ? latestForecastData
    : null;
  const latestScenarioForecastData = latestForecastData?.scenario_name === 'what_if_price'
    ? latestForecastData
    : null;
  const forecastData = runBaseForecastData ?? latestBaseForecastData;
  const scenarioForecastData = runScenarioForecastData ?? latestScenarioForecastData;
  const backtestData = runBacktestData ?? latestBacktestQuery.data?.data ?? null;
  const forecastMeta = latestForecastQuery.data?.meta;
  const backtestMeta = latestBacktestQuery.data?.meta;
  const dataFreshness = forecastMeta?.data_freshness ?? backtestMeta?.data_freshness ?? null;
  const modelFreshness =
    forecastData?.model_freshness
    ?? backtestData?.model_freshness
    ?? forecastMeta?.model_freshness
    ?? backtestMeta?.model_freshness
    ?? null;
  const llmMode = forecastMeta?.llm_mode ?? backtestMeta?.llm_mode ?? null;
  const newsFreshness = forecastMeta?.news_freshness ?? backtestMeta?.news_freshness ?? null;
  const externalIndicatorsMode =
    forecastMeta?.external_indicators_mode
    ?? backtestMeta?.external_indicators_mode
    ?? null;

  useEffect(() => {
    patchSlots({
      dataFreshness,
      modelFreshness,
      llmMode,
      newsFreshness,
      externalIndicatorsMode,
    });
  }, [
    dataFreshness,
    externalIndicatorsMode,
    llmMode,
    modelFreshness,
    newsFreshness,
    patchSlots,
  ]);

  const isInsufficientHistory =
    activeError instanceof ApiHttpError &&
    activeError.code === 'validation_error' &&
    /insufficient history/i.test(activeError.message);
  const retrainStatus = forecastData?.retrain_status ?? backtestData?.retrain_status ?? null;
  const providerMode = forecastData?.provider_mode ?? backtestData?.provider_mode ?? null;

  useEffect(() => {
    if (!filters.scenario_enabled || filters.retail_price_delta_pct === 0) {
      setRunScenarioForecastData(null);
    }
  }, [filters.retail_price_delta_pct, filters.scenario_enabled]);

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
          CatBoost-first прогноз с прозрачным quality-контуром, baseline comparison и сценарной оценкой.
        </Typography>
        <FreshnessBadgeGroup
          dataFreshness={dataFreshness}
          modelFreshness={modelFreshness}
          newsFreshness={newsFreshness}
          showFallback={false}
        />
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
              Открыть импорт
            </Button>
          }
        >
          Истории недостаточно для расчёта прогноза и backtest. Загрузите данные или обновите начальную историю.
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

      {modelFreshness && modelFreshness !== 'fresh' ? (
        <Alert severity="warning">
          Статус модели: {modelFreshness}. Проверьте свежесть признаков и последний retrain.
        </Alert>
      ) : null}

      {forecastData ? (
        <>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="subtitle1" fontWeight={700}>
                  Сводка статуса модели
                </Typography>
                <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                  <Chip size="small" label={`Freshness: ${modelFreshness ?? 'n/a'}`} />
                  <Chip size="small" label={`Retrain: ${retrainStatus ?? 'n/a'}`} />
                  <Chip size="small" label={`Источник: ${providerMode ?? 'n/a'}`} />
                  <Chip size="small" label={`Режим: ${forecastData.model_status}`} />
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          {forecastData.model_status === 'baseline_fallback' ? (
            <Alert severity="info">
              Для выбранного горизонта нет активной модели, используется baseline_fallback.
            </Alert>
          ) : null}

          <ChartCard
            title="Base vs Scenario прогноз"
            subtitle="Факт и доверительные интервалы показываются вместе со сценарной линией."
            state="ready"
          >
            <ForecastChart
              basePoints={forecastData.forecast_points}
              scenarioPoints={scenarioForecastData?.forecast_points ?? null}
              overlays={forecastData.reference_overlays ?? []}
              eventContext={forecastData.event_context ?? []}
              providerMode={forecastData.external_context_quality?.provider_mode ?? providerMode}
              manifestRunDate={forecastData.external_context_quality?.manifest_run_date ?? null}
            />
          </ChartCard>
          <ExternalContextPanel
            context={forecastData.external_context_quality ?? null}
            title="Контекст внешних признаков прогноза"
            extraLines={(forecastData.event_context ?? [])
              .slice(0, 3)
              .map((item) => `${item.title}: ${item.start_date} - ${item.end_date}`)}
          />

          {isMobileReadingOrder ? (
            <Stack spacing={2}>
              <ModelHealthPanel forecast={forecastData} backtest={backtestData} />
              <BacktestMetricsPanel backtest={backtestData} />
              <ForecastDriversPanel drivers={forecastData.drivers} />
            </Stack>
          ) : (
            <>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 5 }}>
                  <ModelHealthPanel forecast={forecastData} backtest={backtestData} />
                </Grid>
                <Grid size={{ xs: 12, md: 7 }}>
                  <ForecastDriversPanel drivers={forecastData.drivers} />
                </Grid>
              </Grid>
              <BacktestMetricsPanel backtest={backtestData} />
            </>
          )}

          <ChartCard
            title={isMobileReadingOrder ? 'Прогноз по дням (Base vs Scenario)' : 'Таблица прогноза (Base vs Scenario)'}
            state="ready"
          >
            {isMobileReadingOrder ? (
              <Stack spacing={1.25}>
                {forecastData.forecast_points.map((point) => {
                  const scenarioPoint = scenarioForecastData?.forecast_points.find(
                    (item) => item.target_date === point.target_date,
                  );
                  return (
                    <Card key={point.target_date} variant="outlined">
                      <CardContent sx={{ py: 1.25, '&:last-child': { pb: 1.25 } }}>
                        <Stack spacing={0.5}>
                          <Typography variant="subtitle2" fontWeight={700}>
                            {new Date(point.target_date).toLocaleDateString('ru-RU')}
                          </Typography>
                          <Typography variant="body2">Base: {formatNumber(point.y_hat)} л</Typography>
                          <Typography variant="body2">Scenario: {formatNumber(scenarioPoint?.y_hat ?? null)} л</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Диапазон: {formatNumber(point.y_lo)} - {formatNumber(point.y_hi)} л
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  );
                })}
              </Stack>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell align="right">Base, л</TableCell>
                    <TableCell align="right">Scenario, л</TableCell>
                    <TableCell align="right">Нижняя граница</TableCell>
                    <TableCell align="right">Верхняя граница</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {forecastData.forecast_points.map((point) => {
                    const scenarioPoint = scenarioForecastData?.forecast_points.find(
                      (item) => item.target_date === point.target_date,
                    );
                    return (
                      <TableRow key={point.target_date}>
                        <TableCell>{new Date(point.target_date).toLocaleDateString('ru-RU')}</TableCell>
                        <TableCell align="right">{formatNumber(point.y_hat)}</TableCell>
                        <TableCell align="right">{formatNumber(scenarioPoint?.y_hat ?? null)}</TableCell>
                        <TableCell align="right">{formatNumber(point.y_lo)}</TableCell>
                        <TableCell align="right">{formatNumber(point.y_hi)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </ChartCard>
        </>
      ) : (
        <ChartCard
          title="Base vs Scenario прогноз"
          state={isMutating ? 'loading' : 'empty'}
          emptyTitle="Прогноз пока не запускался"
          emptyDescription="Выберите продукт и горизонт, затем запустите расчёт."
          loadingLabel="Считаем base/scenario прогноз..."
        />
      )}
    </Stack>
  );
}


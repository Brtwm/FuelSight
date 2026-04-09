import { Alert, Button, Card, CardContent, Grid, Skeleton, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppShellSlots } from '../app/layout/AppShellSlotsContext';
import {
  buildDefaultDateRange,
  resolveAnalyticsFilters,
  toSearchParams,
} from '../features/analytics/urlFilters';
import { ComparisonsPanel } from '../features/sales/components/ComparisonsPanel';
import { SalesAnomalyTable } from '../features/sales/components/SalesAnomalyTable';
import { SalesFilterBar } from '../features/sales/components/SalesFilterBar';
import { SalesTrendChart } from '../features/sales/components/SalesTrendChart';
import { SeasonalityPanel } from '../features/sales/components/SeasonalityPanel';
import { useAuth } from '../features/auth/AuthProvider';
import {
  fetchAnalyticsAnomalies,
  fetchSalesAnalyticsWithMeta,
} from '../lib/api/analytics';
import { DEFAULT_PRODUCT } from '../lib/config/env';
import type { AnalyticsUrlFilters } from '../features/analytics/urlFilters';
import type { AnalyticsAnomaly } from '../lib/api/analytics.types';

export function SalesAnalyticsPage() {
  const navigate = useNavigate();
  const { patchSlots } = useAppShellSlots();
  const { authFetch } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const defaults = useMemo(
    () => ({
      product_code: DEFAULT_PRODUCT,
      ...buildDefaultDateRange(),
    }),
    [],
  );

  const filters = useMemo(
    () => resolveAnalyticsFilters(searchParams, defaults),
    [defaults, searchParams],
  );

  useEffect(() => {
    const normalized = toSearchParams(filters).toString();
    if (searchParams.toString() !== normalized) {
      setSearchParams(toSearchParams(filters), { replace: true });
    }
  }, [filters, searchParams, setSearchParams]);

  const salesQuery = useQuery({
    queryKey: ['analytics', 'sales', filters],
    queryFn: () =>
      fetchSalesAnalyticsWithMeta(authFetch, {
        product_code: filters.product_code,
        date_from: filters.date_from,
        date_to: filters.date_to,
        granularity: filters.granularity,
      }),
  });

  const anomaliesQuery = useQuery({
    queryKey: ['analytics', 'anomalies', 'sales', filters],
    queryFn: () =>
      fetchAnalyticsAnomalies(authFetch, {
        metric: 'sales',
        product_code: filters.product_code,
        date_from: filters.date_from,
        date_to: filters.date_to,
      }),
  });

  const isLoading = salesQuery.isLoading || anomaliesQuery.isLoading;
  const isError = salesQuery.isError || anomaliesQuery.isError;
  const sales = salesQuery.data?.data ?? null;
  const salesMeta = salesQuery.data?.meta;
  const anomalies = anomaliesQuery.data ?? [];
  const dataFreshness = salesMeta?.data_freshness ?? null;
  const modelFreshness = salesMeta?.model_freshness ?? null;
  const llmMode = salesMeta?.llm_mode ?? null;
  const newsFreshness = salesMeta?.news_freshness ?? null;
  const externalIndicatorsMode = salesMeta?.external_indicators_mode ?? null;

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

  const updateFilters = (patch: Partial<AnalyticsUrlFilters>) => {
    const next = { ...filters, ...patch };
    setSearchParams(toSearchParams(next));
  };

  const handleOpenAnomaly = (item: AnalyticsAnomaly) => {
    const nextSearch = toSearchParams(filters);
    navigate(`${item.target_path}?${nextSearch.toString()}`);
  };

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          Аналитика продаж
        </Typography>
        <Skeleton variant="rounded" height={72} />
        <Skeleton variant="rounded" height={320} />
        <Skeleton variant="rounded" height={220} />
      </Stack>
    );
  }

  if (isError) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          Аналитика продаж
        </Typography>
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                void salesQuery.refetch();
                void anomaliesQuery.refetch();
              }}
            >
              Повторить
            </Button>
          }
        >
          Не удалось загрузить аналитику продаж. Проверьте backend и повторите запрос.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="h4" fontWeight={700}>
          Аналитика продаж
        </Typography>
        <Typography color="text.secondary">
          Временной ряд спроса, сезонность и сравнение периодов по выбранному продукту.
        </Typography>
      </Stack>

      <SalesFilterBar
        productCode={filters.product_code}
        dateFrom={filters.date_from}
        dateTo={filters.date_to}
        granularity={filters.granularity}
        onProductCodeChange={(value) => updateFilters({ product_code: value })}
        onDateFromChange={(value) => updateFilters({ date_from: value })}
        onDateToChange={(value) => updateFilters({ date_to: value })}
        onGranularityChange={(value) => updateFilters({ granularity: value })}
      />

      {!sales || sales.series.length === 0 ? (
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>
                Нет данных продаж за выбранный период
              </Typography>
              <Typography color="text.secondary">
                Добавьте данные продаж и закупок или обновите начальную историю на странице импорта.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/import')}>
                Перейти к импорту
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ) : (
        <>
          <SalesTrendChart series={sales.series} />

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 7 }}>
              <SeasonalityPanel seasonality={sales.seasonality} />
            </Grid>
            <Grid size={{ xs: 12, md: 5 }}>
              <ComparisonsPanel comparisons={sales.comparisons} />
            </Grid>
          </Grid>

          <SalesAnomalyTable anomalies={anomalies} onOpenDetails={handleOpenAnomaly} />
        </>
      )}
    </Stack>
  );
}


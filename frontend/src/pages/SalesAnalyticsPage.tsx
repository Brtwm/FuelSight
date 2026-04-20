import { Grid, Skeleton, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppShellSlots } from '../app/layout/AppShellSlotsContext';
import { BusinessSummaryCard, DataStatePanel, FreshnessBadgeGroup, type DataState } from '../components/common';
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
import { fetchAnalyticsAnomalies, fetchSalesAnalyticsWithMeta } from '../lib/api/analytics';
import { DEFAULT_PRODUCT } from '../lib/config/env';
import type { AnalyticsUrlFilters } from '../features/analytics/urlFilters';
import type { AnalyticsAnomaly } from '../lib/api/analytics.types';

export function SalesAnalyticsPage() {
  const navigate = useNavigate();
  const { patchSlots } = useAppShellSlots();
  const { authFetch, user } = useAuth();
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
  const explainability = salesMeta?.explainability;
  const anomalies = anomaliesQuery.data ?? [];

  const dataFreshness = explainability?.trust?.data_freshness ?? null;
  const modelFreshness = null;
  const llmMode = null;
  const newsFreshness = null;
  const externalIndicatorsMode = explainability?.trust?.mode ?? null;

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

  const pageState: DataState = useMemo(() => {
    if (isLoading) {
      return 'loading';
    }
    if (isError) {
      return 'error';
    }
    if (explainability?.state.status === 'error') {
      return 'error';
    }
    if (explainability?.state.status === 'empty' || !sales || sales.series.length === 0) {
      return 'empty';
    }
    if (explainability?.state.status === 'degraded') {
      return 'degraded';
    }
    return 'ready';
  }, [explainability?.state.status, isError, isLoading, sales]);

  const emptyDescription = user?.role === 'admin'
    ? 'Добавьте данные продаж и закупок или обновите начальную историю на странице импорта.'
    : 'Аналитика появится автоматически после обновления данных администратором.';
  const degradedDescription = explainability?.state.reason
    || (user?.role === 'admin'
      ? 'Часть контекста недоступна. Проверьте импорт/обновление источников.'
      : 'Часть контекста недоступна. Используйте аналитику как ориентир до обновления данных.');

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

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="h4" fontWeight={700}>
          Аналитика продаж
        </Typography>
        <Typography color="text.secondary">
          Что произошло, почему это важно и насколько данным можно доверять.
        </Typography>
        <FreshnessBadgeGroup
          dataFreshness={dataFreshness}
          modelFreshness={modelFreshness}
          newsFreshness={newsFreshness}
          showFallback={false}
        />
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

      <DataStatePanel
        state={pageState}
        emptyTitle="Нет данных продаж за выбранный период"
        emptyDescription={emptyDescription}
        degradedTitle="Контекст частично ограничен"
        degradedDescription={degradedDescription}
        errorMessage="Не удалось загрузить аналитику продаж. Проверьте backend и повторите запрос."
        onRetry={() => {
          void salesQuery.refetch();
          void anomaliesQuery.refetch();
        }}
        actionLabel={user?.role === 'admin' ? 'Перейти к импорту' : undefined}
        onAction={user?.role === 'admin' ? () => navigate('/import') : undefined}
      >
        {sales ? (
          <>
            <SalesTrendChart
              series={sales.series}
              state={pageState === 'ready' ? 'ready' : pageState}
              annotations={explainability?.chart.annotations}
              overlays={explainability?.chart.overlays}
              dataFreshness={dataFreshness}
              providerMode={explainability?.trust.mode ?? null}
              emptyTitle="Нет точек для графика спроса"
              emptyDescription={explainability?.state.reason ?? 'Измените фильтры периода и продукта.'}
              degradedTitle="Часть внешних индикаторов недоступна"
              degradedDescription={degradedDescription}
              onRetry={() => {
                void salesQuery.refetch();
                void anomaliesQuery.refetch();
              }}
              actionLabel={user?.role === 'admin' ? 'Обновить данные импорта' : undefined}
              onAction={user?.role === 'admin' ? () => navigate('/import') : undefined}
            />

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 7 }}>
                <SeasonalityPanel seasonality={sales.seasonality} />
              </Grid>
              <Grid size={{ xs: 12, md: 5 }}>
                <ComparisonsPanel
                  comparisons={sales.comparisons}
                  dataMode={explainability?.trust.data_mode ?? null}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 12 }}>
                <BusinessSummaryCard summary={explainability?.summary} />
              </Grid>
            </Grid>

            <SalesAnomalyTable
              anomalies={anomalies}
              supportingRefs={explainability?.chart.supporting_refs}
              onOpenDetails={handleOpenAnomaly}
            />
          </>
        ) : null}
      </DataStatePanel>
    </Stack>
  );
}

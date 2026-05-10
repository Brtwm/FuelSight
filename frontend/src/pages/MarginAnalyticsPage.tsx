import { Grid, Skeleton, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  BusinessSummaryCard,
  DataStatePanel,
  ExternalContextPanel,
  FreshnessBadgeGroup,
  PageHeader,
  isVerifiedLocalExternalContext,
  type DataState,
} from '../components/common';
import { useAuth } from '../features/auth/AuthProvider';
import {
  buildDefaultDateRange,
  resolveAnalyticsFilters,
  toSearchParams,
} from '../features/analytics/urlFilters';
import { AnomalyJournal } from '../features/margin/components/AnomalyJournal';
import { LowMarginTable } from '../features/margin/components/LowMarginTable';
import { MarginFilterBar } from '../features/margin/components/MarginFilterBar';
import { PossibleReasonsPanel } from '../features/margin/components/PossibleReasonsPanel';
import { PriceVsMarginChart } from '../features/margin/components/PriceVsMarginChart';
import { fetchAnalyticsAnomalies, fetchMarginAnalyticsWithMeta } from '../lib/api/analytics';
import { DEFAULT_PRODUCT } from '../lib/config/env';
import type { AnalyticsUrlFilters } from '../features/analytics/urlFilters';
import type { AnalyticsAnomaly } from '../lib/api/analytics.types';

const severityRank: Record<AnalyticsAnomaly['severity'], number> = {
  high: 3,
  medium: 2,
  low: 1,
};

export function MarginAnalyticsPage() {
  const navigate = useNavigate();
  const { authFetch, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedDateState, setSelectedDateState] = useState<{
    filterKey: string;
    date: string | null;
  } | null>(null);

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

  const marginQuery = useQuery({
    queryKey: ['analytics', 'margin', filters],
    queryFn: () =>
      fetchMarginAnalyticsWithMeta(authFetch, {
        product_code: filters.product_code,
        date_from: filters.date_from,
        date_to: filters.date_to,
        granularity: filters.granularity,
      }),
  });

  const anomaliesQuery = useQuery({
    queryKey: ['analytics', 'anomalies', 'margin-combined', filters],
    queryFn: async () => {
      const [marginAnomalies, purchaseAnomalies] = await Promise.all([
        fetchAnalyticsAnomalies(authFetch, {
          metric: 'margin',
          product_code: filters.product_code,
          date_from: filters.date_from,
          date_to: filters.date_to,
        }),
        fetchAnalyticsAnomalies(authFetch, {
          metric: 'purchase_price',
          product_code: filters.product_code,
          date_from: filters.date_from,
          date_to: filters.date_to,
        }),
      ]);
      return [...marginAnomalies, ...purchaseAnomalies].sort((a, b) => {
        if (a.date === b.date) {
          return severityRank[b.severity] - severityRank[a.severity];
        }
        return a.date < b.date ? 1 : -1;
      });
    },
  });

  const isLoading = marginQuery.isLoading || anomaliesQuery.isLoading;
  const isError = marginQuery.isError || anomaliesQuery.isError;
  const margin = marginQuery.data?.data ?? null;
  const marginMeta = marginQuery.data?.meta;
  const explainability = marginMeta?.explainability;
  const externalContext = explainability?.trust.external_context ?? null;
  const verifiedLocalContext = isVerifiedLocalExternalContext(externalContext);
  const anomalies = anomaliesQuery.data ?? [];
  const filterKey = `${filters.product_code}|${filters.date_from}|${filters.date_to}|${filters.granularity}`;
  const selectedDate = selectedDateState?.filterKey === filterKey ? selectedDateState.date : null;
  const effectiveSelectedDate = selectedDate ?? margin?.low_margin_days?.[0]?.date ?? null;

  const dataFreshness = explainability?.trust?.data_freshness ?? null;
  const modelFreshness = null;
  const newsFreshness = null;

  const selectedAnomaly =
    anomalies.find((item) => item.date === effectiveSelectedDate)
    ?? anomalies[0]
    ?? null;
  const supportingRefs = (() => {
    const refs = explainability?.chart.supporting_refs ?? [];
    if (!effectiveSelectedDate) {
      return refs;
    }
    const filtered = refs.filter((item) => item.ref_id.includes(effectiveSelectedDate));
    return filtered.length > 0 ? filtered : refs;
  })();

  const updateFilters = (patch: Partial<AnalyticsUrlFilters>) => {
    const next = { ...filters, ...patch };
    setSearchParams(toSearchParams(next));
  };

  const handleSelectAnomaly = (item: AnalyticsAnomaly) => {
    setSelectedDateState({ filterKey, date: item.date });
    const nextSearch = toSearchParams(filters);
    navigate(`${item.target_path}?${nextSearch.toString()}`, { replace: true });
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
    if (explainability?.state.status === 'empty' || !margin || margin.series.length === 0) {
      return 'empty';
    }
    if (explainability?.state.status === 'degraded' && !verifiedLocalContext) {
      return 'degraded';
    }
    return 'ready';
  }, [explainability?.state.status, isError, isLoading, margin, verifiedLocalContext]);

  const emptyDescription = user?.role === 'admin'
    ? 'Добавьте данные закупок и продаж или обновите начальную историю на странице импорта.'
    : 'Аналитика маржи появится автоматически после обновления данных администратором.';
  const degradedDescription = explainability?.state.reason
    || (user?.role === 'admin'
      ? 'Часть закупочного контекста недоступна. Проверьте свежесть импорта.'
      : 'Часть закупочного контекста недоступна. Интерпретируйте маржу аккуратно до обновления данных.');

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          Закупки и маржа
        </Typography>
        <Skeleton variant="rounded" height={72} />
        <Skeleton variant="rounded" height={340} />
        <Skeleton variant="rounded" height={220} />
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Закупки и маржа"
        description="Что произошло с маржой, почему это важно и насколько данным можно доверять."
        badgeSlot={(
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={modelFreshness}
            newsFreshness={newsFreshness}
            showFallback={false}
          />
        )}
      />

      <MarginFilterBar
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
        emptyTitle="Нет данных по марже за выбранный период"
        emptyDescription={emptyDescription}
        degradedTitle="Контекст маржи частично ограничен"
        degradedDescription={degradedDescription}
        errorMessage="Не удалось загрузить аналитику маржи. Проверьте сервер приложения и повторите запрос."
        onRetry={() => {
          void marginQuery.refetch();
          void anomaliesQuery.refetch();
        }}
        actionLabel={user?.role === 'admin' ? 'Перейти к импорту' : undefined}
        onAction={user?.role === 'admin' ? () => navigate('/import') : undefined}
      >
        {margin ? (
          <>
            <PriceVsMarginChart
              series={margin.series}
              thresholdRubPerLiter={margin.threshold_rub_per_liter}
              state={pageState === 'ready' ? 'ready' : pageState}
              annotations={explainability?.chart.annotations}
              overlays={explainability?.chart.overlays}
              highlightDate={effectiveSelectedDate}
              dataFreshness={dataFreshness}
              providerMode={explainability?.trust.mode ?? null}
              emptyTitle="Нет точек для графика маржи"
              emptyDescription={explainability?.state.reason ?? 'Измените фильтры периода и продукта.'}
              degradedTitle="Часть закупочных/внешних данных недоступна"
              degradedDescription={degradedDescription}
              onRetry={() => {
                void marginQuery.refetch();
                void anomaliesQuery.refetch();
              }}
              actionLabel={user?.role === 'admin' ? 'Обновить данные импорта' : undefined}
              onAction={user?.role === 'admin' ? () => navigate('/import') : undefined}
            />

            <BusinessSummaryCard summary={explainability?.summary} />
            <ExternalContextPanel
              context={externalContext}
              title="Контекст внешних сигналов"
            />

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 5 }}>
                <LowMarginTable
                  days={margin.low_margin_days}
                  onSelectDay={(value) => setSelectedDateState({ filterKey, date: value })}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 7 }}>
                <AnomalyJournal anomalies={anomalies} onSelectAnomaly={handleSelectAnomaly} />
              </Grid>
            </Grid>

            <PossibleReasonsPanel
              anomaly={selectedAnomaly}
              thresholds={explainability?.chart.thresholds}
              supportingRefs={supportingRefs}
            />
          </>
        ) : null}
      </DataStatePanel>
    </Stack>
  );
}

import { Alert, Button, Card, CardContent, Grid, Skeleton, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppShellSlots } from '../app/layout/AppShellSlotsContext';
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
import {
  fetchAnalyticsAnomalies,
  fetchMarginAnalyticsWithMeta,
} from '../lib/api/analytics';
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
  const { patchSlots } = useAppShellSlots();
  const { authFetch } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnalyticsAnomaly | null>(null);

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
  const anomalies = anomaliesQuery.data ?? [];
  const dataFreshness = marginMeta?.data_freshness ?? null;
  const modelFreshness = marginMeta?.model_freshness ?? null;
  const llmMode = marginMeta?.llm_mode ?? null;
  const newsFreshness = marginMeta?.news_freshness ?? null;
  const externalIndicatorsMode = marginMeta?.external_indicators_mode ?? null;

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

  const handleSelectAnomaly = (item: AnalyticsAnomaly) => {
    setSelectedAnomaly(item);
    setSelectedDate(item.date);
    const nextSearch = toSearchParams(filters);
    navigate(`${item.target_path}?${nextSearch.toString()}`, { replace: true });
  };

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

  if (isError) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          Закупки и маржа
        </Typography>
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                void marginQuery.refetch();
                void anomaliesQuery.refetch();
              }}
            >
              Повторить
            </Button>
          }
        >
          Не удалось загрузить аналитику маржи. Проверьте backend и повторите запрос.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="h4" fontWeight={700}>
          Закупки и маржа
        </Typography>
        <Typography color="text.secondary">
          Сравнение цен, динамики маржи и аномальных событий закупки.
        </Typography>
      </Stack>

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

      {!margin || margin.series.length === 0 ? (
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>
                Нет данных по марже за выбранный период
              </Typography>
              <Typography color="text.secondary">
                Добавьте данные закупок и продаж или обновите начальную историю на странице импорта.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/import')}>
                Перейти к импорту
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ) : (
        <>
          <PriceVsMarginChart series={margin.series} highlightDate={selectedDate} />

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 5 }}>
              <LowMarginTable
                days={margin.low_margin_days}
                onSelectDay={(value) => setSelectedDate(value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 7 }}>
              <AnomalyJournal anomalies={anomalies} onSelectAnomaly={handleSelectAnomaly} />
            </Grid>
          </Grid>

          <PossibleReasonsPanel anomaly={selectedAnomaly ?? anomalies[0] ?? null} />
        </>
      )}
    </Stack>
  );
}


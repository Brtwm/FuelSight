import AccountBalanceWalletOutlinedIcon from '@mui/icons-material/AccountBalanceWalletOutlined';
import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
import ReceiptLongOutlinedIcon from '@mui/icons-material/ReceiptLongOutlined';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import TrendingDownOutlinedIcon from '@mui/icons-material/TrendingDownOutlined';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import {
  Alert,
  Grid,
  MenuItem,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  BusinessSummaryCard,
  ChipToggleGroup,
  DataStatePanel,
  ExternalContextPanel,
  FilterPanel,
  FreshnessBadgeGroup,
  MetricCard,
  PageHeader,
  isVerifiedLocalExternalContext,
  type DataState,
} from '../components/common';
import { useAuth } from '../features/auth/AuthProvider';
import { canAccessPath } from '../features/auth/access';
import { AlertFeed } from '../features/kpi/components/AlertFeed';
import { DemandSnapshotChart } from '../features/kpi/components/DemandSnapshotChart';
import { KpiSummaryCards } from '../features/kpi/components/KpiSummaryCards';
import { formatLiters, formatPercent, formatRub, toIsoDateInput } from '../features/kpi/formatters';
import { PurchaseImportErrorControl } from '../features/import/components/PurchaseImportErrorControl';
import {
  fetchKpiAlerts,
  fetchKpiSnapshotWithMeta,
  fetchKpiSummaryWithMeta,
} from '../lib/api/kpi';
import { fetchImportJobs } from '../lib/api/import';
import { getSectionErrorMessage } from '../lib/api/errorMessages';
import { DEFAULT_DATE_TO } from '../lib/config/env';
import type { KpiFilters } from '../lib/api/kpi.types';
import type { KpiSummary } from '../lib/api/kpi.types';

const PRODUCT_OPTIONS = ['', 'AI_92', 'AI_95', 'DT_S', 'DT_W'] as const;

function buildDefaultRange() {
  const dateTo = /^\d{4}-\d{2}-\d{2}$/.test(DEFAULT_DATE_TO)
    ? new Date(`${DEFAULT_DATE_TO}T00:00:00.000`)
    : new Date();
  const dateFrom = new Date(dateTo);
  dateFrom.setDate(dateTo.getDate() - 29);
  return { dateFrom: toIsoDateInput(dateFrom), dateTo: toIsoDateInput(dateTo) };
}

function readDateValue(value: string | null, fallback: string): string {
  if (!value) {
    return fallback;
  }
  const isIsoDate = /^\d{4}-\d{2}-\d{2}$/.test(value);
  return isIsoDate ? value : fallback;
}

function buildDashboardSearchParams(filters: KpiFilters): URLSearchParams {
  const search = new URLSearchParams();
  if (filters.date_from) {
    search.set('date_from', filters.date_from);
  }
  if (filters.date_to) {
    search.set('date_to', filters.date_to);
  }
  if (filters.product_code) {
    search.set('product_code', filters.product_code);
  }
  return search;
}

function AccountingSummaryCards({ summary, onOpenMargin }: { summary: KpiSummary; onOpenMargin?: () => void }) {
  const calculatedCost = summary.revenue_rub - summary.gross_margin_rub;

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Выручка"
          value={formatRub(summary.revenue_rub)}
          helper="Продажная стоимость за период"
          icon={<ReceiptLongOutlinedIcon color="success" />}
          tone="revenue"
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Расчетная себестоимость"
          value={formatRub(calculatedCost)}
          helper="Выручка минус валовая маржа"
          icon={<AccountBalanceWalletOutlinedIcon color="primary" />}
          tone="volume"
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Валовая маржа"
          value={formatRub(summary.gross_margin_rub)}
          helper={formatPercent(summary.gross_margin_pct)}
          icon={<TrendingDownOutlinedIcon color="warning" />}
          tone="margin"
          onClick={onOpenMargin}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Низкомаржинальные позиции"
          value={`${summary.low_margin_days}`}
          helper={`алертов всего: ${summary.anomaly_count}`}
          icon={<WarningAmberOutlinedIcon color="error" />}
          tone="risk"
          onClick={onOpenMargin}
        />
      </Grid>
    </Grid>
  );
}

function SalesSummaryCards({
  summary,
  alertCount,
  onOpenSales,
  onOpenForecast,
}: {
  summary: KpiSummary;
  alertCount: number;
  onOpenSales?: () => void;
  onOpenForecast?: () => void;
}) {
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Объем продаж"
          value={formatLiters(summary.sales_volume_liters)}
          helper="Реализация за выбранный период"
          icon={<AssessmentOutlinedIcon color="primary" />}
          tone="volume"
          onClick={onOpenSales}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Выручка"
          value={formatRub(summary.revenue_rub)}
          helper="Расчет по данным реализации"
          icon={<ReceiptLongOutlinedIcon color="success" />}
          tone="revenue"
          onClick={onOpenSales}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Аномалии продаж"
          value={`${alertCount}`}
          helper="Рост или снижение спроса"
          icon={<WarningAmberOutlinedIcon color="warning" />}
          tone="risk"
          onClick={onOpenSales}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Прогноз спроса"
          value="Открыть"
          helper="Ожидаемые объемы реализации"
          icon={<TimelineOutlinedIcon color="primary" />}
          tone="volume"
          onClick={onOpenForecast}
        />
      </Grid>
    </Grid>
  );
}

export function DashboardPage() {
  const theme = useTheme();
  const isMobileReadingOrder = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const { authFetch, user } = useAuth();
  const isAccounting = user?.role === 'accounting';
  const isSales = user?.role === 'sales';
  const [searchParams, setSearchParams] = useSearchParams();
  const defaults = useMemo(() => buildDefaultRange(), []);

  const filters: KpiFilters = useMemo(
    () => ({
      date_from: readDateValue(searchParams.get('date_from'), defaults.dateFrom),
      date_to: readDateValue(searchParams.get('date_to'), defaults.dateTo),
      product_code: searchParams.get('product_code') || undefined,
    }),
    [defaults.dateFrom, defaults.dateTo, searchParams],
  );

  useEffect(() => {
    const normalized = buildDashboardSearchParams(filters).toString();
    if (normalized !== searchParams.toString()) {
      setSearchParams(buildDashboardSearchParams(filters), { replace: true });
    }
  }, [filters, searchParams, setSearchParams]);

  const summaryQuery = useQuery({
    queryKey: ['kpi', 'summary', filters],
    queryFn: () => fetchKpiSummaryWithMeta(authFetch, filters),
  });

  const alertsQuery = useQuery({
    queryKey: ['kpi', 'alerts', filters],
    queryFn: () => fetchKpiAlerts(authFetch, filters),
  });

  const snapshotQuery = useQuery({
    queryKey: ['kpi', 'snapshot', filters],
    queryFn: () => fetchKpiSnapshotWithMeta(authFetch, filters),
  });

  const purchaseImportJobsQuery = useQuery({
    queryKey: ['import', 'jobs', 'purchases', 'dashboard'],
    queryFn: () => fetchImportJobs(authFetch, {
      entity_type: 'purchases',
      limit: 10,
    }),
    enabled: isAccounting,
  });

  const isLoading = summaryQuery.isLoading || alertsQuery.isLoading || snapshotQuery.isLoading;
  const isError = summaryQuery.isError || alertsQuery.isError || snapshotQuery.isError;
  const summary = summaryQuery.data?.data ?? null;
  const summaryMeta = summaryQuery.data?.meta;
  const alerts = Array.isArray(alertsQuery.data) ? alertsQuery.data : [];
  const visibleAlerts = alerts.filter((item) => canAccessPath(user?.role, item.target_path));
  const snapshot = snapshotQuery.data?.data ?? [];
  const snapshotMeta = snapshotQuery.data?.meta;

  const summaryExplainability = summaryMeta?.explainability;
  const snapshotExplainability = snapshotMeta?.explainability;
  const explainability = summaryExplainability ?? snapshotExplainability ?? null;
  const explainabilityState = explainability?.state?.status ?? 'ready';
  const explainabilityReason = explainability?.state?.reason ?? null;

  const dataFreshness =
    summaryExplainability?.trust?.data_freshness
    ?? snapshotExplainability?.trust?.data_freshness
    ?? null;
  const modelFreshness = null;
  const newsFreshness = null;
  const externalContext =
    snapshotExplainability?.trust?.external_context
    ?? summaryExplainability?.trust?.external_context
    ?? null;
  const verifiedLocalContext = isVerifiedLocalExternalContext(externalContext);

  const pageState: DataState = useMemo(() => {
    if (isLoading) {
      return 'loading';
    }
    if (isError) {
      return 'error';
    }
    if (explainabilityState === 'error') {
      return 'error';
    }
    if (explainabilityState === 'empty' || !summary) {
      return 'empty';
    }
    if (explainabilityState === 'degraded' && !verifiedLocalContext) {
      return 'degraded';
    }
    return 'ready';
  }, [explainabilityState, isError, isLoading, summary, verifiedLocalContext]);

  const chartState: DataState = useMemo(() => {
    if (pageState === 'error' || pageState === 'loading') {
      return pageState;
    }
    if (snapshotExplainability?.state?.status === 'degraded' && !verifiedLocalContext) {
      return 'degraded';
    }
    if (snapshotExplainability?.state?.status === 'empty' || snapshot.length === 0) {
      return 'empty';
    }
    return 'ready';
  }, [pageState, snapshot.length, snapshotExplainability?.state?.status, verifiedLocalContext]);

  const emptyDescription = user?.role === 'admin'
    ? 'Чтобы увидеть KPI и динамику, загрузите продажи/закупки или выполните обновление начальной истории.'
    : isSales
      ? 'Данные реализации за выбранный период пока недоступны. Загрузите файл продаж или измените фильтры.'
      : 'Данные за выбранный период пока недоступны. После обновления данных администратором обзор KPI появится автоматически.';
  const degradedDescription = explainabilityReason
    || (user?.role === 'admin'
      ? 'Часть данных устарела или неполна. Проверьте импорт и обновите историю.'
      : 'Часть данных устарела или неполна. Аналитику можно использовать как ориентир до обновления.');
  const errorMessage = getSectionErrorMessage(
    [summaryQuery.error, alertsQuery.error, snapshotQuery.error],
    'Не удалось загрузить KPI и алерты. Проверьте сервер приложения и попробуйте снова.',
  );

  const navigateIfAllowed = (path: string) => {
    if (canAccessPath(user?.role, path)) {
      navigate(path);
    }
  };
  const importActionPath = isSales ? '/import/sales' : user?.role === 'admin' ? '/import' : null;

  const dateFrom = filters.date_from ?? defaults.dateFrom;
  const dateTo = filters.date_to ?? defaults.dateTo;
  const productCode = filters.product_code ?? '';

  const updateFilters = (patch: Partial<KpiFilters>) => {
    const resolvedProduct = patch.product_code ?? (productCode || undefined);
    const next: KpiFilters = {
      date_from: patch.date_from ?? dateFrom,
      date_to: patch.date_to ?? dateTo,
      product_code: resolvedProduct,
    };
    setSearchParams(buildDashboardSearchParams(next));
  };

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          KPI Dashboard
        </Typography>
        <Skeleton variant="rounded" height={120} />
        <Skeleton variant="rounded" height={320} />
        <Skeleton variant="rounded" height={220} />
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        title={isAccounting ? 'Финансовый обзор' : isSales ? 'Продажи' : 'KPI за период'}
        description={
          isAccounting
            ? 'Бухгалтерия контролирует закупочные данные, себестоимость, валовую маржу и ошибки импорта закупок'
            : isSales
              ? 'Раздел помогает отделу продаж отслеживать реализацию нефтепродуктов, видеть изменение спроса и быстро переходить к прогнозу.'
              : 'Краткий бизнес-обзор продаж, маржи и рисков по выбранному периоду.'
        }
        badgeSlot={(
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={modelFreshness}
            newsFreshness={newsFreshness}
            showFallback={false}
          />
        )}
      />

      <FilterPanel>
        <Grid container spacing={1.5}>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              label="Дата начала"
              type="date"
              value={dateFrom}
              InputLabelProps={{ shrink: true }}
              onChange={(event) => updateFilters({ date_from: event.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              label="Дата окончания"
              type="date"
              value={dateTo}
              InputLabelProps={{ shrink: true }}
              onChange={(event) => updateFilters({ date_to: event.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            {isMobileReadingOrder ? (
              <ChipToggleGroup
                label="Продукт"
                value={productCode}
                options={PRODUCT_OPTIONS.map((item) => ({
                  label: item || 'Все',
                  value: item,
                }))}
                onChange={(value) => updateFilters({ product_code: value || undefined })}
              />
            ) : (
              <TextField
                fullWidth
                label="Продукт"
                select
                value={productCode}
                onChange={(event) => updateFilters({ product_code: event.target.value || undefined })}
              >
                <MenuItem value="">Все продукты</MenuItem>
                {PRODUCT_OPTIONS.filter((item) => item).map((item) => (
                  <MenuItem key={item} value={item}>
                    {item}
                  </MenuItem>
                ))}
              </TextField>
            )}
          </Grid>
        </Grid>
      </FilterPanel>

      <DataStatePanel
        state={pageState}
        emptyTitle="Пока нет данных для KPI"
        emptyDescription={emptyDescription}
        degradedTitle="Данные частично ограничены"
        degradedDescription={degradedDescription}
        errorMessage={errorMessage}
        onRetry={() => {
          void summaryQuery.refetch();
          void alertsQuery.refetch();
          void snapshotQuery.refetch();
        }}
        actionLabel={importActionPath ? (isSales ? 'Перейти к импорту продаж' : 'Перейти к импорту') : undefined}
        onAction={importActionPath ? () => navigate(importActionPath) : undefined}
      >
        {summary ? (
          <>
            {visibleAlerts.some((item) => item.severity === 'high') ? (
              <Alert severity="warning">
                В периоде есть критические алерты. Проверьте детали на страницах аналитики.
              </Alert>
            ) : null}

            {isAccounting ? (
              <AccountingSummaryCards
                summary={summary}
                onOpenMargin={
                  canAccessPath(user?.role, '/analytics/margin')
                    ? () => navigate('/analytics/margin')
                    : undefined
                }
              />
            ) : isSales ? (
              <SalesSummaryCards
                summary={summary}
                alertCount={visibleAlerts.length}
                onOpenSales={
                  canAccessPath(user?.role, '/analytics/sales')
                    ? () => navigate('/analytics/sales')
                    : undefined
                }
                onOpenForecast={
                  canAccessPath(user?.role, '/forecast')
                    ? () => navigate('/forecast')
                    : undefined
                }
              />
            ) : (
              <KpiSummaryCards
                summary={summary}
                onOpenSales={
                  canAccessPath(user?.role, '/analytics/sales')
                    ? () => navigate('/analytics/sales')
                    : undefined
                }
                onOpenMargin={
                  canAccessPath(user?.role, '/analytics/margin')
                    ? () => navigate('/analytics/margin')
                    : undefined
                }
              />
            )}

            {isSales && summary.low_margin_days > 0 ? (
              <Alert severity="info">
                Есть позиции с пониженной маржинальностью, требуется согласование цены/объема с финансовым контуром.
              </Alert>
            ) : null}

            {isMobileReadingOrder ? (
              <Stack spacing={2}>
                {isAccounting ? (
                  <PurchaseImportErrorControl
                    jobs={purchaseImportJobsQuery.data ?? []}
                    loading={purchaseImportJobsQuery.isLoading}
                    isError={purchaseImportJobsQuery.isError}
                  />
                ) : isSales ? (
                  <ExternalContextPanel
                    context={externalContext}
                    title="Контекст спроса"
                  />
                ) : (
                  <>
                    <BusinessSummaryCard summary={summaryExplainability?.summary ?? snapshotExplainability?.summary} />
                    <ExternalContextPanel
                      context={externalContext}
                      title="Контекст внешних сигналов"
                    />
                  </>
                )}
                <AlertFeed
                  alerts={visibleAlerts}
                  onOpenAlert={(alert) => {
                    const search = new URLSearchParams({
                      product_code: alert.product_code,
                      date_from: dateFrom,
                      date_to: dateTo,
                    });
                    navigateIfAllowed(`${alert.target_path}?${search.toString()}`);
                  }}
                />
                {isAccounting ? null : (
                  <DemandSnapshotChart
                    points={snapshot}
                    state={chartState}
                    annotations={snapshotExplainability?.chart.annotations}
                    overlays={snapshotExplainability?.chart.overlays}
                    dataFreshness={dataFreshness}
                    providerMode={snapshotExplainability?.trust.mode ?? null}
                    emptyTitle="Нет динамики спроса"
                    emptyDescription={snapshotExplainability?.state.reason ?? 'Измените фильтры периода и продукта.'}
                  />
                )}
              </Stack>
            ) : (
              <Grid container spacing={2}>
                {isAccounting ? (
                  <Grid size={{ xs: 12, lg: 8 }}>
                    <PurchaseImportErrorControl
                      jobs={purchaseImportJobsQuery.data ?? []}
                      loading={purchaseImportJobsQuery.isLoading}
                      isError={purchaseImportJobsQuery.isError}
                    />
                  </Grid>
                ) : (
                  <Grid size={{ xs: 12, lg: 8 }}>
                    <DemandSnapshotChart
                      points={snapshot}
                      state={chartState}
                      annotations={snapshotExplainability?.chart.annotations}
                      overlays={snapshotExplainability?.chart.overlays}
                      dataFreshness={dataFreshness}
                      providerMode={snapshotExplainability?.trust.mode ?? null}
                      emptyTitle="Нет динамики спроса"
                      emptyDescription={snapshotExplainability?.state.reason ?? 'Измените фильтры периода и продукта.'}
                    />
                  </Grid>
                )}
                <Grid size={{ xs: 12, lg: 4 }}>
                  <Stack spacing={2}>
                    {isAccounting ? null : (
                      isSales ? (
                        <ExternalContextPanel
                          context={externalContext}
                          title="Контекст спроса"
                        />
                      ) : (
                        <>
                        <BusinessSummaryCard summary={summaryExplainability?.summary ?? snapshotExplainability?.summary} />
                        <ExternalContextPanel
                          context={externalContext}
                          title="Контекст внешних сигналов"
                        />
                        </>
                      )
                    )}
                    <AlertFeed
                      alerts={visibleAlerts}
                      onOpenAlert={(alert) => {
                        const search = new URLSearchParams({
                          product_code: alert.product_code,
                          date_from: dateFrom,
                          date_to: dateTo,
                        });
                        navigateIfAllowed(`${alert.target_path}?${search.toString()}`);
                      }}
                    />
                  </Stack>
                </Grid>
              </Grid>
            )}
          </>
        ) : null}
      </DataStatePanel>
    </Stack>
  );
}

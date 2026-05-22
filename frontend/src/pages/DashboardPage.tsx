import AccountBalanceWalletOutlinedIcon from '@mui/icons-material/AccountBalanceWalletOutlined';
import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
import InsertChartOutlinedIcon from '@mui/icons-material/InsertChartOutlined';
import ReceiptLongOutlinedIcon from '@mui/icons-material/ReceiptLongOutlined';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import TrendingDownOutlinedIcon from '@mui/icons-material/TrendingDownOutlined';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useQuery } from '@tanstack/react-query';
import type { ReactNode } from 'react';
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
import { canAccessPath, isKnownUserRole } from '../features/auth/access';
import { AlertFeed } from '../features/kpi/components/AlertFeed';
import { DemandSnapshotChart } from '../features/kpi/components/DemandSnapshotChart';
import { KpiSummaryCards } from '../features/kpi/components/KpiSummaryCards';
import { formatLiters, formatPercent, formatRub, toIsoDateInput } from '../features/kpi/formatters';
import { PurchaseImportErrorControl } from '../features/import/components/PurchaseImportErrorControl';
import { checkBackendHealth, type HealthData } from '../lib/api/client';
import { fetchLatestForecastWithMeta } from '../lib/api/forecast';
import { fetchImportJobs } from '../lib/api/import';
import { fetchKpiAlerts, fetchKpiSnapshotWithMeta, fetchKpiSummaryWithMeta } from '../lib/api/kpi';
import { fetchLatestNewsDigestWithMeta } from '../lib/api/news';
import { getSectionErrorMessage } from '../lib/api/errorMessages';
import { DEFAULT_DATE_TO, DEFAULT_PRODUCT } from '../lib/config/env';
import { formatImportDisplayLabel } from '../lib/display/importDisplayLabel';
import type { UserRole } from '../lib/api/auth.types';
import type { ForecastData } from '../lib/api/forecast.types';
import type { ImportJob, ImportJobStatus } from '../lib/api/import.types';
import type { KpiFilters, KpiSummary } from '../lib/api/kpi.types';
import type { NewsDigestData } from '../lib/api/news.types';

const PRODUCT_OPTIONS = ['', 'AI_92', 'AI_95', 'DT_S', 'DT_W'] as const;

type DashboardQuickAction = {
  label: string;
  path: string;
  variant?: 'contained' | 'outlined';
};

type DashboardRoleConfig = {
  title: string;
  description: string;
  quickActions: DashboardQuickAction[];
  emptyAction?: DashboardQuickAction;
  showBusinessSummary: boolean;
  showDemandChart: boolean;
  showExternalContext: boolean;
  showForecastSummary: boolean;
  showNewsSummary: boolean;
  showRecentImports: boolean;
  showSystemStatus: boolean;
  importEntityType?: 'sales' | 'purchases';
  recentImportsTitle?: string;
};

const DASHBOARD_ROLE_CONFIG: Record<UserRole, DashboardRoleConfig> = {
  admin: {
    title: 'Технический обзор системы',
    description:
      'Администратор сопровождает систему, demo/debug-контур, качество данных и состояние сервисов.',
    quickActions: [
      { label: 'Импорт данных', path: '/import/sales', variant: 'outlined' },
      { label: 'Сгенерировать демо-историю', path: '/import/history', variant: 'contained' },
    ],
    emptyAction: { label: 'Перейти к импорту', path: '/import/sales' },
    showBusinessSummary: true,
    showDemandChart: true,
    showExternalContext: true,
    showForecastSummary: false,
    showNewsSummary: false,
    showRecentImports: true,
    showSystemStatus: true,
    recentImportsTitle: 'Последние импорты',
  },
  sales: {
    title: 'Обзор отдела продаж',
    description:
      'Раздел помогает отслеживать реализацию, выручку, спрос по продуктам и прогноз спроса.',
    quickActions: [
      { label: 'Импорт продаж', path: '/import/sales', variant: 'contained' },
      { label: 'Аналитика продаж', path: '/analytics/sales', variant: 'outlined' },
      { label: 'Прогноз спроса', path: '/forecast', variant: 'outlined' },
    ],
    emptyAction: { label: 'Перейти к импорту продаж', path: '/import/sales' },
    showBusinessSummary: false,
    showDemandChart: true,
    showExternalContext: true,
    showForecastSummary: true,
    showNewsSummary: false,
    showRecentImports: true,
    showSystemStatus: false,
    importEntityType: 'sales',
    recentImportsTitle: 'Последние импорты продаж',
  },
  accounting: {
    title: 'Финансовый обзор',
    description:
      'Бухгалтерия контролирует закупочную стоимость, себестоимость, валовую маржу и низкомаржинальные позиции.',
    quickActions: [
      { label: 'Импорт закупок', path: '/import/purchases', variant: 'contained' },
      { label: 'Аналитика маржи', path: '/analytics/margin', variant: 'outlined' },
    ],
    emptyAction: { label: 'Перейти к импорту закупок', path: '/import/purchases' },
    showBusinessSummary: false,
    showDemandChart: false,
    showExternalContext: false,
    showForecastSummary: false,
    showNewsSummary: false,
    showRecentImports: true,
    showSystemStatus: false,
    importEntityType: 'purchases',
    recentImportsTitle: 'Последние импорты закупок',
  },
  analyst: {
    title: 'Аналитический обзор',
    description:
      'Аналитик видит полную картину по продажам, марже, прогнозам, аномалиям и рыночному контексту.',
    quickActions: [
      { label: 'Аналитика продаж', path: '/analytics/sales', variant: 'outlined' },
      { label: 'Аналитика маржи', path: '/analytics/margin', variant: 'outlined' },
      { label: 'Прогноз спроса', path: '/forecast', variant: 'outlined' },
      { label: 'Новости и RAG-чат', path: '/news', variant: 'outlined' },
      { label: 'Управленческий отчет', path: '/reports/executive', variant: 'outlined' },
    ],
    showBusinessSummary: true,
    showDemandChart: true,
    showExternalContext: true,
    showForecastSummary: true,
    showNewsSummary: true,
    showRecentImports: false,
    showSystemStatus: false,
  },
  director: {
    title: 'Управленческая сводка',
    description:
      'Директор видит итоговые KPI, прогноз, риски и может сформировать управленческий отчет.',
    quickActions: [
      { label: 'Риски маржи', path: '/analytics/margin', variant: 'outlined' },
      { label: 'Сводка прогноза', path: '/forecast', variant: 'outlined' },
      { label: 'Новостная сводка', path: '/news', variant: 'outlined' },
    ],
    showBusinessSummary: true,
    showDemandChart: false,
    showExternalContext: false,
    showForecastSummary: true,
    showNewsSummary: true,
    showRecentImports: false,
    showSystemStatus: false,
  },
};

const statusLabel: Record<ImportJobStatus, string> = {
  queued: 'В очереди',
  processing: 'Обрабатывается',
  completed: 'Завершено',
  completed_with_errors: 'Завершено с ошибками',
  failed: 'Ошибка',
};

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

function formatDateTime(value: string | null): string {
  if (!value) {
    return '—';
  }
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatForecastTotal(forecast: ForecastData): string {
  const total = forecast.forecast_points.reduce((sum, point) => sum + point.y_hat, 0);
  return formatLiters(total);
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

function DirectorSummaryCards({
  summary,
  alertCount,
  onOpenMargin,
}: {
  summary: KpiSummary;
  alertCount: number;
  onOpenMargin?: () => void;
}) {
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Выручка"
          value={formatRub(summary.revenue_rub)}
          helper="Итоговая выручка за период"
          icon={<ReceiptLongOutlinedIcon color="success" />}
          tone="revenue"
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
        <MetricCard
          label="Объем продаж"
          value={formatLiters(summary.sales_volume_liters)}
          helper="Реализация нефтепродуктов"
          icon={<AssessmentOutlinedIcon color="primary" />}
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
          label="Риски"
          value={`${alertCount}`}
          helper={`низкая маржа: ${summary.low_margin_days}`}
          icon={<WarningAmberOutlinedIcon color="error" />}
          tone="risk"
          onClick={onOpenMargin}
        />
      </Grid>
    </Grid>
  );
}

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1.25}>
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

function DashboardQuickActions({
  actions,
  onNavigate,
}: {
  actions: DashboardQuickAction[];
  onNavigate: (path: string) => void;
}) {
  if (actions.length === 0) {
    return null;
  }

  return (
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} useFlexGap flexWrap="wrap">
      {actions.map((action) => (
        <Button
          key={`${action.path}-${action.label}`}
          variant={action.variant ?? 'outlined'}
          startIcon={<InsertChartOutlinedIcon fontSize="small" />}
          onClick={() => onNavigate(action.path)}
          sx={{ width: { xs: '100%', sm: 'auto' }, textTransform: 'none' }}
        >
          {action.label}
        </Button>
      ))}
    </Stack>
  );
}

function SystemStatusPanel({
  health,
  loading,
  isError,
  warningLines,
}: {
  health: HealthData | undefined;
  loading: boolean;
  isError: boolean;
  warningLines: string[];
}) {
  return (
    <SectionCard title="Статус системы">
      {loading ? <Typography color="text.secondary">Проверяем состояние backend...</Typography> : null}
      {isError ? <Alert severity="error">Не удалось получить health/status backend.</Alert> : null}
      {!loading && !isError && health ? (
        <Stack spacing={1}>
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            <Chip color={health.ok ? 'success' : 'error'} label={health.ok ? 'API доступен' : 'API требует внимания'} />
            <Chip variant="outlined" label={`Окружение: ${health.app_env}`} />
            <Chip variant="outlined" label={`Версия: ${health.version}`} />
            {health.llm_active?.mode ? <Chip variant="outlined" label={`LLM: ${health.llm_active.mode}`} /> : null}
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Новости: {health.news_provider ?? 'не настроено'}; внешние индикаторы: {health.external_indicators_mode ?? 'не настроено'}.
          </Typography>
        </Stack>
      ) : null}
      {!loading && !isError && !health ? (
        <Alert severity="info">Служебный статус пока недоступен.</Alert>
      ) : null}
      {warningLines.length > 0 ? (
        <Stack spacing={0.75}>
          <Divider />
          {warningLines.map((line) => (
            <Alert key={line} severity="warning">
              {line}
            </Alert>
          ))}
        </Stack>
      ) : null}
    </SectionCard>
  );
}

function RecentImportJobsPanel({
  title,
  jobs,
  loading,
  isError,
}: {
  title: string;
  jobs: ImportJob[];
  loading: boolean;
  isError: boolean;
}) {
  return (
    <SectionCard title={title}>
      {loading ? <Typography color="text.secondary">Загружаем историю импортов...</Typography> : null}
      {isError ? <Alert severity="error">Не удалось загрузить последние импорты.</Alert> : null}
      {!loading && !isError && jobs.length === 0 ? (
        <Alert severity="info">История импортов пока пуста.</Alert>
      ) : null}
      {!loading && !isError && jobs.length > 0 ? (
        <List disablePadding>
          {jobs.slice(0, 5).map((job, index) => (
            <div key={job.id}>
              <ListItem disableGutters>
                <ListItemText
                  primary={job.file_name ?? formatImportDisplayLabel(job.display_label, job.entity_type)}
                  secondary={`${formatImportDisplayLabel(job.display_label, job.entity_type)} · ${statusLabel[job.status]} · ${formatDateTime(job.started_at)}`}
                />
                {job.quality_status ? <Chip size="small" label={job.quality_status} /> : null}
              </ListItem>
              {index < jobs.slice(0, 5).length - 1 ? <Divider component="li" /> : null}
            </div>
          ))}
        </List>
      ) : null}
    </SectionCard>
  );
}

function ForecastSummaryPanel({
  forecast,
  loading,
  isError,
}: {
  forecast: ForecastData | null | undefined;
  loading: boolean;
  isError: boolean;
}) {
  return (
    <SectionCard title="Прогноз спроса">
      {loading ? <Typography color="text.secondary">Загружаем сохраненный прогноз...</Typography> : null}
      {isError ? <Alert severity="error">Не удалось загрузить прогноз спроса.</Alert> : null}
      {!loading && !isError && !forecast ? (
        <Alert severity="info">Сохраненный прогноз спроса пока недоступен.</Alert>
      ) : null}
      {!loading && !isError && forecast ? (
        <Stack spacing={1}>
          <Typography fontWeight={700}>
            {forecast.product_code}: {formatForecastTotal(forecast)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Горизонт: {forecast.horizon_days} дн.; модель: {forecast.model_type}; статус: {forecast.model_status}.
          </Typography>
          {forecast.drivers.length > 0 ? (
            <Typography variant="body2" color="text.secondary">
              Факторы: {forecast.drivers.slice(0, 3).join(', ')}
            </Typography>
          ) : null}
        </Stack>
      ) : null}
    </SectionCard>
  );
}

function NewsSummaryPanel({
  digest,
  loading,
  isError,
}: {
  digest: NewsDigestData | null | undefined;
  loading: boolean;
  isError: boolean;
}) {
  return (
    <SectionCard title="Рыночный контекст">
      {loading ? <Typography color="text.secondary">Загружаем новостную сводку...</Typography> : null}
      {isError ? <Alert severity="error">Не удалось загрузить рыночный контекст.</Alert> : null}
      {!loading && !isError && !digest ? (
        <Alert severity="info">Новостная сводка пока недоступна.</Alert>
      ) : null}
      {!loading && !isError && digest ? (
        <Stack spacing={1}>
          <Typography>{digest.summary_text}</Typography>
          {digest.bullet_points.slice(0, 3).map((point) => (
            <Typography key={point} variant="body2" color="text.secondary">
              • {point}
            </Typography>
          ))}
        </Stack>
      ) : null}
    </SectionCard>
  );
}

export function DashboardPage() {
  const theme = useTheme();
  const isMobileReadingOrder = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const { authFetch, user } = useAuth();
  const role = isKnownUserRole(user?.role) ? user.role : null;
  const config = role ? DASHBOARD_ROLE_CONFIG[role] : null;
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
    enabled: Boolean(role),
  });

  const alertsQuery = useQuery({
    queryKey: ['kpi', 'alerts', filters],
    queryFn: () => fetchKpiAlerts(authFetch, filters),
    enabled: Boolean(role),
  });

  const snapshotQuery = useQuery({
    queryKey: ['kpi', 'snapshot', filters],
    queryFn: () => fetchKpiSnapshotWithMeta(authFetch, filters),
    enabled: Boolean(role),
  });

  const importJobsQuery = useQuery({
    queryKey: ['import', 'jobs', 'dashboard', config?.importEntityType ?? 'all'],
    queryFn: () => fetchImportJobs(authFetch, {
      entity_type: config?.importEntityType,
      limit: 5,
    }),
    enabled: Boolean(config?.showRecentImports),
  });

  const healthQuery = useQuery({
    queryKey: ['backend-health', 'dashboard'],
    queryFn: checkBackendHealth,
    enabled: Boolean(config?.showSystemStatus),
  });

  const forecastQuery = useQuery({
    queryKey: ['forecast', 'latest', 'dashboard', DEFAULT_PRODUCT, 7],
    queryFn: () => fetchLatestForecastWithMeta(authFetch, {
      product_code: DEFAULT_PRODUCT,
      horizon_days: 7,
    }),
    enabled: Boolean(config?.showForecastSummary && role && canAccessPath(role, '/forecast')),
  });

  const newsQuery = useQuery({
    queryKey: ['news', 'digest', 'dashboard', 'weekly'],
    queryFn: () => fetchLatestNewsDigestWithMeta(authFetch, 'weekly'),
    enabled: Boolean(config?.showNewsSummary && role && canAccessPath(role, '/news')),
  });

  const isLoading = summaryQuery.isLoading || alertsQuery.isLoading || snapshotQuery.isLoading;
  const isError = summaryQuery.isError || alertsQuery.isError || snapshotQuery.isError;
  const summary = summaryQuery.data?.data ?? null;
  const summaryMeta = summaryQuery.data?.meta;
  const alerts = Array.isArray(alertsQuery.data) ? alertsQuery.data : [];
  const visibleAlerts = alerts.filter((item) => canAccessPath(role, item.target_path));
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
  const modelFreshness = forecastQuery.data?.meta?.model_freshness ?? null;
  const newsFreshness = newsQuery.data?.meta?.news_freshness ?? newsQuery.data?.data?.news_freshness ?? null;
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

  const navigateIfAllowed = (path: string) => {
    if (canAccessPath(role, path)) {
      navigate(path);
    }
  };

  const quickActions = useMemo(
    () => (config?.quickActions ?? []).filter((action) => canAccessPath(role, action.path)),
    [config?.quickActions, role],
  );
  const reportActionVisible = role === 'director' && canAccessPath(role, '/reports/executive');
  const emptyAction = config?.emptyAction && canAccessPath(role, config.emptyAction.path)
    ? config.emptyAction
    : undefined;

  const emptyDescription = role === 'admin'
    ? 'Чтобы увидеть KPI и динамику, загрузите продажи/закупки или выполните обновление начальной истории.'
    : role === 'sales'
      ? 'Данные реализации за выбранный период пока недоступны. Загрузите файл продаж или измените фильтры.'
      : role === 'accounting'
        ? 'Данные закупок и маржи за выбранный период пока недоступны. Загрузите файл закупок или измените фильтры.'
        : 'Данные за выбранный период пока недоступны. После обновления данных обзор KPI появится автоматически.';
  const degradedDescription = explainabilityReason
    || (role === 'admin'
      ? 'Часть данных устарела или неполна. Проверьте импорт и обновите историю.'
      : 'Часть данных устарела или неполна. Аналитику можно использовать как ориентир до обновления.');
  const errorMessage = getSectionErrorMessage(
    [summaryQuery.error, alertsQuery.error, snapshotQuery.error],
    'Не удалось загрузить KPI и алерты. Проверьте сервер приложения и попробуйте снова.',
  );

  const technicalWarningLines = [
    explainabilityReason ? `KPI: ${explainabilityReason}` : null,
    importJobsQuery.data?.some((job) => job.status === 'failed' || job.status === 'completed_with_errors')
      ? 'В последних импортах есть операции с ошибками.'
      : null,
  ].filter((item): item is string => Boolean(item));

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

  if (!role || !config) {
    return (
      <Stack spacing={3}>
        <PageHeader
          title="Доступ ограничен"
          description="Для текущей роли dashboard недоступен. Обратитесь к администратору системы."
        />
        <Alert severity="error">У вашей роли нет доступа к этому разделу.</Alert>
      </Stack>
    );
  }

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          {config.title}
        </Typography>
        <Skeleton variant="rounded" height={120} />
        <Skeleton variant="rounded" height={320} />
        <Skeleton variant="rounded" height={220} />
      </Stack>
    );
  }

  const renderSummaryCards = () => {
    if (!summary) {
      return null;
    }
    if (role === 'accounting') {
      return (
        <AccountingSummaryCards
          summary={summary}
          onOpenMargin={
            canAccessPath(role, '/analytics/margin')
              ? () => navigate('/analytics/margin')
              : undefined
          }
        />
      );
    }
    if (role === 'sales') {
      return (
        <SalesSummaryCards
          summary={summary}
          alertCount={visibleAlerts.length}
          onOpenSales={
            canAccessPath(role, '/analytics/sales')
              ? () => navigate('/analytics/sales')
              : undefined
          }
          onOpenForecast={
            canAccessPath(role, '/forecast')
              ? () => navigate('/forecast')
              : undefined
          }
        />
      );
    }
    if (role === 'director') {
      return (
        <DirectorSummaryCards
          summary={summary}
          alertCount={visibleAlerts.length}
          onOpenMargin={
            canAccessPath(role, '/analytics/margin')
              ? () => navigate('/analytics/margin')
              : undefined
          }
        />
      );
    }
    return (
      <KpiSummaryCards
        summary={summary}
        onOpenSales={
          canAccessPath(role, '/analytics/sales')
            ? () => navigate('/analytics/sales')
            : undefined
        }
        onOpenMargin={
          canAccessPath(role, '/analytics/margin')
            ? () => navigate('/analytics/margin')
            : undefined
        }
      />
    );
  };

  const rolePanels = (
    <>
      {config.showSystemStatus ? (
        <SystemStatusPanel
          health={healthQuery.data}
          loading={healthQuery.isLoading}
          isError={healthQuery.isError}
          warningLines={technicalWarningLines}
        />
      ) : null}
      {config.showRecentImports ? (
        <RecentImportJobsPanel
          title={config.recentImportsTitle ?? 'Последние импорты'}
          jobs={importJobsQuery.data ?? []}
          loading={importJobsQuery.isLoading}
          isError={importJobsQuery.isError}
        />
      ) : null}
      {role === 'accounting' ? (
        <PurchaseImportErrorControl
          jobs={importJobsQuery.data ?? []}
          loading={importJobsQuery.isLoading}
          isError={importJobsQuery.isError}
        />
      ) : null}
      {config.showBusinessSummary ? (
        <BusinessSummaryCard
          summary={summaryExplainability?.summary ?? snapshotExplainability?.summary}
          title={role === 'director' ? 'Executive summary' : 'Бизнес-резюме'}
        />
      ) : null}
      {config.showForecastSummary ? (
        <ForecastSummaryPanel
          forecast={forecastQuery.data?.data}
          loading={forecastQuery.isLoading}
          isError={forecastQuery.isError}
        />
      ) : null}
      {config.showNewsSummary ? (
        <NewsSummaryPanel
          digest={newsQuery.data?.data}
          loading={newsQuery.isLoading}
          isError={newsQuery.isError}
        />
      ) : null}
      {config.showExternalContext ? (
        <ExternalContextPanel
          context={externalContext}
          title={role === 'sales' ? 'Контекст спроса' : 'Контекст внешних сигналов'}
        />
      ) : null}
    </>
  );

  return (
    <Stack spacing={3}>
      <PageHeader
        title={config.title}
        description={config.description}
        badgeSlot={(
          <FreshnessBadgeGroup
            dataFreshness={dataFreshness}
            modelFreshness={modelFreshness}
            newsFreshness={newsFreshness}
            showFallback={false}
          />
        )}
        actionSlot={reportActionVisible ? (
          <Button
            variant="contained"
            startIcon={<InsertChartOutlinedIcon fontSize="small" />}
            onClick={() => navigate('/reports/executive')}
            sx={{ width: { xs: '100%', md: 'auto' }, textTransform: 'none' }}
          >
            Сформировать отчет
          </Button>
        ) : undefined}
      />

      <DashboardQuickActions actions={quickActions} onNavigate={navigateIfAllowed} />

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
        actionLabel={emptyAction?.label}
        onAction={emptyAction ? () => navigate(emptyAction.path) : undefined}
      >
        {summary ? (
          <Stack spacing={2}>
            {visibleAlerts.some((item) => item.severity === 'high') ? (
              <Alert severity="warning">
                В периоде есть критические алерты. Проверьте детали на страницах аналитики.
              </Alert>
            ) : null}

            {renderSummaryCards()}

            {role === 'sales' && summary.low_margin_days > 0 ? (
              <Alert severity="info">
                Есть позиции с пониженной маржинальностью, требуется согласование цены/объема с финансовым контуром.
              </Alert>
            ) : null}

            {role === 'director' && visibleAlerts.length > 0 ? (
              <Alert severity="warning">
                Есть управленческие риски по марже или аномалиям. Детали доступны в разрешенных аналитических разделах.
              </Alert>
            ) : null}

            {isMobileReadingOrder ? (
              <Stack spacing={2}>
                {rolePanels}
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
                {config.showDemandChart ? (
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
                ) : null}
              </Stack>
            ) : (
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, lg: 8 }}>
                  {config.showDemandChart ? (
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
                  ) : (
                    <Stack spacing={2}>{rolePanels}</Stack>
                  )}
                </Grid>
                <Grid size={{ xs: 12, lg: 4 }}>
                  <Stack spacing={2}>
                    {config.showDemandChart ? rolePanels : null}
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
          </Stack>
        ) : null}
      </DataStatePanel>
    </Stack>
  );
}

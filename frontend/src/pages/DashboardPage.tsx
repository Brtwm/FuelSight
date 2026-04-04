import {
  Alert,
  Button,
  Card,
  CardContent,
  Grid,
  MenuItem,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthProvider';
import { AlertFeed } from '../features/kpi/components/AlertFeed';
import { DemandSnapshotChart } from '../features/kpi/components/DemandSnapshotChart';
import { KpiSummaryCards } from '../features/kpi/components/KpiSummaryCards';
import { toIsoDateInput } from '../features/kpi/formatters';
import { fetchKpiAlerts, fetchKpiSnapshot, fetchKpiSummary } from '../lib/api/kpi';
import type { KpiFilters } from '../lib/api/kpi.types';

const PRODUCT_OPTIONS = ['', 'AI_92', 'AI_95', 'DT_S', 'DT_W'] as const;

function buildDefaultRange() {
  const dateTo = new Date();
  const dateFrom = new Date(dateTo);
  dateFrom.setDate(dateTo.getDate() - 29);
  return { dateFrom: toIsoDateInput(dateFrom), dateTo: toIsoDateInput(dateTo) };
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { authFetch } = useAuth();
  const defaults = useMemo(() => buildDefaultRange(), []);
  const [dateFrom, setDateFrom] = useState(defaults.dateFrom);
  const [dateTo, setDateTo] = useState(defaults.dateTo);
  const [productCode, setProductCode] = useState<string>('');

  const filters: KpiFilters = useMemo(
    () => ({
      date_from: dateFrom,
      date_to: dateTo,
      product_code: productCode || undefined,
    }),
    [dateFrom, dateTo, productCode],
  );

  const summaryQuery = useQuery({
    queryKey: ['kpi', 'summary', filters],
    queryFn: () => fetchKpiSummary(authFetch, filters),
  });

  const alertsQuery = useQuery({
    queryKey: ['kpi', 'alerts', filters],
    queryFn: () => fetchKpiAlerts(authFetch, filters),
  });

  const snapshotQuery = useQuery({
    queryKey: ['kpi', 'snapshot', filters],
    queryFn: () => fetchKpiSnapshot(authFetch, filters),
  });

  const isLoading = summaryQuery.isLoading || alertsQuery.isLoading || snapshotQuery.isLoading;
  const isError = summaryQuery.isError || alertsQuery.isError || snapshotQuery.isError;
  const summary = summaryQuery.data;
  const alerts = alertsQuery.data ?? [];
  const snapshot = snapshotQuery.data ?? [];

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

  if (isError) {
    return (
      <Stack spacing={2}>
        <Typography variant="h4" fontWeight={700}>
          KPI Dashboard
        </Typography>
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                void summaryQuery.refetch();
                void alertsQuery.refetch();
                void snapshotQuery.refetch();
              }}
            >
              Повторить
            </Button>
          }
        >
          Не удалось загрузить KPI и алерты. Проверьте backend и попробуйте снова.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="h4" fontWeight={700}>
          KPI Dashboard
        </Typography>
        <Typography color="text.secondary">
          Краткий обзор продаж, маржи и аномалий за выбранный период.
        </Typography>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <TextField
            fullWidth
            label="Дата начала"
            type="date"
            value={dateFrom}
            InputLabelProps={{ shrink: true }}
            onChange={(event) => setDateFrom(event.target.value)}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <TextField
            fullWidth
            label="Дата окончания"
            type="date"
            value={dateTo}
            InputLabelProps={{ shrink: true }}
            onChange={(event) => setDateTo(event.target.value)}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <TextField
            fullWidth
            label="Продукт"
            select
            value={productCode}
            onChange={(event) => setProductCode(event.target.value)}
          >
            <MenuItem value="">Все продукты</MenuItem>
            {PRODUCT_OPTIONS.filter((item) => item).map((item) => (
              <MenuItem key={item} value={item}>
                {item}
              </MenuItem>
            ))}
          </TextField>
        </Grid>
      </Grid>

      {!summary ? (
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>
                Пока нет данных для KPI
              </Typography>
              <Typography color="text.secondary">
                Загрузите продажи и закупки или сгенерируйте исторические данные на странице импорта.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/import')}>
                Перейти к импорту
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ) : (
        <>
          {alerts.some((item) => item.severity === 'high') ? (
            <Alert severity="warning">
              В периоде есть критические алерты. Проверьте детали на страницах аналитики.
            </Alert>
          ) : null}

          <KpiSummaryCards
            summary={summary}
            onOpenSales={() => navigate('/analytics/sales')}
            onOpenMargin={() => navigate('/analytics/margin')}
          />

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, lg: 8 }}>
              <DemandSnapshotChart points={snapshot} />
            </Grid>
            <Grid size={{ xs: 12, lg: 4 }}>
              <AlertFeed
                alerts={alerts}
                onOpenAlert={(alert) => {
                  const search = new URLSearchParams({
                    product_code: alert.product_code,
                    date_from: dateFrom,
                    date_to: dateTo,
                  });
                  navigate(`${alert.target_path}?${search.toString()}`);
                }}
              />
            </Grid>
          </Grid>
        </>
      )}
    </Stack>
  );
}


import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { DiagnosticsDrawer, PageHeader } from '../components/common';
import { useAuth } from '../features/auth/AuthProvider';
import { GenerateHistoryDataForm } from '../features/import/components/GenerateHistoryDataForm';
import { ImportJobsTable } from '../features/import/components/ImportJobsTable';
import { ImportUploadCard } from '../features/import/components/ImportUploadCard';
import { invalidateImportCaches } from '../features/import/invalidateImportCaches';
import { ApiHttpError } from '../lib/api/http';
import { fetchImportJobs, generateHistoryData, uploadPurchasesFile, uploadSalesFile } from '../lib/api/import';
import type {
  GenerateHistoryPayload,
  ImportEntityType,
  ImportJob,
  ImportJobStatus,
} from '../lib/api/import.types';
import type { UserRole } from '../lib/api/auth.types';

const terminalStatuses: ImportJobStatus[] = ['completed', 'completed_with_errors', 'failed'];

const salesColumns = ['date', 'product_code', 'volume_liters', 'revenue_rub', 'avg_retail_price_rub'];
const purchasesColumns = [
  'date',
  'product_code',
  'volume_liters',
  'purchase_price_rub',
  'supplier_name',
  'logistics_cost_rub',
];

const provenanceLabel: Record<string, string> = {
  live: 'актуальные данные',
  cached: 'сохранённые данные',
  manual_snapshot: 'проверенный контур',
};

const qualityLabel: Record<string, string> = {
  ok: 'данные корректные',
  warning: 'нужно внимание',
  degraded: 'требует обновления',
  failed: 'ошибка',
};

const statusLabel: Record<ImportJobStatus, string> = {
  queued: 'В очереди',
  processing: 'Обрабатывается',
  completed: 'Завершено',
  completed_with_errors: 'Завершено с ошибками',
  failed: 'Ошибка',
};

type ImportTab = 'sales' | 'purchases' | 'history';

function toReadableError(error: unknown): string {
  if (error instanceof ApiHttpError) {
    if (error.code === 'validation_error') {
      return error.message || 'Ошибка валидации входных данных';
    }
    if (error.status === 403) {
      return 'У вашей роли нет доступа к этому действию импорта';
    }
    return error.message;
  }
  return 'Не удалось выполнить операцию импорта';
}

function getImportAccess(role: UserRole | undefined) {
  return {
    canUploadSales: role === 'admin' || role === 'sales',
    canUploadPurchases: role === 'admin' || role === 'accounting',
    canGenerateHistory: role === 'admin',
    canReadHistory: role === 'admin' || role === 'sales' || role === 'accounting',
    historyEntityType: role === 'sales'
      ? 'sales'
      : role === 'accounting'
        ? 'purchases'
        : undefined,
  } satisfies {
    canUploadSales: boolean;
    canUploadPurchases: boolean;
    canGenerateHistory: boolean;
    canReadHistory: boolean;
    historyEntityType?: ImportEntityType;
  };
}

function getHistoryEmptyDescription(role: UserRole | undefined): string {
  if (role === 'sales') {
    return 'История операций продаж пока пустая. Загрузите файл продаж, чтобы увидеть операции здесь.';
  }
  if (role === 'accounting') {
    return 'История операций закупок пока пустая. Загрузите файл закупок, чтобы увидеть операции здесь.';
  }
  if (role === 'analyst') {
    return 'История операций пока пустая. После загрузки данных история импортов появится здесь.';
  }
  return 'История операций пока пустая. Загрузите файл продаж/закупок или выполните обновление начальной истории.';
}

function DiagnosticsContent({ jobs, loading, isError }: { jobs: ImportJob[]; loading: boolean; isError: boolean }) {
  if (loading) {
    return <Typography color="text.secondary">Загружаем диагностику...</Typography>;
  }

  if (isError) {
    return <Alert severity="error">Не удалось загрузить диагностические данные.</Alert>;
  }

  if (jobs.length === 0) {
    return <Typography color="text.secondary">Диагностика пока недоступна: история операций пустая.</Typography>;
  }

  return (
    <Stack spacing={1.5}>
      {jobs.slice(0, 10).map((job) => (
        <Card key={job.id} variant="outlined">
          <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Stack spacing={0.75}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="subtitle2" fontWeight={700}>
                  {job.display_label ?? job.entity_type}
                </Typography>
                <Chip size="small" label={statusLabel[job.status] ?? 'Статус уточняется'} />
              </Stack>
              <Divider />
              {job.provenance_mode ? (
                <Typography variant="body2" color="text.secondary">
                  Источник: {provenanceLabel[job.provenance_mode] ?? job.provenance_mode}
                </Typography>
              ) : null}
              {job.quality_status ? (
                <Typography variant="body2" color="text.secondary">
                  Качество: {qualityLabel[job.quality_status] ?? job.quality_status}
                </Typography>
              ) : null}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

export function ImportPage() {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);

  const { authFetch, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const importAccess = useMemo(() => getImportAccess(user?.role), [user?.role]);
  const routeTab = useMemo<ImportTab>(() => {
    if (location.pathname.endsWith('/purchases')) {
      return 'purchases';
    }
    if (location.pathname.endsWith('/history')) {
      return 'history';
    }
    return 'sales';
  }, [location.pathname]);

  const visibleTabs = useMemo<ImportTab[]>(() => {
    const tabs: ImportTab[] = [];
    if (importAccess.canUploadSales) {
      tabs.push('sales');
    }
    if (importAccess.canUploadPurchases) {
      tabs.push('purchases');
    }
    if (importAccess.canReadHistory) {
      tabs.push('history');
    }
    return tabs;
  }, [importAccess.canGenerateHistory, importAccess.canReadHistory, importAccess.canUploadPurchases, importAccess.canUploadSales]);

  const effectiveTab = visibleTabs.includes(routeTab) ? routeTab : visibleTabs[0];

  const jobsQuery = useQuery({
    queryKey: ['import', 'jobs', importAccess.historyEntityType ?? 'all'],
    queryFn: () => fetchImportJobs(authFetch, {
      limit: 30,
      entity_type: importAccess.historyEntityType,
    }),
    enabled: importAccess.canReadHistory,
    refetchInterval: (query) => {
      const jobs = query.state.data ?? [];
      return jobs.some((item) => !terminalStatuses.includes(item.status)) ? 3000 : false;
    },
  });

  const uploadSalesMutation = useMutation({
    mutationFn: ({ file, sourceName }: { file: File; sourceName?: string }) =>
      uploadSalesFile(file, authFetch, sourceName),
    onSuccess: async (data) => {
      setErrorMessage(null);
      setStatusMessage(`Операция принята в обработку. Номер операции: ${data.job_id}`);
      await invalidateImportCaches(queryClient);
      await jobsQuery.refetch();
    },
    onError: (error) => {
      setStatusMessage(null);
      setErrorMessage(toReadableError(error));
    },
  });

  const uploadPurchasesMutation = useMutation({
    mutationFn: ({ file, sourceName }: { file: File; sourceName?: string }) =>
      uploadPurchasesFile(file, authFetch, sourceName),
    onSuccess: async (data) => {
      setErrorMessage(null);
      setStatusMessage(`Операция принята в обработку. Номер операции: ${data.job_id}`);
      await invalidateImportCaches(queryClient);
      await jobsQuery.refetch();
    },
    onError: (error) => {
      setStatusMessage(null);
      setErrorMessage(toReadableError(error));
    },
  });

  const generateHistoryMutation = useMutation({
    mutationFn: (payload: GenerateHistoryPayload) => generateHistoryData(payload, authFetch),
    onSuccess: async (data) => {
      setErrorMessage(null);
      setStatusMessage(`Обновление начальной истории запущено. Номер операции: ${data.job_id}`);
      await invalidateImportCaches(queryClient);
      await jobsQuery.refetch();
    },
    onError: (error) => {
      setStatusMessage(null);
      setErrorMessage(toReadableError(error));
    },
  });

  const isBusy = useMemo(
    () =>
      uploadSalesMutation.isPending ||
      uploadPurchasesMutation.isPending ||
      generateHistoryMutation.isPending,
    [generateHistoryMutation.isPending, uploadPurchasesMutation.isPending, uploadSalesMutation.isPending],
  );
  const requiredColumns = effectiveTab === 'sales' ? salesColumns : effectiveTab === 'purchases' ? purchasesColumns : [];

  if (!effectiveTab) {
    return (
      <Stack spacing={3}>
        <PageHeader
          title="Начальные данные и обновления"
          description="Управление загрузкой данных и историей операций."
        />
        <Alert severity="error">У вашей роли нет доступа к разделу импорта.</Alert>
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Начальные данные и обновления"
        description="Управляйте загрузкой продаж, закупок и обновлением начальной истории в операционном режиме."
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={1}>
        <Tabs
          value={effectiveTab}
          onChange={(_, value: ImportTab) => navigate(`/import/${value}`)}
          variant="scrollable"
        >
          {visibleTabs.includes('sales') ? <Tab label="Импорт продаж" value="sales" /> : null}
          {visibleTabs.includes('purchases') ? <Tab label="Импорт закупок" value="purchases" /> : null}
          {visibleTabs.includes('history') ? <Tab label="История импортов" value="history" /> : null}
        </Tabs>

        {importAccess.canGenerateHistory ? (
          <Button variant="outlined" onClick={() => setDiagnosticsOpen(true)}>
            Диагностика
          </Button>
        ) : null}
      </Stack>

      {statusMessage ? <Alert severity="success">{statusMessage}</Alert> : null}
      {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 8 }}>
          {effectiveTab === 'sales' && importAccess.canUploadSales ? (
            <ImportUploadCard
              entityType="sales"
              loading={isBusy}
              onSubmit={async (file, sourceName) => {
                try {
                  await uploadSalesMutation.mutateAsync({
                    file,
                    sourceName,
                  });
                } catch {
                  // Error state is handled in mutation.onError.
                }
              }}
            />
          ) : null}
          {effectiveTab === 'purchases' && importAccess.canUploadPurchases ? (
            <ImportUploadCard
              entityType="purchases"
              loading={isBusy}
              onSubmit={async (file, sourceName) => {
                try {
                  await uploadPurchasesMutation.mutateAsync({
                    file,
                    sourceName,
                  });
                } catch {
                  // Error state is handled in mutation.onError.
                }
              }}
            />
          ) : null}
          {effectiveTab === 'history' && importAccess.canGenerateHistory ? (
            <GenerateHistoryDataForm
              loading={isBusy}
              onSubmit={async (payload) => {
                try {
                  await generateHistoryMutation.mutateAsync(payload);
                } catch {
                  // Error state is handled in mutation.onError.
                }
              }}
            />
          ) : null}
          {effectiveTab === 'history' && !importAccess.canGenerateHistory ? (
            <Alert severity="info">
              Для вашей роли доступна только история операций импорта без загрузки файлов и технических действий.
            </Alert>
          ) : null}
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="h6" fontWeight={700}>
                  Операционные требования
                </Typography>
                {requiredColumns.map((columnName) => (
                  <Typography key={columnName} color="text.secondary">
                    {columnName}
                  </Typography>
                ))}
                {effectiveTab === 'history' && importAccess.canGenerateHistory ? (
                  <Typography color="text.secondary">
                    Для обновления истории используйте период от 12 месяцев и выбранные продукты AI_92/AI_95/DT.
                  </Typography>
                ) : null}
                {effectiveTab === 'history' && !importAccess.canGenerateHistory ? (
                  <Typography color="text.secondary">
                    История отфильтрована backend-правами вашей роли.
                  </Typography>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Stack spacing={1}>
        <Typography variant="h6" fontWeight={700}>
          История операций
        </Typography>
        <ImportJobsTable
          jobs={jobsQuery.data ?? []}
          loading={jobsQuery.isLoading}
          isError={jobsQuery.isError}
          emptyDescription={getHistoryEmptyDescription(user?.role)}
        />
      </Stack>

      <DiagnosticsDrawer
        open={diagnosticsOpen && importAccess.canGenerateHistory}
        onClose={() => setDiagnosticsOpen(false)}
        title="Диагностика качества и источников"
      >
        <DiagnosticsContent
          jobs={jobsQuery.data ?? []}
          loading={jobsQuery.isLoading}
          isError={jobsQuery.isError}
        />
      </DiagnosticsDrawer>
    </Stack>
  );
}

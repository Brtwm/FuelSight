import { Alert, Card, CardContent, Grid, Stack, Tab, Tabs, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useAuth } from '../features/auth/AuthProvider';
import { GenerateHistoryDataForm } from '../features/import/components/GenerateHistoryDataForm';
import { ImportJobsTable } from '../features/import/components/ImportJobsTable';
import { ImportUploadCard } from '../features/import/components/ImportUploadCard';
import { invalidateImportCaches } from '../features/import/invalidateImportCaches';
import { ApiHttpError } from '../lib/api/http';
import { fetchImportJobs, generateHistoryData, uploadPurchasesFile, uploadSalesFile } from '../lib/api/import';
import type { GenerateHistoryPayload, ImportJobStatus } from '../lib/api/import.types';

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

type ImportTab = 'sales' | 'purchases' | 'history';

function toReadableError(error: unknown): string {
  if (error instanceof ApiHttpError) {
    if (error.code === 'validation_error') {
      return error.message || 'Ошибка валидации входных данных';
    }
    if (error.status === 403) {
      return 'Доступ к импорту доступен только роли admin';
    }
    return error.message;
  }
  return 'Не удалось выполнить операцию импорта';
}

export function ImportPage() {
  const [activeTab, setActiveTab] = useState<ImportTab>('sales');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { authFetch } = useAuth();
  const queryClient = useQueryClient();

  const jobsQuery = useQuery({
    queryKey: ['import', 'jobs'],
    queryFn: () => fetchImportJobs(authFetch, { limit: 30 }),
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
      setStatusMessage(`Загрузка принята. Job: ${data.job_id}`);
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
      setStatusMessage(`Загрузка принята. Job: ${data.job_id}`);
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
      setStatusMessage(`Генерация запущена. Job: ${data.job_id}`);
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

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="h4" fontWeight={700}>
          Импорт данных
        </Typography>
        <Typography color="text.secondary">
          Загружайте продажи и закупки или сгенерируйте исторические данные для демонстрации MVP.
        </Typography>
      </Stack>

      <Tabs
        value={activeTab}
        onChange={(_, value: ImportTab) => setActiveTab(value)}
        variant="scrollable"
      >
        <Tab label="Продажи" value="sales" />
        <Tab label="Закупки" value="purchases" />
        <Tab label="Исторические данные" value="history" />
      </Tabs>

      {statusMessage ? <Alert severity="success">{statusMessage}</Alert> : null}
      {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 8 }}>
          {activeTab === 'sales' ? (
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
          {activeTab === 'purchases' ? (
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
          {activeTab === 'history' ? (
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
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="h6" fontWeight={700}>
                  Требуемые колонки
                </Typography>
                {(activeTab === 'sales' ? salesColumns : purchasesColumns).map((columnName) => (
                  <Typography key={columnName} color="text.secondary">
                    {columnName}
                  </Typography>
                ))}
                {activeTab === 'history' ? (
                  <Typography color="text.secondary">
                    Для генерации используйте период 12 месяцев (по умолчанию) и продукты AI_92/AI_95/DT.
                  </Typography>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Stack spacing={1}>
        <Typography variant="h6" fontWeight={700}>
          История импортов
        </Typography>
        <ImportJobsTable
          jobs={jobsQuery.data ?? []}
          loading={jobsQuery.isLoading}
          isError={jobsQuery.isError}
        />
      </Stack>
    </Stack>
  );
}

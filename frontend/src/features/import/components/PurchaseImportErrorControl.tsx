import { Alert, Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import type { ImportJob, ImportJobStatus } from '../../../lib/api/import.types';

const statusLabel: Record<ImportJobStatus, string> = {
  queued: 'В очереди',
  processing: 'Обрабатывается',
  completed: 'Завершено',
  completed_with_errors: 'Завершено с ошибками',
  failed: 'Ошибка',
};

const statusColor: Record<ImportJobStatus, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  queued: 'default',
  processing: 'info',
  completed: 'success',
  completed_with_errors: 'warning',
  failed: 'error',
};

const qualityLabel: Record<string, string> = {
  ok: 'Данные корректные',
  warning: 'Нужно внимание',
  degraded: 'Требует обновления',
  failed: 'Ошибка',
};

function isProblemJob(job: ImportJob): boolean {
  return (
    job.status === 'failed'
    || job.status === 'completed_with_errors'
    || job.rows_failed > 0
    || job.quality_status === 'warning'
    || job.quality_status === 'degraded'
    || job.quality_status === 'failed'
  );
}

type Props = {
  jobs: ImportJob[];
  loading?: boolean;
  isError?: boolean;
};

export function PurchaseImportErrorControl({ jobs, loading = false, isError = false }: Props) {
  const purchaseJobs = jobs.filter((job) => job.entity_type === 'purchases');
  const problemJobs = purchaseJobs.filter(isProblemJob);
  const visibleJobs = problemJobs.length > 0 ? problemJobs : purchaseJobs.slice(0, 3);

  return (
    <Card>
      <CardContent>
        <Stack spacing={1.25}>
          <Typography variant="h6" fontWeight={700}>
            Контроль ошибок импорта закупок
          </Typography>
          {loading ? (
            <Typography color="text.secondary">Загружаем статусы закупочных импортов...</Typography>
          ) : null}
          {isError ? (
            <Alert severity="error">Не удалось загрузить статусы закупочных импортов.</Alert>
          ) : null}
          {!loading && !isError && purchaseJobs.length === 0 ? (
            <Alert severity="info">История закупочных импортов пока пуста.</Alert>
          ) : null}
          {!loading && !isError && purchaseJobs.length > 0 && problemJobs.length === 0 ? (
            <Alert severity="success">Последние закупочные импорты без ошибок.</Alert>
          ) : null}
          {visibleJobs.map((job) => (
            <Card key={job.id} variant="outlined">
              <CardContent sx={{ py: 1.25, '&:last-child': { pb: 1.25 } }}>
                <Stack spacing={0.75}>
                  <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle2" fontWeight={700}>
                      {job.file_name ?? 'Файл закупок'}
                    </Typography>
                    <Chip
                      size="small"
                      color={statusColor[job.status]}
                      label={statusLabel[job.status]}
                    />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {`${job.rows_failed} строк с ошибкой`}
                  </Typography>
                  {job.quality_status ? (
                    <Typography variant="body2" color="text.secondary">
                      Качество: {qualityLabel[job.quality_status] ?? job.quality_status}
                    </Typography>
                  ) : null}
                  {job.error_report_path ? (
                    <Typography variant="body2" color="text.secondary">
                      Отчет об ошибках: {job.error_report_path}
                    </Typography>
                  ) : null}
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

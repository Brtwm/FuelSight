import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
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

function formatDateTime(value: string | null): string {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date);
}

type Props = {
  jobs: ImportJob[];
  loading: boolean;
  isError: boolean;
};

export function ImportJobsTable({ jobs, loading, isError }: Props) {
  if (loading) {
    return (
      <Paper sx={{ p: 3 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <CircularProgress size={20} />
          <Typography color="text.secondary">Загружаем историю импортов...</Typography>
        </Stack>
      </Paper>
    );
  }

  if (isError) {
    return (
      <Alert severity="error">
        Не удалось получить историю импортов. Проверьте backend и повторите попытку.
      </Alert>
    );
  }

  if (jobs.length === 0) {
    return (
      <Alert severity="info">
        История импортов пока пустая. Загрузите файл или сгенерируйте исторические данные.
      </Alert>
    );
  }

  return (
    <Paper>
      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Тип</TableCell>
              <TableCell>Файл</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Результат</TableCell>
              <TableCell>Начат</TableCell>
              <TableCell>Завершён</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {jobs.map((job) => (
              <TableRow key={job.id} hover>
                <TableCell>{job.entity_type}</TableCell>
                <TableCell>{job.file_name ?? '—'}</TableCell>
                <TableCell>
                  <Chip size="small" color={statusColor[job.status]} label={statusLabel[job.status]} />
                </TableCell>
                <TableCell>{`${job.rows_success} ok / ${job.rows_failed} fail`}</TableCell>
                <TableCell>{formatDateTime(job.started_at)}</TableCell>
                <TableCell>{formatDateTime(job.finished_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Paper>
  );
}


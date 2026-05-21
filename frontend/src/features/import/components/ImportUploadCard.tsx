import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import type { DragEvent } from 'react';
import { useRef, useState } from 'react';

type Props = {
  entityType: 'sales' | 'purchases';
  loading: boolean;
  onSubmit: (file: File, sourceName?: string) => Promise<void>;
};

const maxUploadBytes = 10 * 1024 * 1024;
const maxUploadMegabytes = maxUploadBytes / (1024 * 1024);
const supportedExtensions = ['.csv', '.xlsx'];

function validateFile(file: File): string | null {
  const normalizedName = file.name.toLowerCase();
  const hasSupportedExtension = supportedExtensions.some((extension) => normalizedName.endsWith(extension));
  if (!hasSupportedExtension) {
    return 'Поддерживаются только файлы CSV или XLSX.';
  }
  if (file.size > maxUploadBytes) {
    return `Файл больше ${maxUploadMegabytes} МБ. Разделите выгрузку или уменьшите файл.`;
  }
  return null;
}

export function ImportUploadCard({ entityType, loading, onSubmit }: Props) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const title = entityType === 'sales' ? 'Импорт продаж' : 'Импорт закупок';
  const description = entityType === 'sales'
    ? 'Загрузите файл с данными о реализации нефтепродуктов. Эти данные используются для анализа спроса, расчета выручки и построения прогноза.'
    : 'Загрузите файл с данными о закупках нефтепродуктов. Эти данные используются для расчета себестоимости, валовой маржи и контроля низкомаржинальных позиций.';

  const selectFile = (file: File | null) => {
    if (!file) {
      setSelectedFile(null);
      return;
    }
    const validationError = validateFile(file);
    if (validationError) {
      setSelectedFile(null);
      setLocalError(validationError);
      return;
    }
    setSelectedFile(file);
    setLocalError(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setLocalError('Выберите CSV/XLSX файл для загрузки');
      return;
    }
    setLocalError(null);
    await onSubmit(selectedFile, sourceName);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!loading) {
      setIsDragActive(true);
    }
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    if (loading) {
      return;
    }
    selectFile(event.dataTransfer.files?.[0] ?? null);
  };

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
          <Typography color="text.secondary">
            {description}
          </Typography>

          <Box
            onDragEnter={handleDragOver}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            sx={{
              border: '1px dashed',
              borderColor: isDragActive ? 'primary.main' : 'divider',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              bgcolor: isDragActive ? 'action.hover' : 'background.default',
              transition: 'border-color 0.16s ease, background-color 0.16s ease',
            }}
          >
            <Stack spacing={1} alignItems="center">
              <CloudUploadOutlinedIcon color="action" />
              <Typography variant="body2" color="text.secondary">
                {isDragActive ? 'Отпустите файл для выбора' : 'Перетащите файл сюда или выберите вручную'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                CSV/XLSX до {maxUploadMegabytes} МБ, до 50 000 строк
              </Typography>
              <Button
                variant="outlined"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                Выбрать файл
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx"
                hidden
                onChange={(event) => {
                  selectFile(event.target.files?.[0] ?? null);
                }}
              />
            </Stack>
          </Box>

          {selectedFile ? <Chip label={selectedFile.name} color="primary" variant="outlined" /> : null}

          <TextField
            label="Источник (опционально)"
            value={sourceName}
            onChange={(event) => setSourceName(event.target.value)}
            disabled={loading}
            helperText="Например: Операционная выгрузка март 2026"
          />

          {localError ? <Alert severity="error">{localError}</Alert> : null}

          <Button variant="contained" onClick={() => void handleSubmit()} disabled={loading}>
            {loading ? 'Идёт обработка...' : 'Загрузить'}
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}

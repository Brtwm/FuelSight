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
import { useRef, useState } from 'react';

type Props = {
  entityType: 'sales' | 'purchases';
  loading: boolean;
  onSubmit: (file: File, sourceName?: string) => Promise<void>;
};

export function ImportUploadCard({ entityType, loading, onSubmit }: Props) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const title = entityType === 'sales' ? 'Загрузка продаж' : 'Загрузка закупок';

  const handleSubmit = async () => {
    if (!selectedFile) {
      setLocalError('Выберите CSV/XLSX файл для загрузки');
      return;
    }
    setLocalError(null);
    await onSubmit(selectedFile, sourceName);
  };

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
          <Typography color="text.secondary">
            Поддерживаемые форматы: `CSV`, `XLSX`. Дубликаты будут пропущены и сохранены в отчёте ошибок.
          </Typography>

          <Box
            sx={{
              border: '1px dashed',
              borderColor: 'divider',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              bgcolor: 'background.default',
            }}
          >
            <Stack spacing={1} alignItems="center">
              <CloudUploadOutlinedIcon color="action" />
              <Typography variant="body2" color="text.secondary">
                Перетащите файл или выберите вручную
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
                  const nextFile = event.target.files?.[0] ?? null;
                  setSelectedFile(nextFile);
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

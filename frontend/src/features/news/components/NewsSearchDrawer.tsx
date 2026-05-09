import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  Link,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { SourceModeBadge } from '../../../components/common';
import type { NewsSearchItem } from '../../../lib/api/news.types';

type Props = {
  q: string;
  topic: string;
  dateFrom: string;
  dateTo: string;
  isLoading: boolean;
  hasError: boolean;
  results: NewsSearchItem[];
  onQChange: (value: string) => void;
  onTopicChange: (value: string) => void;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onRetry: () => void;
};

export function NewsSearchDrawer({
  q,
  topic,
  dateFrom,
  dateTo,
  isLoading,
  hasError,
  results,
  onQChange,
  onTopicChange,
  onDateFromChange,
  onDateToChange,
  onRetry,
}: Props) {
  const [localQ, setLocalQ] = useState(q);

  useEffect(() => {
    setLocalQ(q);
  }, [q]);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (localQ !== q) {
        onQChange(localQ);
      }
    }, 400);
    return () => clearTimeout(handler);
  }, [localQ, onQChange, q]);

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            Поиск по новостям
          </Typography>

          <Grid container spacing={1.5}>
            <Grid size={{ xs: 12, sm: 6, md: 5 }}>
              <TextField
                fullWidth
                size="small"
                label="Запрос"
                value={localQ}
                onChange={(event) => setLocalQ(event.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel id="topic-select-label">Тема</InputLabel>
                <Select
                  labelId="topic-select-label"
                  label="Тема"
                  value={topic}
                  onChange={(event) => onTopicChange(event.target.value as string)}
                >
                  <MenuItem value=""><em>Все темы</em></MenuItem>
                  <MenuItem value="logistics">Логистика</MenuItem>
                  <MenuItem value="diesel">Дизель</MenuItem>
                  <MenuItem value="gasoline">Бензин</MenuItem>
                  <MenuItem value="demand">Спрос</MenuItem>
                  <MenuItem value="fx">Валюта</MenuItem>
                  <MenuItem value="oil">Нефть</MenuItem>
                  <MenuItem value="wholesale">Опт</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <TextField
                fullWidth
                size="small"
                label="Дата с"
                type="date"
                value={dateFrom}
                InputLabelProps={{ shrink: true }}
                onChange={(event) => onDateFromChange(event.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <TextField
                fullWidth
                size="small"
                label="Дата по"
                type="date"
                value={dateTo}
                InputLabelProps={{ shrink: true }}
                onChange={(event) => onDateToChange(event.target.value)}
              />
            </Grid>
          </Grid>

          {hasError ? (
            <Alert
              severity="error"
              action={
                <Button color="inherit" size="small" onClick={onRetry}>
                  Повторить
                </Button>
              }
            >
              Ошибка поиска новостей.
            </Alert>
          ) : null}

          {!hasError && !isLoading && results.length === 0 ? (
            <Alert severity="info">По вашему запросу новости не найдены.</Alert>
          ) : null}

          {!hasError && results.length > 0 ? (
            <List dense disablePadding>
              {results.map((item) => (
                <ListItem key={item.id} disablePadding sx={{ py: 0.5 }}>
                  <ListItemText
                    primary={
                      <Stack spacing={0.75}>
                        <Link
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          underline="hover"
                          color="inherit"
                        >
                          {`${item.source_name} · ${new Date(item.published_at).toLocaleDateString('ru-RU')} · ${item.title}`}
                        </Link>
                        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                          <SourceModeBadge mode={item.provider_mode} title="Источник" compact compactTitle="Ист." />
                          {item.cached_at ? (
                            <Chip
                              size="small"
                              variant="outlined"
                              label={`Кэш: ${new Date(item.cached_at).toLocaleDateString('ru-RU')}`}
                            />
                          ) : null}
                        </Stack>
                      </Stack>
                    }
                    secondary={`${item.ref_id}${item.snippet ? ` · ${item.snippet}` : ''}`}
                  />
                </ListItem>
              ))}
            </List>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

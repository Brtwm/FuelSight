import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Link,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
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
                value={q}
                onChange={(event) => onQChange(event.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <TextField
                fullWidth
                size="small"
                label="Тема"
                value={topic}
                onChange={(event) => onTopicChange(event.target.value)}
              />
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
                          <SourceModeBadge mode={item.provider_mode} title="Источник" compact compactTitle="Mode" />
                          {item.cached_at ? (
                            <Chip
                              size="small"
                              variant="outlined"
                              label={`Cached: ${new Date(item.cached_at).toLocaleDateString('ru-RU')}`}
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

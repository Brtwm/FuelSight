import {
  Card,
  CardContent,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import type { AnalyticsAnomaly } from '../../../lib/api/analytics.types';

type Props = {
  anomalies: AnalyticsAnomaly[];
  onSelectAnomaly: (item: AnalyticsAnomaly) => void;
};

export function AnomalyJournal({ anomalies, onSelectAnomaly }: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Журнал аномалий
        </Typography>
        {anomalies.length === 0 ? (
          <Typography color="text.secondary">Аномалии по марже и закупкам не найдены.</Typography>
        ) : isCompact ? (
          <Stack spacing={1}>
            {anomalies.map((item, index) => (
              <Card
                key={`${item.date}-${item.metric}-${index}`}
                variant="outlined"
                sx={{ cursor: 'pointer' }}
                onClick={() => onSelectAnomaly(item)}
              >
                <CardContent sx={{ p: 1.25, '&:last-child': { pb: 1.25 } }}>
                  <Stack spacing={0.75}>
                    <Typography variant="body2" fontWeight={600}>
                      {new Date(item.date).toLocaleDateString('ru-RU')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.metric} / {item.severity}
                    </Typography>
                    <Divider />
                    <Typography variant="body2" color="text.secondary">
                      Факт: {new Intl.NumberFormat('ru-RU').format(item.actual_value)}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Метрика</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Факт</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {anomalies.map((item, index) => (
                <TableRow
                  key={`${item.date}-${item.metric}-${index}`}
                  hover
                  onClick={() => onSelectAnomaly(item)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{new Date(item.date).toLocaleDateString('ru-RU')}</TableCell>
                  <TableCell>{item.metric}</TableCell>
                  <TableCell>{item.severity}</TableCell>
                  <TableCell>{new Intl.NumberFormat('ru-RU').format(item.actual_value)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

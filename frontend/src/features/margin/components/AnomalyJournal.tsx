import {
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import type { AnalyticsAnomaly } from '../../../lib/api/analytics.types';

type Props = {
  anomalies: AnalyticsAnomaly[];
  onSelectAnomaly: (item: AnalyticsAnomaly) => void;
};

export function AnomalyJournal({ anomalies, onSelectAnomaly }: Props) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Журнал аномалий
        </Typography>
        {anomalies.length === 0 ? (
          <Typography color="text.secondary">Аномалии по марже и закупкам не найдены.</Typography>
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

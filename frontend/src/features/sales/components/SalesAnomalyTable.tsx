import {
  Button,
  Card,
  CardContent,
  Stack,
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
  onOpenDetails: (anomaly: AnalyticsAnomaly) => void;
};

export function SalesAnomalyTable({ anomalies, onOpenDetails }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Аномалии спроса
          </Typography>
          {anomalies.length === 0 ? (
            <Typography color="text.secondary">За выбранный период аномалий не найдено.</Typography>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Дата</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Факт</TableCell>
                  <TableCell>Действие</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {anomalies.map((item, index) => (
                  <TableRow key={`${item.date}-${item.metric}-${index}`} hover>
                    <TableCell>{new Date(item.date).toLocaleDateString('ru-RU')}</TableCell>
                    <TableCell>{item.severity}</TableCell>
                    <TableCell>{new Intl.NumberFormat('ru-RU').format(item.actual_value)}</TableCell>
                    <TableCell>
                      <Button size="small" onClick={() => onOpenDetails(item)}>
                        Открыть детали
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

import {
  Card,
  Box,
  Button,
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
import type { SupportingRef } from '../../../lib/api/common.types';

type Props = {
  anomalies: AnalyticsAnomaly[];
  supportingRefs?: SupportingRef[];
  selectedAnomaly: AnalyticsAnomaly | null;
  onOpenDetails: (anomaly: AnalyticsAnomaly) => void;
};

const severityLabel: Record<AnalyticsAnomaly['severity'], string> = {
  high: 'высокая',
  medium: 'средняя',
  low: 'низкая',
};

export function SalesAnomalyTable({
  anomalies,
  supportingRefs = [],
  selectedAnomaly,
  onOpenDetails,
}: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Аномалии продаж
          </Typography>
          {anomalies.length === 0 ? (
            <Typography color="text.secondary">За выбранный период аномалий не найдено.</Typography>
          ) : isCompact ? (
            <Stack spacing={1}>
              {anomalies.map((item, index) => (
                <Card key={`${item.date}-${item.metric}-${index}`} variant="outlined">
                  <CardContent sx={{ p: 1.25, '&:last-child': { pb: 1.25 } }}>
                    <Stack spacing={0.75}>
                      <Typography variant="body2" fontWeight={600}>
                        {new Date(item.date).toLocaleDateString('ru-RU')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Важность: {severityLabel[item.severity] ?? item.severity}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Факт: {new Intl.NumberFormat('ru-RU').format(item.actual_value)}
                      </Typography>
                      <Divider />
                      <Button size="small" onClick={() => onOpenDetails(item)}>
                        Показать причины
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              ))}
            </Stack>
        ) : (
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small" sx={{ minWidth: 520 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell>Важность</TableCell>
                    <TableCell>Факт</TableCell>
                    <TableCell>Действие</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {anomalies.map((item, index) => (
                    <TableRow key={`${item.date}-${item.metric}-${index}`} hover>
                      <TableCell>{new Date(item.date).toLocaleDateString('ru-RU')}</TableCell>
                      <TableCell>{severityLabel[item.severity] ?? item.severity}</TableCell>
                      <TableCell>{new Intl.NumberFormat('ru-RU').format(item.actual_value)}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => onOpenDetails(item)}>
                          Показать причины
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
          {selectedAnomaly ? (
            <Card variant="outlined">
              <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Stack spacing={0.75}>
                  <Typography variant="subtitle2" fontWeight={700}>
                    Причины аномалии за {new Date(selectedAnomaly.date).toLocaleDateString('ru-RU')}
                  </Typography>
                  {selectedAnomaly.possible_reasons.map((reason, index) => (
                    <Typography key={`${reason}-${index}`} variant="body2" color="text.secondary">
                      • {reason}
                    </Typography>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          ) : null}
          {supportingRefs.length > 0 ? (
            <Stack spacing={0.5} sx={{ pt: 0.5 }}>
              <Typography variant="subtitle2" fontWeight={700}>
                Что проверено
              </Typography>
              {supportingRefs.slice(0, 4).map((ref) => (
                <Typography key={ref.ref_id} variant="body2" color="text.secondary">
                  • {ref.title}
                </Typography>
              ))}
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

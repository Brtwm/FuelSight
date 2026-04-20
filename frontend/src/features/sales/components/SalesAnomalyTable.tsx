import {
  Card,
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
  onOpenDetails: (anomaly: AnalyticsAnomaly) => void;
};

export function SalesAnomalyTable({ anomalies, supportingRefs = [], onOpenDetails }: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Аномалии спроса
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
                        Severity: {item.severity}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Факт: {new Intl.NumberFormat('ru-RU').format(item.actual_value)}
                      </Typography>
                      <Divider />
                      <Button size="small" onClick={() => onOpenDetails(item)}>
                        Открыть детали
                      </Button>
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
          {supportingRefs.length > 0 ? (
            <Stack spacing={0.5} sx={{ pt: 0.5 }}>
              <Typography variant="subtitle2" fontWeight={700}>
                Supporting refs
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

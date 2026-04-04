import { Card, CardContent, Stack, Typography } from '@mui/material';
import type { SalesAnalyticsData } from '../../../lib/api/analytics.types';
import { formatPercent } from '../../kpi/formatters';

type Props = {
  comparisons: SalesAnalyticsData['comparisons'];
};

export function ComparisonsPanel({ comparisons }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Сравнение периодов
          </Typography>
          <Typography color="text.secondary">MoM: {formatPercent(comparisons.mom_pct)}</Typography>
          <Typography color="text.secondary">YoY: {formatPercent(comparisons.yoy_pct)}</Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, Stack, Typography } from '@mui/material';
import type { SalesAnalyticsData } from '../../../lib/api/analytics.types';
import { formatPercent } from '../../kpi/formatters';

type Props = {
  comparisons: SalesAnalyticsData['comparisons'];
  dataMode?: string | null;
};

export function ComparisonsPanel({ comparisons, dataMode }: Props) {
  const yoyLabel = comparisons.yoy_pct === null
    ? 'N/A (недостаточно истории)'
    : formatPercent(comparisons.yoy_pct);
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Сравнение периодов
          </Typography>
          <Typography color="text.secondary">MoM: {formatPercent(comparisons.mom_pct)}</Typography>
          <Typography color="text.secondary">YoY: {yoyLabel}</Typography>
          <Typography color="text.secondary">Режим данных: {dataMode ?? 'n/a'}</Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import type { SalesAnalyticsData } from '../../../lib/api/analytics.types';

type Props = {
  seasonality: SalesAnalyticsData['seasonality'];
};

export function SeasonalityPanel({ seasonality }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            Сезонность
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Stack spacing={0.5}>
                <Typography fontWeight={600}>По дням недели</Typography>
                {seasonality.by_weekday.length === 0 ? (
                  <Typography color="text.secondary">Недостаточно данных</Typography>
                ) : (
                  seasonality.by_weekday.map((item) => (
                    <Typography key={item.weekday} color="text.secondary">
                      {item.weekday}: {new Intl.NumberFormat('ru-RU').format(item.avg_volume_liters)} л
                    </Typography>
                  ))
                )}
              </Stack>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Stack spacing={0.5}>
                <Typography fontWeight={600}>По месяцам</Typography>
                {seasonality.by_month.length === 0 ? (
                  <Typography color="text.secondary">Недостаточно данных</Typography>
                ) : (
                  seasonality.by_month.map((item) => (
                    <Typography key={item.month} color="text.secondary">
                      {item.month}: {new Intl.NumberFormat('ru-RU').format(item.avg_volume_liters)} л
                    </Typography>
                  ))
                )}
              </Stack>
            </Grid>
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
}

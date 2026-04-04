import { Card, CardContent, Stack, Typography } from '@mui/material';
import type { AnalyticsAnomaly } from '../../../lib/api/analytics.types';

type Props = {
  anomaly: AnalyticsAnomaly | null;
};

export function PossibleReasonsPanel({ anomaly }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Возможные причины
          </Typography>
          {!anomaly ? (
            <Typography color="text.secondary">
              Выберите строку аномалии, чтобы увидеть пояснение.
            </Typography>
          ) : (
            anomaly.possible_reasons.map((reason, index) => (
              <Typography key={`${reason}-${index}`} color="text.secondary">
                • {reason}
              </Typography>
            ))
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

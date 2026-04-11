import { Card, CardContent, Stack, Typography } from '@mui/material';
import type { AnalyticsAnomaly } from '../../../lib/api/analytics.types';
import type { SupportingRef } from '../../../lib/api/common.types';

type Props = {
  anomaly: AnalyticsAnomaly | null;
  thresholdInfo?: string | null;
  supportingRefs?: SupportingRef[];
};

export function PossibleReasonsPanel({
  anomaly,
  thresholdInfo,
  supportingRefs = [],
}: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Возможные причины
          </Typography>
          {thresholdInfo ? (
            <Typography color="text.secondary">{thresholdInfo}</Typography>
          ) : null}
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
          {supportingRefs.length > 0 ? (
            <>
              <Typography variant="subtitle2" fontWeight={700} sx={{ pt: 0.5 }}>
                Supporting refs
              </Typography>
              {supportingRefs.map((ref) => (
                <Typography key={ref.ref_id} color="text.secondary" variant="body2">
                  • {ref.title}
                </Typography>
              ))}
            </>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

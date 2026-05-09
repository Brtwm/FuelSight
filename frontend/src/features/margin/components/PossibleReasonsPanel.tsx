import { Card, CardContent, Stack, Typography } from '@mui/material';
import type { AnalyticsAnomaly } from '../../../lib/api/analytics.types';
import type { ExplainabilityThreshold, SupportingRef } from '../../../lib/api/common.types';

type Props = {
  anomaly: AnalyticsAnomaly | null;
  thresholds?: ExplainabilityThreshold[];
  supportingRefs?: SupportingRef[];
};

export function PossibleReasonsPanel({
  anomaly,
  thresholds = [],
  supportingRefs = [],
}: Props) {
  const thresholdDetails = thresholds
    .map((item) => item.description || (item.value !== undefined && item.value !== null
      ? `${item.label}: ${item.value}${item.unit ? ` ${item.unit}` : ''}`
      : item.label))
    .filter(Boolean);

  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Возможные причины
          </Typography>
          {thresholdDetails.map((item, index) => (
            <Typography key={`${index}-${item}`} color="text.secondary">{item}</Typography>
          ))}
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
                Что проверено
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

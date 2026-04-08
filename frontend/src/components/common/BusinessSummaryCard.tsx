import { Card, CardContent, Stack, Typography } from '@mui/material';
import type { BusinessSummary } from '../../lib/api/common.types';

type BusinessSummaryCardProps = {
  summary: BusinessSummary | null | undefined;
  title?: string;
};

export function BusinessSummaryCard({
  summary,
  title = 'Бизнес-резюме',
}: BusinessSummaryCardProps) {
  const displayTitle = summary?.title?.trim() || title;
  const displaySummary = summary?.summary?.trim() || 'Сводка по выбранному периоду пока не сформирована.';
  const bullets = summary?.bullets ?? [];

  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            {displayTitle}
          </Typography>
          <Typography color="text.secondary">{displaySummary}</Typography>
          {bullets.map((item, index) => (
            <Typography key={`${index}-${item}`} variant="body2" color="text.secondary">
              • {item}
            </Typography>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

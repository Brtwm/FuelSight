import { Box, Card, CardActionArea, CardContent, Stack, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';

type MetricTone = 'volume' | 'revenue' | 'margin' | 'risk';

// Color mapping is now moved inside the component to use theme

type MetricCardProps = {
  label: string;
  value: string;
  helper?: string;
  icon: ReactNode;
  tone: MetricTone;
  onClick?: () => void;
};

export function MetricCard({ label, value, helper, icon, tone, onClick }: MetricCardProps) {
  const theme = useTheme();
  
  const toneColor: Record<MetricTone, string> = {
    volume: theme.palette.primary.main,
    revenue: theme.palette.warning.main,
    margin: theme.palette.success.main,
    risk: theme.palette.error.main,
  };
  const color = toneColor[tone];
  const content = (
    <CardContent sx={{ minHeight: 136 }}>
      <Stack spacing={1.25} sx={{ height: '100%' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
            {label}
          </Typography>
          <Box
            sx={{
              width: 34,
              height: 34,
              borderRadius: 1.25,
              display: 'grid',
              placeItems: 'center',
              color,
              border: `1px solid ${alpha(color, 0.26)}`,
              background: `linear-gradient(135deg, ${alpha(color, 0.14)}, ${alpha(color, 0.04)})`,
            }}
          >
            {icon}
          </Box>
        </Stack>
        <Typography
          variant="h6"
          className="numeric"
          sx={{
            color: theme.palette.text.primary,
            fontWeight: 700,
            lineHeight: 1.25,
            overflowWrap: 'anywhere',
          }}
        >
          {value}
        </Typography>
        {helper ? (
          <Typography variant="caption" color="text.secondary">
            {helper}
          </Typography>
        ) : null}
      </Stack>
    </CardContent>
  );

  return (
    <Card
      sx={{
        borderColor: alpha(color, 0.16),
        '&:hover': {
          borderColor: alpha(color, 0.3),
          boxShadow: `0 18px 48px ${alpha(color, 0.08)}`,
        },
      }}
    >
      {onClick ? <CardActionArea onClick={onClick}>{content}</CardActionArea> : content}
    </Card>
  );
}

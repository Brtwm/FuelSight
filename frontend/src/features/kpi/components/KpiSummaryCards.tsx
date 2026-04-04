import TrendingDownOutlinedIcon from '@mui/icons-material/TrendingDownOutlined';
import TrendingUpOutlinedIcon from '@mui/icons-material/TrendingUpOutlined';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import { Card, CardActionArea, CardContent, Grid, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';
import type { KpiSummary } from '../../../lib/api/kpi.types';
import { formatLiters, formatPercent, formatRub } from '../formatters';

type Props = {
  summary: KpiSummary;
  onOpenSales: () => void;
  onOpenMargin: () => void;
};

type KpiCardItem = {
  label: string;
  value: string;
  icon: ReactNode;
  onClick: () => void;
};

export function KpiSummaryCards({ summary, onOpenSales, onOpenMargin }: Props) {
  const items: KpiCardItem[] = [
    {
      label: 'Продажи',
      value: formatLiters(summary.sales_volume_liters),
      icon: <TrendingUpOutlinedIcon color="primary" />,
      onClick: onOpenSales,
    },
    {
      label: 'Выручка',
      value: formatRub(summary.revenue_rub),
      icon: <TrendingUpOutlinedIcon color="success" />,
      onClick: onOpenSales,
    },
    {
      label: 'Маржа',
      value: `${formatRub(summary.gross_margin_rub)} (${formatPercent(summary.gross_margin_pct)})`,
      icon: <TrendingDownOutlinedIcon color="warning" />,
      onClick: onOpenMargin,
    },
    {
      label: 'Алерты',
      value: `${summary.anomaly_count} / low margin: ${summary.low_margin_days}`,
      icon: <WarningAmberOutlinedIcon color="error" />,
      onClick: onOpenMargin,
    },
  ];

  return (
    <Grid container spacing={2}>
      {items.map((item) => (
        <Grid key={item.label} size={{ xs: 12, sm: 6, xl: 3 }}>
          <Card>
            <CardActionArea onClick={item.onClick}>
              <CardContent>
                <Stack spacing={1}>
                  {item.icon}
                  <Typography color="text.secondary" variant="body2">
                    {item.label}
                  </Typography>
                  <Typography variant="h6" fontWeight={700}>
                    {item.value}
                  </Typography>
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

import TrendingDownOutlinedIcon from '@mui/icons-material/TrendingDownOutlined';
import TrendingUpOutlinedIcon from '@mui/icons-material/TrendingUpOutlined';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import { Grid } from '@mui/material';
import type { ReactNode } from 'react';
import { MetricCard } from '../../../components/common';
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
  helper?: string;
  icon: ReactNode;
  tone: 'volume' | 'revenue' | 'margin' | 'risk';
  onClick: () => void;
};

export function KpiSummaryCards({ summary, onOpenSales, onOpenMargin }: Props) {
  const items: KpiCardItem[] = [
    {
      label: 'Продажи',
      value: formatLiters(summary.sales_volume_liters),
      icon: <TrendingUpOutlinedIcon color="primary" />,
      tone: 'volume',
      onClick: onOpenSales,
    },
    {
      label: 'Выручка',
      value: formatRub(summary.revenue_rub),
      icon: <TrendingUpOutlinedIcon color="success" />,
      tone: 'revenue',
      onClick: onOpenSales,
    },
    {
      label: 'Маржа',
      value: formatRub(summary.gross_margin_rub),
      helper: formatPercent(summary.gross_margin_pct),
      icon: <TrendingDownOutlinedIcon color="warning" />,
      tone: 'margin',
      onClick: onOpenMargin,
    },
    {
      label: 'Алерты',
      value: `${summary.anomaly_count}`,
      helper: `низкая маржа: ${summary.low_margin_days}`,
      icon: <WarningAmberOutlinedIcon color="error" />,
      tone: 'risk',
      onClick: onOpenMargin,
    },
  ];

  return (
    <Grid container spacing={2}>
      {items.map((item) => (
        <Grid key={item.label} size={{ xs: 12, sm: 6, xl: 3 }}>
          <MetricCard
            label={item.label}
            value={item.value}
            helper={item.helper}
            icon={item.icon}
            tone={item.tone}
            onClick={item.onClick}
          />
        </Grid>
      ))}
    </Grid>
  );
}

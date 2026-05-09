import { Grid, MenuItem, TextField } from '@mui/material';
import { FilterPanel } from '../../../components/common';
import type { AnalyticsGranularity } from '../../../lib/api/analytics.types';

const PRODUCT_OPTIONS = ['AI_92', 'AI_95', 'DT_S', 'DT_W'] as const;

type Props = {
  productCode: string;
  dateFrom: string;
  dateTo: string;
  granularity: AnalyticsGranularity;
  onProductCodeChange: (value: string) => void;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onGranularityChange: (value: AnalyticsGranularity) => void;
};

export function SalesFilterBar({
  productCode,
  dateFrom,
  dateTo,
  granularity,
  onProductCodeChange,
  onDateFromChange,
  onDateToChange,
  onGranularityChange,
}: Props) {
  return (
    <FilterPanel>
      <Grid container spacing={1.5}>
        <Grid size={{ xs: 12, md: 3 }}>
          <TextField
            fullWidth
            select
            label="Продукт"
            value={productCode}
            onChange={(event) => onProductCodeChange(event.target.value)}
          >
            {PRODUCT_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <TextField
            fullWidth
            label="Дата начала"
            type="date"
            value={dateFrom}
            InputLabelProps={{ shrink: true }}
            onChange={(event) => onDateFromChange(event.target.value)}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <TextField
            fullWidth
            label="Дата окончания"
            type="date"
            value={dateTo}
            InputLabelProps={{ shrink: true }}
            onChange={(event) => onDateToChange(event.target.value)}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <TextField
            fullWidth
            select
            label="Гранулярность"
            value={granularity}
            onChange={(event) => onGranularityChange(event.target.value as AnalyticsGranularity)}
          >
            <MenuItem value="day">День</MenuItem>
            <MenuItem value="week">Неделя</MenuItem>
            <MenuItem value="month">Месяц</MenuItem>
          </TextField>
        </Grid>
      </Grid>
    </FilterPanel>
  );
}

import type {
  SharedMeta,
} from './common.types';

export type AnalyticsGranularity = 'day' | 'week' | 'month';
export type AnalyticsMetric = 'sales' | 'margin' | 'purchase_price';
export type AnalyticsSeverity = 'high' | 'medium' | 'low';
export type AnalyticsDataMode = 'live' | 'cached' | 'degraded';

export type SalesSeriesPoint = {
  period_start: string;
  volume_liters: number;
  avg_retail_price_rub: number | null;
};

export type SalesSeasonalityWeekday = {
  weekday: string;
  avg_volume_liters: number;
};

export type SalesSeasonalityMonth = {
  month: number;
  avg_volume_liters: number;
};

export type SalesAnalyticsData = {
  product_code: string;
  granularity: AnalyticsGranularity;
  series: SalesSeriesPoint[];
  seasonality: {
    by_weekday: SalesSeasonalityWeekday[];
    by_month: SalesSeasonalityMonth[];
  };
  comparisons: {
    mom_pct: number | null;
    yoy_pct: number | null;
  };
};

export type MarginSeriesPoint = {
  period_start: string;
  avg_purchase_price_rub: number | null;
  avg_retail_price_rub: number | null;
  gross_margin_rub: number | null;
  gross_margin_rub_per_liter: number | null;
  gross_margin_pct: number | null;
  purchase_data_missing: boolean;
};

export type LowMarginDay = {
  date: string;
  gross_margin_rub_per_liter: number | null;
  purchase_data_missing: boolean;
};

export type MarginAnalyticsData = {
  product_code: string;
  granularity: AnalyticsGranularity;
  series: MarginSeriesPoint[];
  threshold_rub_per_liter: number;
  below_threshold_days: number;
  low_margin_days: LowMarginDay[];
};

export type AnalyticsAnomaly = {
  date: string;
  product_code: string;
  metric: AnalyticsMetric;
  severity: AnalyticsSeverity;
  actual_value: number;
  expected_range: [number, number] | null;
  possible_reasons: string[];
  target_path: string;
};

export type AnalyticsBaseFilters = {
  product_code: string;
  date_from?: string;
  date_to?: string;
};

export type SalesAnalyticsFilters = AnalyticsBaseFilters & {
  granularity?: AnalyticsGranularity;
};

export type MarginAnalyticsFilters = AnalyticsBaseFilters & {
  granularity?: AnalyticsGranularity;
};

export type AnalyticsAnomaliesFilters = AnalyticsBaseFilters & {
  metric: AnalyticsMetric;
};

export type SalesAnalyticsMeta = SharedMeta & {
  data_mode: AnalyticsDataMode | null;
  date_from?: string;
  date_to?: string;
  product_code?: string | null;
  granularity?: AnalyticsGranularity;
  points?: number;
  empty_state?: string;
};

export type MarginAnalyticsMeta = SharedMeta & {
  threshold_info: string | null;
  date_from?: string;
  date_to?: string;
  product_code?: string | null;
  granularity?: AnalyticsGranularity;
  points?: number;
  empty_state?: string;
};

export type AnalyticsAnomaliesMeta = SharedMeta & {
  date_from?: string;
  date_to?: string;
  product_code?: string | null;
  metric?: AnalyticsMetric;
  count?: number;
};

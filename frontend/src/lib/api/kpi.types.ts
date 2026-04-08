import type {
  BusinessSummary,
  ChartAnnotation,
  FreshnessStatus,
  ReferenceOverlay,
} from './common.types';

export type KpiSummary = {
  sales_volume_liters: number;
  revenue_rub: number;
  gross_margin_rub: number;
  gross_margin_pct: number | null;
  low_margin_days: number;
  anomaly_count: number;
};

export type KpiSummaryMeta = {
  business_summary?: BusinessSummary | null;
  data_freshness?: FreshnessStatus | null;
  margin_coverage_days?: number;
  margin_missing_days?: number;
};

export type KpiAlertSeverity = 'high' | 'medium' | 'low';
export type KpiAlertType = 'low_margin' | 'purchase_spike' | 'demand_anomaly';

export type KpiAlert = {
  type: KpiAlertType;
  severity: KpiAlertSeverity;
  date: string;
  product_code: string;
  message: string;
  metric: string;
  actual_value: number;
  expected_range: [number, number] | null;
  target_path: string;
};

export type KpiSnapshotPoint = {
  date: string;
  volume_liters: number;
  avg_retail_price_rub: number | null;
};

export type KpiSnapshotMeta = {
  business_summary?: BusinessSummary | null;
  chart_annotations?: ChartAnnotation[];
  reference_overlays?: ReferenceOverlay[];
};

export type KpiFilters = {
  date_from?: string;
  date_to?: string;
  product_code?: string;
};

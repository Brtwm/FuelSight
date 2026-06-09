import type {
  DegradationStatus,
  ExternalContextQuality,
  FreshnessStatus,
  ProviderMode,
  ReferenceOverlay,
  SharedMeta,
} from './common.types';

export type ForecastModelType = 'catboost' | 'seasonal_naive';
export type ForecastModelStatus = 'active' | 'baseline_fallback';
export type ForecastHorizonDays = 1 | 7 | 30;
export type BacktestWindowType = 'rolling' | 'expanding';

export type ForecastPoint = {
  target_date: string;
  y_hat: number;
  y_lo: number | null;
  y_hi: number | null;
};

export type ForecastScenario = {
  retail_price_delta_pct: number;
};

export type ForecastData = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  model_type: ForecastModelType;
  model_status: ForecastModelStatus;
  scenario_name: string;
  scenario_params: ForecastScenario | null;
  forecast_points: ForecastPoint[];
  base_forecast_points?: ForecastPoint[] | null;
  scenario_forecast_points?: ForecastPoint[] | null;
  drivers: string[];
  model_freshness?: FreshnessStatus | null;
  training_window?: { start_date: string; end_date: string } | null;
  baseline_comparison?: Record<string, Record<string, number>> | null;
  feature_sources?: string[] | null;
  retrain_status?: DegradationStatus | null;
  provider_mode?: ProviderMode | null;
  external_context_quality?: ExternalContextQuality | null;
  event_context?: ForecastEventContext[];
  reference_overlays?: ReferenceOverlay[];
};

export type ForecastEventContext = {
  event_code: string;
  title: string;
  start_date: string;
  end_date: string;
  pressure_score: number;
  demand_delta_pct: number;
  purchase_delta_pct: number;
  source_mode: string;
};

export type RunForecastRequest = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  scenario?: ForecastScenario;
};

export type ForecastLatestFilters = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
};

export type BacktestMetrics = {
  mae: number;
  rmse: number;
  smape: number;
};

export type ValidationStatus = 'OK' | 'LIMITED' | 'UNKNOWN';

export type ValidationPeriod = {
  start?: string | null;
  end?: string | null;
};

export type ValidationObservations = {
  total?: number | null;
  train?: number | null;
  test?: number | null;
};

export type ValidationMetricValues = {
  mae?: number | null;
  rmse?: number | null;
  smape?: number | null;
};

export type ValidationImprovement = {
  mae_pct?: number | null;
  rmse_pct?: number | null;
  smape_pct?: number | null;
};

export type ValidationMetrics = {
  catboost?: ValidationMetricValues | null;
  seasonal_naive?: ValidationMetricValues | null;
  improvement?: ValidationImprovement | null;
};

export type ValidationSeriesPoint = {
  date: string;
  actual?: number | null;
  catboost_prediction?: number | null;
  seasonal_naive_prediction?: number | null;
};

export type ValidationSummary = {
  status: ValidationStatus;
  status_reason?: string | null;
  train_period?: ValidationPeriod | null;
  test_period?: ValidationPeriod | null;
  observations?: ValidationObservations | null;
  metrics?: ValidationMetrics | null;
  series?: ValidationSeriesPoint[];
};

export type BacktestData = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  model_type: ForecastModelType;
  window_type: BacktestWindowType;
  metrics: BacktestMetrics;
  comparison: Record<string, BacktestMetrics>;
  trained_at: string;
  model_version: string | null;
  model_freshness?: FreshnessStatus | null;
  training_window?: { start_date: string; end_date: string } | null;
  baseline_comparison?: Record<string, Record<string, number>> | null;
  feature_sources?: string[] | null;
  retrain_status?: DegradationStatus | null;
  provider_mode?: ProviderMode | null;
  validation_summary?: ValidationSummary | null;
};

export type RunBacktestRequest = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  window_type?: BacktestWindowType;
};

export type ForecastMeta = SharedMeta & {
  points?: number;
  scenario_delta_pct?: number;
  forecast_date?: string;
  empty_state?: string;
  status?: string;
};

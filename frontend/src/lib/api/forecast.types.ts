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
  drivers: string[];
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

export type BacktestData = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  model_type: ForecastModelType;
  window_type: BacktestWindowType;
  metrics: BacktestMetrics;
  comparison: Record<string, BacktestMetrics>;
  trained_at: string;
  model_version: string | null;
};

export type RunBacktestRequest = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  window_type?: BacktestWindowType;
};


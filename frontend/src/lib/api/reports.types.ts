export type ExecutiveReportRequest = {
  date_from?: string;
  date_to?: string;
};

export type ExecutiveReportKpi = {
  revenue_rub: number;
  sales_volume_liters: number;
  gross_margin_rub: number;
  gross_margin_pct: number;
};

export type ExecutiveProblemProduct = {
  product_code: string;
  product_name: string;
  reason: string;
  margin_pct: number;
  recommendation: string;
};

export type ExecutiveDemandForecastItem = {
  product_code: string;
  product_name: string;
  forecast_period: string;
  forecast_volume_liters: number;
  risk_level: 'low' | 'medium' | 'high';
};

export type ExecutiveMarginRisk = {
  product_code: string;
  risk: string;
  impact: string;
  recommendation: string;
};

export type ExecutiveMarketContextItem = {
  title: string;
  summary: string;
  source?: string | null;
  published_at?: string | null;
};

export type ExecutiveDataQuality = {
  has_sales_data: boolean;
  has_purchase_data: boolean;
  has_forecast_data: boolean;
  has_news_data: boolean;
  warnings: string[];
};

export type ExecutiveReportData = {
  report_id: string;
  generated_at: string;
  period: {
    date_from: string;
    date_to: string;
  };
  executive_summary: string;
  kpi: ExecutiveReportKpi;
  problem_products: ExecutiveProblemProduct[];
  demand_forecast: ExecutiveDemandForecastItem[];
  margin_risks: ExecutiveMarginRisk[];
  market_context: ExecutiveMarketContextItem[];
  recommendations: string[];
  data_quality: ExecutiveDataQuality;
};

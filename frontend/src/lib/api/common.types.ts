export type DataProviderMode = 'live' | 'cached' | 'manual_snapshot';
export type ProviderMode = DataProviderMode | 'cloud_llm' | 'local_llm' | 'retrieval_only';

export type FreshnessStatus = 'fresh' | 'warning' | 'degraded';
export type DegradationStatus = 'ok' | 'warning' | 'degraded' | 'failed';
export type QualityStatus = 'ok' | 'warning' | 'degraded' | 'failed';

export type DisplayLabelCode = 'sales' | 'purchases' | 'initial_history';

export type BusinessSummary = {
  title?: string | null;
  summary?: string | null;
  bullets?: string[];
};

export type ChartAnnotation = {
  id: string;
  date?: string | null;
  label: string;
  severity?: string | null;
  message?: string | null;
};

export type ReferenceOverlayPoint = {
  date?: string | null;
  value?: number | null;
  label?: string | null;
};

export type ReferenceOverlay = {
  code: string;
  label: string;
  unit?: string | null;
  provider_mode?: ProviderMode | null;
  points?: ReferenceOverlayPoint[];
};

export type SharedMeta = {
  business_summary: BusinessSummary | null;
  chart_annotations: ChartAnnotation[];
  reference_overlays: ReferenceOverlay[];
  data_freshness: FreshnessStatus | null;
  model_freshness: FreshnessStatus | null;
  news_freshness: FreshnessStatus | null;
  external_indicators_mode: DataProviderMode | null;
  provider_mode: ProviderMode | null;
  llm_mode: ProviderMode | null;
  request_id?: string;
};

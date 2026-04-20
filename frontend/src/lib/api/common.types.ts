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

export type SupportingRef = {
  type: string;
  ref_id: string;
  title: string;
  provider_mode?: ProviderMode | null;
  confidence?: number | null;
  source_type?: string | null;
};

export type ExplainabilityStateStatus = 'ready' | 'empty' | 'degraded' | 'error';

export type ExplainabilityThreshold = {
  id: string;
  label: string;
  value?: number | null;
  unit?: string | null;
  severity?: string | null;
  description?: string | null;
};

export type ExplainabilityChart = {
  annotations: ChartAnnotation[];
  overlays: ReferenceOverlay[];
  thresholds: ExplainabilityThreshold[];
  supporting_refs: SupportingRef[];
};

export type ExplainabilityTrust = {
  data_freshness?: FreshnessStatus | null;
  mode?: DataProviderMode | null;
  data_mode?: string | null;
  external_context?: ExternalContextQuality | null;
};

export type ExternalContextQuality = {
  provider_mode?: DataProviderMode | null;
  coverage_ratio?: number | null;
  fallback_ratio?: number | null;
  quality_status?: QualityStatus | null;
  reasons?: string[];
  manifest_run_date?: string | null;
  source_refs?: SupportingRef[];
};

export type ExplainabilityState = {
  status: ExplainabilityStateStatus;
  reason?: string | null;
};

export type ExplainabilityPayload = {
  summary: BusinessSummary | null;
  chart: ExplainabilityChart;
  trust: ExplainabilityTrust;
  state: ExplainabilityState;
};

export type SharedMeta = {
  business_summary: BusinessSummary | null;
  chart_annotations: ChartAnnotation[];
  reference_overlays: ReferenceOverlay[];
  supporting_refs: SupportingRef[];
  data_freshness: FreshnessStatus | null;
  model_freshness: FreshnessStatus | null;
  news_freshness: FreshnessStatus | null;
  external_indicators_mode: DataProviderMode | null;
  provider_mode: ProviderMode | null;
  llm_mode: ProviderMode | null;
  external_context?: ExternalContextQuality | null;
  request_id?: string;
};

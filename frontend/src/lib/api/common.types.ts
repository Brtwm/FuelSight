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


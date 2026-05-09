import type {
  DataProviderMode,
  ExternalContextQuality,
  FreshnessStatus,
  SupportingRef,
  SharedMeta,
} from './common.types';

export type DigestPeriodType = 'daily' | 'weekly';

export type NewsDigestData = {
  digest_date: string;
  created_at?: string | null;
  period_type: DigestPeriodType;
  summary_text: string;
  bullet_points: string[];
  source_ids: string[];
  llm_mode: string;
  provider_mode?: DataProviderMode | null;
  news_freshness?: FreshnessStatus | null;
  context_story?: NewsContextStory | null;
};

export type NewsContextEvent = {
  event_code: string;
  title: string;
  start_date: string;
  end_date: string;
  pressure_score: number;
  demand_delta_pct: number;
  purchase_delta_pct: number;
  source_mode: string;
};

export type NewsContextStory = {
  window: {
    start_date: string;
    end_date: string;
  };
  external_context: ExternalContextQuality | null;
  event_context: NewsContextEvent[];
  indicator_refs: SupportingRef[];
  event_refs: SupportingRef[];
};

export type NewsSearchItem = {
  id: string;
  ref_id: string;
  source_name: string;
  provider_name?: string | null;
  published_at: string;
  title: string;
  url: string;
  snippet: string | null;
  topic_tags: string[];
  impact_hint: string | null;
  provider_mode?: DataProviderMode | null;
  confidence?: number | null;
  cached_at?: string | null;
};

export type NewsRefreshData = {
  status: string;
  imported_news_count: number;
  created_digests: number;
  provider_mode?: DataProviderMode | null;
  news_freshness?: FreshnessStatus | null;
};

export type NewsSearchFilters = {
  q?: string;
  date_from?: string;
  date_to?: string;
  topic?: string;
  limit?: number;
};

export type NewsDigestMeta = SharedMeta & {
  period_type?: DigestPeriodType;
  empty_state?: string;
};

export type NewsSearchMeta = SharedMeta & {
  count?: number;
};

export type NewsRefreshMeta = SharedMeta;

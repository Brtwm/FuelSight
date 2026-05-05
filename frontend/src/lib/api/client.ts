import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';
import type { ProviderMode } from './common.types';
import type { DataProviderMode } from './common.types';

type LlmActiveData = {
  provider: string;
  mode: ProviderMode;
  model?: string | null;
  degradation_reason?: string | null;
};

export type HealthData = {
  ok: boolean;
  app_env: string;
  version: string;
  enable_llm: boolean;
  llm_provider?: string | null;
  llm_provider_mode?: string | null;
  llm_chat_model?: string | null;
  llm_embedding_model?: string | null;
  cloud_configured?: boolean;
  fallback_available?: boolean;
  llm_active?: LlmActiveData | null;
  defense_mode?: boolean;
  defense_profile?: 'offline-safe' | 'cloud-enhanced' | string | null;
  external_indicators_mode?: DataProviderMode | null;
  news_provider?: string | null;
  timestamp: string;
};

export async function checkBackendHealth(): Promise<HealthData> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
  });

  return parseApiEnvelope<HealthData>(response);
}

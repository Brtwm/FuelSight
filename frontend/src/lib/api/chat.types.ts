import type { ProviderMode } from './common.types';

export type RetrievalScope = 'news_raw' | 'news_digests' | 'kpi' | 'analytics' | 'forecast';
export type ChatScope = 'internal_analytics' | 'news_digest' | RetrievalScope;
export type CitationType = 'news' | 'digest' | 'kpi' | 'chart' | 'forecast';
export type ChatSenderType = 'user' | 'assistant';
export type ChatAnswerMode = 'cloud_llm' | 'local_llm' | 'retrieval_only';
export type ChatVerificationStatus = 'verified' | 'repaired' | 'fallback_verified' | 'blocked';
export type ChatVerificationSeverity = 'info' | 'warning' | 'error';

export type ChatVerificationData = {
  status: ChatVerificationStatus;
  reason?: string | null;
  checked_claims: number;
  supported_claims: number;
  severity?: ChatVerificationSeverity;
  unsupported_terms?: string[];
  repair_attempted?: boolean;
};

export type ChatLlmProviderData = {
  provider: string;
  mode: ChatAnswerMode;
  model?: string | null;
  degradation_reason?: string | null;
};

export type CitationData = {
  type: CitationType;
  ref_id: string;
  title: string;
  provider_mode: ProviderMode;
  confidence: number;
  source_type: string;
  url?: string | null;
  published_at?: string | null;
  route_path?: string | null;
  snippet?: string | null;
};

export type ChatSessionData = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessageData = {
  id: string;
  sender_type: ChatSenderType;
  message_text: string;
  citations: CitationData[] | null;
  confidence?: number | null;
  verification?: ChatVerificationData | null;
  created_at: string;
};

export type ChatAnswerData = {
  answer: string;
  citations: CitationData[];
  mode: ChatAnswerMode;
  provider_mode: ProviderMode;
  confidence: number;
  verification: ChatVerificationData;
  llm_provider?: ChatLlmProviderData | null;
};

export type CreateChatSessionRequest = {
  title: string;
};

export type AskChatRequest = {
  question: string;
  context_scope: ChatScope[];
};

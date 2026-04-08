import type { ProviderMode } from './common.types';

export type ChatScope = 'internal_analytics' | 'news_digest' | 'forecast';
export type CitationType = 'news' | 'chart';
export type ChatSenderType = 'user' | 'assistant';

export type CitationData = {
  type: CitationType;
  ref_id: string;
  title: string;
  provider_mode?: ProviderMode | null;
  confidence?: number | null;
  source_type?: string | null;
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
  created_at: string;
};

export type ChatAnswerData = {
  answer: string;
  citations: CitationData[];
  mode: string;
  provider_mode?: ProviderMode | null;
};

export type CreateChatSessionRequest = {
  title: string;
};

export type AskChatRequest = {
  question: string;
  context_scope: ChatScope[];
};

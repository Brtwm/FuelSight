import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope, parseApiEnvelopeWithMeta } from './http';
import type {
  AskChatRequest,
  ChatAnswerData,
  ChatLlmProviderData,
  ChatMessageData,
  ChatSessionData,
  CreateChatSessionRequest,
} from './chat.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export async function createChatSession(
  authFetch: AuthFetch,
  payload: CreateChatSessionRequest,
): Promise<ChatSessionData> {
  const response = await authFetch(`${API_BASE_URL}/chat/sessions`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseApiEnvelope<ChatSessionData>(response);
}

export async function fetchChatMessages(
  authFetch: AuthFetch,
  sessionId: string,
): Promise<ChatMessageData[]> {
  const response = await authFetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: 'GET',
  });
  return parseApiEnvelope<ChatMessageData[]>(response);
}

export async function askChatQuestion(
  authFetch: AuthFetch,
  sessionId: string,
  payload: AskChatRequest,
): Promise<ChatAnswerData> {
  const response = await authFetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await parseApiEnvelopeWithMeta<
    ChatAnswerData,
    { llm_provider?: ChatLlmProviderData | null }
  >(response);
  return {
    ...result.data,
    llm_provider: result.meta.llm_provider ?? result.data.llm_provider ?? null,
  };
}

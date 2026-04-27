import { describe, expect, it, vi } from 'vitest';
import { askChatQuestion, createChatSession, fetchChatMessages } from './chat';

describe('chat api client', () => {
  it('creates session and fetches messages', async () => {
    const authFetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              id: 's1',
              title: 'Сессия',
              created_at: '2026-04-05T10:00:00+00:00',
              updated_at: '2026-04-05T10:00:00+00:00',
            },
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: [
              {
                id: 'm1',
                sender_type: 'assistant',
                message_text: 'Ответ',
                citations: [],
                created_at: '2026-04-05T10:01:00+00:00',
              },
            ],
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      );

    const session = await createChatSession(authFetch, { title: 'Сессия' });
    const messages = await fetchChatMessages(authFetch, session.id);

    expect(session.id).toBe('s1');
    expect(messages).toHaveLength(1);
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/chat/sessions');
    expect(String(authFetch.mock.calls[1]?.[0])).toContain('/chat/sessions/s1/messages');
  });

  it('posts question payload', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            answer: 'Ответ',
            citations: [
              {
                type: 'news',
                ref_id: 'gdelt_1',
                title: 'Новость',
                provider_mode: 'cached',
                confidence: 0.78,
                source_type: 'news_raw',
              },
            ],
            mode: 'retrieval_only',
            provider_mode: 'retrieval_only',
          },
          error: null,
          meta: {},
        }),
        { status: 200 },
      ),
    );

    const result = await askChatQuestion(authFetch, 'session-1', {
      question: 'Что с маржой?',
      context_scope: ['internal_analytics', 'news_digest'],
    });

    expect(result.mode).toBe('retrieval_only');
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/chat/sessions/session-1/messages');
    expect(String(authFetch.mock.calls[0]?.[1]?.body)).toContain('"question":"Что с маржой?"');
  });
});

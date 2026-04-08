import { describe, expect, it } from 'vitest';
import { ApiHttpError, parseApiEnvelope, parseApiEnvelopeWithMeta } from './http';

describe('parseApiEnvelope', () => {
  it('parses successful envelope', async () => {
    const response = new Response(
      JSON.stringify({
        data: { ok: true },
        error: null,
        meta: {},
      }),
      { status: 200 },
    );

    const data = await parseApiEnvelope<{ ok: boolean }>(response);
    expect(data.ok).toBe(true);
  });

  it('throws ApiHttpError for envelope error', async () => {
    const response = new Response(
      JSON.stringify({
        data: null,
        error: {
          code: 'invalid_credentials',
          message: 'Неверный email или пароль',
        },
        meta: {},
      }),
      { status: 401 },
    );

    await expect(parseApiEnvelope(response)).rejects.toBeInstanceOf(ApiHttpError);
  });

  it('parses successful envelope with meta', async () => {
    const response = new Response(
      JSON.stringify({
        data: { ok: true },
        error: null,
        meta: { request_id: 'req-1', points: 12 },
      }),
      { status: 200 },
    );

    const result = await parseApiEnvelopeWithMeta<
      { ok: boolean },
      { request_id?: string; points?: number }
    >(response);
    expect(result.data.ok).toBe(true);
    expect(result.meta.request_id).toBe('req-1');
    expect(result.meta.points).toBe(12);
  });
});

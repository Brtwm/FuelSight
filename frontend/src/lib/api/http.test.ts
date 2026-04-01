import { describe, expect, it } from 'vitest';
import { ApiHttpError, parseApiEnvelope } from './http';

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
});

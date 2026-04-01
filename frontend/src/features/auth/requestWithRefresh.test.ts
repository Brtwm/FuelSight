import { describe, expect, it, vi } from 'vitest';
import { requestWithRefresh } from './requestWithRefresh';

describe('requestWithRefresh', () => {
  it('returns first response when request is not unauthorized', async () => {
    const doFetch = vi.fn().mockResolvedValueOnce(new Response(null, { status: 200 }));
    const refreshAccessToken = vi.fn().mockResolvedValue('new-token');

    const response = await requestWithRefresh({
      input: 'https://example.com',
      accessToken: 'token',
      doFetch,
      refreshAccessToken,
    });

    expect(response.status).toBe(200);
    expect(doFetch).toHaveBeenCalledTimes(1);
    expect(refreshAccessToken).not.toHaveBeenCalled();
  });

  it('refreshes and retries once after 401', async () => {
    const doFetch = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response(null, { status: 200 }));
    const refreshAccessToken = vi.fn().mockResolvedValue('new-token');

    const response = await requestWithRefresh({
      input: 'https://example.com',
      accessToken: 'expired-token',
      doFetch,
      refreshAccessToken,
    });

    expect(response.status).toBe(200);
    expect(doFetch).toHaveBeenCalledTimes(2);
    expect(refreshAccessToken).toHaveBeenCalledTimes(1);
  });

  it('returns 401 when refresh fails', async () => {
    const doFetch = vi.fn().mockResolvedValueOnce(new Response(null, { status: 401 }));
    const refreshAccessToken = vi.fn().mockResolvedValue(null);

    const response = await requestWithRefresh({
      input: 'https://example.com',
      accessToken: 'expired-token',
      doFetch,
      refreshAccessToken,
    });

    expect(response.status).toBe(401);
    expect(doFetch).toHaveBeenCalledTimes(1);
    expect(refreshAccessToken).toHaveBeenCalledTimes(1);
  });
});

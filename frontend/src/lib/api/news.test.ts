import { describe, expect, it, vi } from 'vitest';
import { fetchLatestNewsDigest, refreshNews, searchNews } from './news';

describe('news api client', () => {
  it('fetches latest digest and supports null data', async () => {
    const authFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: null,
          error: null,
          meta: { empty_state: 'empty' },
        }),
        { status: 200 },
      ),
    );

    const digest = await fetchLatestNewsDigest(authFetch, 'daily');
    expect(digest).toBeNull();
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/news/digests/latest');
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('period_type=daily');
  });

  it('searches news and refreshes feed', async () => {
    const authFetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: [
              {
                id: 'a1',
                ref_id: 'gdelt_2026_03_24_01',
                source_name: 'GDELT',
                published_at: '2026-03-24T08:30:00+00:00',
                title: 'Логистика',
                url: 'https://example.local/news/1',
                snippet: 'snippet',
                topic_tags: ['logistics'],
                impact_hint: 'purchase_up',
              },
            ],
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: { status: 'ok', imported_news_count: 5, created_digests: 2 },
            error: null,
            meta: {},
          }),
          { status: 200 },
        ),
      );

    const rows = await searchNews(authFetch, { q: 'логистика', topic: 'diesel' });
    const refresh = await refreshNews(authFetch);

    expect(rows).toHaveLength(1);
    expect(refresh.created_digests).toBe(2);
    expect(String(authFetch.mock.calls[0]?.[0])).toContain('/news/search');
    expect(String(authFetch.mock.calls[1]?.[0])).toContain('/news/refresh');
  });
});

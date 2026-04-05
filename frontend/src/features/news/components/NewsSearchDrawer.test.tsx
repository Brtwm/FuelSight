import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { NewsSearchDrawer } from './NewsSearchDrawer';

describe('NewsSearchDrawer', () => {
  it('renders external links for news materials', () => {
    const html = renderToStaticMarkup(
      <NewsSearchDrawer
        q="логистика"
        topic="diesel"
        dateFrom="2026-03-01"
        dateTo="2026-03-30"
        isLoading={false}
        hasError={false}
        results={[
          {
            id: 'news-1',
            ref_id: 'gdelt_2026_03_24_01',
            source_name: 'GDELT',
            published_at: '2026-03-24T08:30:00+00:00',
            title: 'Логистические ограничения',
            url: 'https://example.local/news/1',
            snippet: 'Снижение поставок',
            topic_tags: ['logistics'],
            impact_hint: 'purchase_up',
          },
        ]}
        onQChange={vi.fn()}
        onTopicChange={vi.fn()}
        onDateFromChange={vi.fn()}
        onDateToChange={vi.fn()}
        onRetry={vi.fn()}
      />,
    );

    expect(html).toContain('https://example.local/news/1');
    expect(html).toContain('gdelt_2026_03_24_01');
  });
});


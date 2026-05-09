import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { NewsDigestPanel } from './NewsDigestPanel';

describe('NewsDigestPanel', () => {
  it('renders digest summary and collapsed sources action', () => {
    const html = renderToStaticMarkup(
      <NewsDigestPanel
        digest={{
          digest_date: '2026-03-28',
          created_at: '2026-03-28T09:15:00+00:00',
          period_type: 'daily',
          summary_text: 'Сводка по рынку',
          bullet_points: ['Рост спроса', 'Давление на закупку'],
          source_ids: ['gdelt_2026_03_24_01', 'gdelt_2026_03_25_02'],
          llm_mode: 'off',
        }}
        isLoading={false}
        isRefreshing={false}
        canRefresh={false}
        onRefresh={vi.fn()}
        onRetry={vi.fn()}
        onSelectSource={vi.fn()}
        hasError={false}
      />,
    );

    expect(html).toContain('Сводка по рынку');
    expect(html).toContain('Показать источники (2)');
    expect(html).not.toContain('gdelt_2026_03_24_01');
  });

  it('renders empty-state hint when digest is missing', () => {
    const html = renderToStaticMarkup(
      <NewsDigestPanel
        digest={null}
        isLoading={false}
        isRefreshing={false}
        canRefresh
        onRefresh={vi.fn()}
        onRetry={vi.fn()}
        onSelectSource={vi.fn()}
        hasError={false}
      />,
    );

    expect(html).toContain('Сводка пока отсутствует');
    expect(html).toContain('Обновить');
  });
});

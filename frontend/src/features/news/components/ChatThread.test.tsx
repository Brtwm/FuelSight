import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { ChatThread } from './ChatThread';

describe('ChatThread', () => {
  it('renders LLM off state and disables chat input', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[]}
        isLoading={false}
        isSending={false}
        isLlmEnabled={false}
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={vi.fn(async () => undefined)}
      />,
    );

    expect(html).toContain('LLM off');
    expect(html).toContain('Ваш вопрос');
    expect(html).toContain('disabled');
  });

  it('shows citations block for assistant messages', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[
          {
            id: 'm1',
            sender_type: 'assistant',
            message_text: 'Ответ с источниками',
            citations: [
              { type: 'news', ref_id: 'gdelt_2026_03_24_01', title: 'Логистические ограничения' },
              { type: 'chart', ref_id: 'analytics_margin_AI_95_latest', title: 'Динамика маржи AI_95' },
            ],
            created_at: '2026-04-05T10:01:00+00:00',
          },
        ]}
        isLoading={false}
        isSending={false}
        isLlmEnabled
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={vi.fn(async () => undefined)}
      />,
    );

    expect(html).toContain('Источники');
    expect(html).toContain('Найти в новостях');
    expect(html).toContain('analytics_margin_AI_95_latest');
  });
});


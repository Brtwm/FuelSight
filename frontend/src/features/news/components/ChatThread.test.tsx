/** @vitest-environment jsdom */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ChatThread } from './ChatThread';

const originalScrollIntoView = Element.prototype.scrollIntoView;

afterEach(() => {
  Element.prototype.scrollIntoView = originalScrollIntoView;
});

describe('ChatThread', () => {
  it('renders retrieval-only state and keeps chat input available', () => {
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

    expect(html).toContain('Ответ построен по найденным источникам без внешней генерации');
    expect(html).toContain('Ваш вопрос');
    expect(html).not.toMatch(/<input[^>]*disabled/);
  });

  it('shows cloud provider diagnostics when answer meta is available', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[]}
        isLoading={false}
        isSending={false}
        isLlmEnabled
        llmProvider={{
          provider: 'neuraldeep',
          mode: 'cloud_llm',
          model: 'gpt-oss-120b',
          degradation_reason: null,
        }}
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={vi.fn(async () => undefined)}
      />,
    );

    expect(html).not.toContain('Провайдер: neuraldeep');
    expect(html).not.toContain('gpt-oss-120b');
    expect(html).not.toContain('Облачный провайдер временно недоступен');
  });

  it('shows provider degradation warning only when generation falls back', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[]}
        isLoading={false}
        isSending={false}
        isLlmEnabled
        llmProvider={{
          provider: 'neuraldeep',
          mode: 'retrieval_only',
          model: 'gpt-oss-120b',
          degradation_reason: 'cloud_provider_unavailable',
        }}
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={vi.fn(async () => undefined)}
      />,
    );

    expect(html).toContain('Облачный провайдер временно недоступен, ответ построен по источникам');
    expect(html).not.toContain('cloud_provider_unavailable');
  });

  it('shows citations block for assistant messages', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[
          {
            id: 'm1',
            sender_type: 'assistant',
            message_text: 'Ответ с источниками',
            confidence: 0.74,
            verification: {
              status: 'repaired',
              reason: null,
              checked_claims: 2,
              supported_claims: 2,
              severity: 'warning',
              unsupported_terms: [],
              repair_attempted: true,
            },
            citations: [
              {
                type: 'news',
                ref_id: 'gdelt_2026_03_24_01',
                title: 'Логистические ограничения',
                provider_mode: 'cached',
                confidence: 0.78,
                source_type: 'news_raw',
                snippet: 'Логистические ограничения повышают риск закупочных цен.',
              },
              {
                type: 'chart',
                ref_id: 'analytics_margin_AI_95_latest',
                title: 'Динамика маржи AI_95',
                provider_mode: 'retrieval_only',
                confidence: 0.82,
                source_type: 'analytics',
              },
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
    expect(html).toContain('Ответ исправлен');
    expect(html).toContain('Уверенность: 74%');
    expect(html).toContain('Найти в новостях');
    expect(html).toContain('Уверенность источника: 78%');
    expect(html).toContain('Логистические ограничения повышают риск закупочных цен.');
    expect(html).toContain('источник: сохр.');
    expect(html).toContain('analytics_margin_AI_95_latest');
  });

  it('shows blocked uncertainty state and exposes broad retrieval scope', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[
          {
            id: 'm2',
            sender_type: 'assistant',
            message_text: 'По текущим данным недостаточно подтверждённых данных.',
            confidence: 0.12,
            verification: {
              status: 'blocked',
              reason: 'weak_evidence',
              checked_claims: 1,
              supported_claims: 0,
              severity: 'error',
              unsupported_terms: [],
              repair_attempted: false,
            },
            citations: [],
            created_at: '2026-04-05T10:01:00+00:00',
          },
        ]}
        isLoading={false}
        isSending={false}
        isLlmEnabled={false}
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={vi.fn(async () => undefined)}
      />,
    );

    expect(html).toContain('Недостаточно данных');
    expect(html).toContain('Новости');
    expect(html).toContain('Прогноз');
  });

  it('shows fallback verified status as source-grounded answer', () => {
    const html = renderToStaticMarkup(
      <ChatThread
        messages={[
          {
            id: 'assistant-3',
            sender_type: 'assistant',
            message_text: 'Ответ построен по источникам.',
            confidence: 0.81,
            verification: {
              status: 'fallback_verified',
              reason: 'unsupported_numeric_claim',
              checked_claims: 2,
              supported_claims: 1,
              severity: 'warning',
              unsupported_terms: ['1200'],
              repair_attempted: true,
            },
            citations: [],
            created_at: '2026-04-05T10:01:00+00:00',
          },
        ]}
        isLoading={false}
        isSending={false}
        isLlmEnabled
        hasError={false}
        onRetry={() => undefined}
        onNewsCitationClick={() => undefined}
        onSend={async () => undefined}
      />,
    );

    expect(html).toContain('Ответ построен по источникам');
    expect(html).toContain('Уверенность: 81%');
  });

  it('sends selected retrieval scopes with the question', async () => {
    const onSend = vi.fn(async () => undefined);

    render(
      <ChatThread
        messages={[]}
        isLoading={false}
        isSending={false}
        isLlmEnabled={false}
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={onSend}
      />,
    );

    fireEvent.click(screen.getByRole('switch', { name: 'Новости' }));
    fireEvent.change(screen.getByLabelText('Ваш вопрос'), {
      target: { value: 'Что с маржой AI_95?' },
    });
    fireEvent.click(screen.getByRole('button', { name: /отправить/i }));

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith({
        question: 'Что с маржой AI_95?',
        context_scope: ['internal_analytics', 'forecast'],
      });
    });
  });

  it('auto-scrolls when assistant messages are rendered', () => {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;

    render(
      <ChatThread
        messages={[
          {
            id: 'assistant-scroll',
            sender_type: 'assistant',
            message_text: 'Ответ с источниками.',
            confidence: 0.8,
            verification: null,
            citations: [
              {
                type: 'news',
                ref_id: 'news-scroll',
                title: 'Источник',
                provider_mode: 'cached',
                confidence: 0.8,
                source_type: 'news_raw',
              },
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

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
  });

  it('disables the input and send action while a question is being sent', () => {
    render(
      <ChatThread
        messages={[]}
        isLoading={false}
        isSending
        isLlmEnabled
        hasError={false}
        onRetry={vi.fn()}
        onNewsCitationClick={vi.fn()}
        onSend={vi.fn(async () => undefined)}
      />,
    );

    expect((screen.getByLabelText('Ваш вопрос') as HTMLInputElement).disabled).toBe(true);
    expect((screen.getByRole('button', { name: /отправить/i }) as HTMLButtonElement).disabled).toBe(true);
  });
});

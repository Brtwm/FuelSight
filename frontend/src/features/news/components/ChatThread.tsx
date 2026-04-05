import SendOutlinedIcon from '@mui/icons-material/SendOutlined';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import type { ChatMessageData, ChatScope } from '../../../lib/api/chat.types';
import { CitationList } from './CitationList';

type Props = {
  messages: ChatMessageData[];
  isLoading: boolean;
  isSending: boolean;
  isLlmEnabled: boolean;
  hasError: boolean;
  onRetry: () => void;
  onNewsCitationClick: (refId: string) => void;
  onSend: (payload: { question: string; context_scope: ChatScope[] }) => Promise<void>;
};

export function ChatThread({
  messages,
  isLoading,
  isSending,
  isLlmEnabled,
  hasError,
  onRetry,
  onNewsCitationClick,
  onSend,
}: Props) {
  const [question, setQuestion] = useState('');

  const send = async () => {
    const normalized = question.trim();
    if (normalized.length < 3) {
      return;
    }
    await onSend({
      question: normalized,
      context_scope: ['internal_analytics', 'news_digest'],
    });
    setQuestion('');
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ height: '100%' }}>
        <Stack spacing={2} sx={{ height: '100%' }}>
          <Typography variant="h6" fontWeight={700}>
            Чат
          </Typography>

          {!isLlmEnabled ? (
            <Alert severity="info">LLM off: генерация ответов недоступна, digest и поиск продолжают работать.</Alert>
          ) : null}

          {hasError ? (
            <Alert
              severity="error"
              action={
                <Button color="inherit" size="small" onClick={onRetry}>
                  Повторить
                </Button>
              }
            >
              Не удалось загрузить чат.
            </Alert>
          ) : null}

          <Stack spacing={1} sx={{ flexGrow: 1, overflowY: 'auto', pr: 0.5 }}>
            {!isLoading && messages.length === 0 ? (
              <Typography color="text.secondary">
                Задайте вопрос по внутренней аналитике и новостному фону.
              </Typography>
            ) : null}

            {messages.map((message) => (
              <Box
                key={message.id}
                sx={{
                  alignSelf: message.sender_type === 'user' ? 'flex-end' : 'stretch',
                  backgroundColor: message.sender_type === 'user' ? 'primary.light' : 'grey.100',
                  color: message.sender_type === 'user' ? 'primary.contrastText' : 'text.primary',
                  borderRadius: 2,
                  p: 1.5,
                }}
              >
                <Stack spacing={1}>
                  <Typography variant="body2">{message.message_text}</Typography>
                  {message.sender_type === 'assistant' && message.citations && message.citations.length > 0 ? (
                    <>
                      <Divider />
                      <CitationList citations={message.citations} onNewsCitationClick={onNewsCitationClick} />
                    </>
                  ) : null}
                </Stack>
              </Box>
            ))}
          </Stack>

          <Stack direction="row" spacing={1}>
            <TextField
              fullWidth
              label="Ваш вопрос"
              value={question}
              disabled={!isLlmEnabled || isSending}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void send();
                }
              }}
            />
            <Button
              variant="contained"
              startIcon={<SendOutlinedIcon />}
              disabled={!isLlmEnabled || isSending || question.trim().length < 3}
              onClick={() => void send()}
            >
              Отправить
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

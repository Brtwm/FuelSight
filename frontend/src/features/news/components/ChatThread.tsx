import SendOutlinedIcon from '@mui/icons-material/SendOutlined';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControlLabel,
  Switch,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import type { ChatLlmProviderData, ChatMessageData, ChatScope } from '../../../lib/api/chat.types';
import { CitationList } from './CitationList';

type Props = {
  messages: ChatMessageData[];
  isLoading: boolean;
  isSending: boolean;
  isLlmEnabled: boolean;
  llmProvider?: ChatLlmProviderData | null;
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
  llmProvider,
  hasError,
  onRetry,
  onNewsCitationClick,
  onSend,
}: Props) {
  const [question, setQuestion] = useState('');
  const [includeForecast, setIncludeForecast] = useState(true);
  const [includeNews, setIncludeNews] = useState(true);

  const send = async () => {
    const normalized = question.trim();
    if (normalized.length < 3) {
      return;
    }
    const contextScope: ChatScope[] = ['internal_analytics'];
    if (includeNews) {
      contextScope.push('news_digest');
      contextScope.push('news_raw');
    }
    if (includeForecast) {
      contextScope.push('forecast');
    }
    await onSend({
      question: normalized,
      context_scope: contextScope,
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
            <Alert severity="info">
              Ответ построен по найденным источникам без внешней генерации.
            </Alert>
          ) : null}

          {llmProvider ? (
            <Alert severity={llmProvider.degradation_reason ? 'warning' : 'success'}>
              <Stack spacing={0.5}>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Chip size="small" label={`Провайдер: ${llmProvider.provider}`} />
                  {llmProvider.model ? <Chip size="small" label={`Модель: ${llmProvider.model}`} /> : null}
                </Stack>
                {llmProvider.degradation_reason ? (
                  <Typography variant="caption" color="text.secondary">
                    Техническая причина: {llmProvider.degradation_reason}
                  </Typography>
                ) : null}
              </Stack>
            </Alert>
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
                  {message.sender_type === 'assistant' ? (
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {typeof message.confidence === 'number' ? (
                        <Chip
                          size="small"
                          variant="outlined"
                          label={`Уверенность: ${Math.round(message.confidence * 100)}%`}
                        />
                      ) : null}
                      {message.verification ? (
                        <Chip
                          size="small"
                          color={verificationColor(message.verification.status)}
                          label={verificationLabel(message.verification.status)}
                        />
                      ) : null}
                    </Stack>
                  ) : null}
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
              disabled={isSending}
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
              disabled={isSending || question.trim().length < 3}
              onClick={() => void send()}
            >
              Отправить
            </Button>
          </Stack>
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={includeNews}
                  onChange={(event) => setIncludeNews(event.target.checked)}
                />
              }
              label="Новости"
            />
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={includeForecast}
                  onChange={(event) => setIncludeForecast(event.target.checked)}
                />
              }
              label="Прогноз"
            />
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

function verificationLabel(status: NonNullable<ChatMessageData['verification']>['status']) {
  if (status === 'verified') {
    return 'Ответ проверен';
  }
  if (status === 'repaired') {
    return 'Ответ исправлен';
  }
  if (status === 'fallback_verified') {
    return 'Ответ построен по источникам';
  }
  return 'Недостаточно данных';
}

function verificationColor(status: NonNullable<ChatMessageData['verification']>['status']) {
  if (status === 'verified') {
    return 'success';
  }
  if (status === 'blocked') {
    return 'warning';
  }
  return 'info';
}

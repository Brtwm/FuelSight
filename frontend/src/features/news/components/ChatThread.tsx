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
import { alpha, useTheme } from '@mui/material/styles';
import { useEffect, useRef, useState } from 'react';
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
  const theme = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

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
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: { xs: 2, sm: 2.5 }, '&:last-child': { pb: 2 } }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1.5, flexShrink: 0 }}>
          Чат
        </Typography>

        {!isLlmEnabled ? (
          <Alert severity="info" sx={{ mb: 1, flexShrink: 0 }}>
            Ответ построен по найденным источникам без внешней генерации.
          </Alert>
        ) : null}

        {llmProvider?.degradation_reason ? (
          <Alert severity="warning" sx={{ mb: 1, flexShrink: 0 }}>
            Облачный провайдер временно недоступен, ответ построен по источникам.
          </Alert>
        ) : null}

        {hasError ? (
          <Alert
            severity="error"
            sx={{ mb: 1, flexShrink: 0 }}
            action={
              <Button color="inherit" size="small" onClick={onRetry}>
                Повторить
              </Button>
            }
          >
            Не удалось загрузить чат.
          </Alert>
        ) : null}

        {/* Messages area — scrollable */}
        <Stack
          spacing={1}
          sx={{
            flexGrow: 1,
            overflowY: 'auto',
            pr: 0.5,
            mb: 1.5,
            minHeight: 100,
          }}
        >
          {!isLoading && messages.length === 0 ? (
            <Stack
              spacing={1}
              alignItems="center"
              justifyContent="center"
              sx={{ py: 4, opacity: 0.6 }}
            >
              <Typography color="text.secondary" textAlign="center">
                Задайте вопрос по аналитике и новостному фону
              </Typography>
            </Stack>
          ) : null}

          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                alignSelf: message.sender_type === 'user' ? 'flex-end' : 'stretch',
                maxWidth: message.sender_type === 'user' ? '85%' : '100%',
                backgroundColor:
                  message.sender_type === 'user'
                    ? alpha('#38D5FF', 0.12)
                    : alpha('#111A24', 0.72),
                color: 'text.primary',
                borderRadius: 2.5,
                p: 1.5,
                border: message.sender_type === 'assistant'
                  ? `1px solid ${alpha('#F5B13F', 0.22)}`
                  : `1px solid ${alpha('#38D5FF', 0.16)}`,
                boxShadow: message.sender_type === 'assistant'
                  ? `inset 2px 0 0 ${alpha('#F5B13F', 0.45)}`
                  : 'none',
              }}
            >
              <Stack spacing={1}>
                <Typography variant="body2">{message.message_text}</Typography>
                {message.sender_type === 'assistant' ? (
                  <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                    {typeof message.confidence === 'number' ? (
                      <Chip
                        size="small"
                        variant="outlined"
                        label={`Уверенность: ${Math.round(message.confidence * 100)}%`}
                        sx={{ fontSize: '0.65rem' }}
                      />
                    ) : null}
                    {message.verification ? (
                      <Chip
                        size="small"
                        color={verificationColor(message.verification.status)}
                        label={verificationLabel(message.verification.status)}
                        sx={{ fontSize: '0.65rem' }}
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
          <div ref={messagesEndRef} />
        </Stack>

        {/* Sticky input area */}
        <Stack
          spacing={1}
          sx={{
            flexShrink: 0,
            pt: 1,
            borderTop: `1px solid ${alpha(theme.palette.divider, 0.8)}`,
            backgroundColor: alpha('#0B1017', 0.72),
          }}
        >
          <Stack direction="row" spacing={1}>
            <TextField
              fullWidth
              size="small"
              label="Ваш вопрос"
              placeholder="Ваш вопрос..."
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
              size="small"
              aria-label="Отправить вопрос"
              disabled={isSending || question.trim().length < 3}
              onClick={() => void send()}
              sx={{ minWidth: 44, px: 1.5 }}
            >
              <SendOutlinedIcon fontSize="small" />
            </Button>
          </Stack>
          <Stack direction="row" spacing={1.5} useFlexGap flexWrap="wrap">
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={includeNews}
                  onChange={(event) => setIncludeNews(event.target.checked)}
                />
              }
              label={<Typography variant="caption">Новости</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={includeForecast}
                  onChange={(event) => setIncludeForecast(event.target.checked)}
                />
              }
              label={<Typography variant="caption">Прогноз</Typography>}
            />
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

function verificationLabel(status: NonNullable<ChatMessageData['verification']>['status']) {
  if (status === 'verified') {
    return 'Проверен';
  }
  if (status === 'repaired') {
    return 'Ответ исправлен';
  }
  if (status === 'fallback_verified') {
    return 'По источникам';
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

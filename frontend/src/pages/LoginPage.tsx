import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Alert, Avatar, Box, Card, CardContent, Container, Stack, Typography } from '@mui/material';
import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { LoginForm } from '../features/auth/components/LoginForm';
import { useAuth } from '../features/auth/AuthProvider';
import type { LoginCredentials } from '../lib/api/auth.types';
import { ApiHttpError } from '../lib/api/http';

function resolveLandingRoute(route: string | null | undefined): string {
  if (!route || !route.startsWith('/')) {
    return '/dashboard';
  }
  return route;
}

function toRussianErrorMessage(error: unknown): string {
  if (error instanceof ApiHttpError) {
    if (error.code === 'invalid_credentials') {
      return 'Неверный email или пароль';
    }
    if (error.status >= 500) {
      return 'Сервис временно недоступен. Попробуйте ещё раз.';
    }
    return error.message || 'Ошибка авторизации';
  }
  return 'Не удалось выполнить вход. Проверьте соединение и попробуйте снова.';
}

export function LoginPage() {
  const { status, isAuthenticated, user, login, sessionExpired, clearSessionExpired } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (status === 'loading') {
    return (
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography color="text.secondary">Проверяем сессию...</Typography>
      </Container>
    );
  }

  if (isAuthenticated) {
    return <Navigate to={resolveLandingRoute(user?.preferred_landing_route)} replace />;
  }

  const handleSubmit = async (credentials: LoginCredentials) => {
    setSubmitting(true);
    setErrorMessage(null);
    clearSessionExpired();
    try {
      await login(credentials);
    } catch (error) {
      setErrorMessage(toRussianErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 4, md: 10 } }}>
      <Box
        sx={{
          display: 'grid',
          gap: { xs: 2.5, md: 4 },
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
          alignItems: 'stretch',
        }}
      >
        <Box>
          <Stack spacing={1.25} sx={{ height: '100%', justifyContent: 'center' }}>
            <Typography variant="h3" fontWeight={800} sx={{ fontSize: { xs: '2.8rem', sm: '3.25rem' } }}>
              FuelSight
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ fontSize: { xs: '1.55rem', sm: '1.75rem' } }}>
              Аналитика спроса, маржи и внешнего контекста для нефтепродуктов
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Analyst mode по умолчанию
            </Typography>
            <Typography variant="body2" color="text.secondary">- KPI и риски</Typography>
            <Typography variant="body2" color="text.secondary">- Прогноз и качество модели</Typography>
            <Typography variant="body2" color="text.secondary">- Сводка новостей и чат с источниками</Typography>
          </Stack>
        </Box>

        <Box>
          <Card>
            <CardContent sx={{ p: { xs: 2.25, sm: 3 } }}>
              <Stack spacing={2}>
                <Box sx={{ textAlign: 'center' }}>
                  <Avatar sx={{ mx: 'auto', mb: 1, bgcolor: 'primary.main' }}>
                    <LockOutlinedIcon />
                  </Avatar>
                  <Typography variant="h5" fontWeight={700}>
                    Вход в систему
                  </Typography>
                </Box>

                {sessionExpired ? (
                  <Alert severity="warning">
                    Сессия истекла. Выполните вход повторно.
                  </Alert>
                ) : null}

                <LoginForm loading={submitting} errorMessage={errorMessage} onSubmit={handleSubmit} />
              </Stack>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Container>
  );
}

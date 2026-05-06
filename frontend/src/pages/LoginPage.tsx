import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import {
  Alert,
  Avatar,
  Box,
  Card,
  CardContent,
  Container,
  Stack,
  Typography,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
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

const features = [
  {
    icon: <DashboardOutlinedIcon sx={{ fontSize: 28 }} />,
    title: 'KPI и риски',
    description: 'Мгновенный обзор ключевых метрик и критических алертов',
  },
  {
    icon: <TimelineOutlinedIcon sx={{ fontSize: 28 }} />,
    title: 'Прогноз спроса',
    description: 'ML-модели с оценкой качества и сценарным анализом',
  },
  {
    icon: <InsightsOutlinedIcon sx={{ fontSize: 28 }} />,
    title: 'Аналитика маржи',
    description: 'Контроль закупочных цен и маржинальности в реальном времени',
  },
];

export function LoginPage() {
  const { status, isAuthenticated, user, login, sessionExpired, clearSessionExpired } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const theme = useTheme();

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
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: '-30%',
          left: '-10%',
          width: '60%',
          height: '80%',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.15)}, transparent 70%)`,
          filter: 'blur(80px)',
          pointerEvents: 'none',
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          bottom: '-20%',
          right: '-10%',
          width: '50%',
          height: '70%',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(theme.palette.secondary.main, 0.12)}, transparent 70%)`,
          filter: 'blur(80px)',
          pointerEvents: 'none',
        },
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1, py: { xs: 4, md: 0 } }}>
        <Box
          sx={{
            display: 'grid',
            gap: { xs: 4, md: 6 },
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            alignItems: 'center',
          }}
        >
          {/* Hero section */}
          <Box>
            <Stack spacing={3}>
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: '2.5rem', sm: '3.25rem', md: '3.5rem' },
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  lineHeight: 1.1,
                }}
              >
                FuelSight
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: 'text.secondary',
                  fontSize: { xs: '1.1rem', sm: '1.25rem' },
                  fontWeight: 400,
                  maxWidth: 440,
                  lineHeight: 1.5,
                }}
              >
                Аналитическая платформа для управления спросом, маржой и прогнозирования в нефтепродуктовом бизнесе
              </Typography>

              <Stack spacing={2.5} sx={{ pt: 1 }}>
                {features.map((feature) => (
                  <Stack key={feature.title} direction="row" spacing={2} alignItems="flex-start">
                    <Box
                      sx={{
                        p: 1,
                        borderRadius: 2,
                        backgroundColor: alpha(theme.palette.primary.main, 0.1),
                        color: theme.palette.primary.light,
                        display: 'flex',
                        flexShrink: 0,
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Stack spacing={0.25}>
                      <Typography variant="subtitle2" fontWeight={700}>
                        {feature.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.4 }}>
                        {feature.description}
                      </Typography>
                    </Stack>
                  </Stack>
                ))}
              </Stack>
            </Stack>
          </Box>

          {/* Login card */}
          <Box>
            <Card
              sx={{
                maxWidth: 420,
                mx: { xs: 'auto', md: 0 },
                ml: { md: 'auto' },
                border: `1px solid ${alpha(theme.palette.primary.main, 0.15)}`,
                backgroundColor: alpha(theme.palette.background.paper, 0.7),
                backdropFilter: 'blur(20px)',
              }}
            >
              <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
                <Stack spacing={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Avatar
                      sx={{
                        mx: 'auto',
                        mb: 1.5,
                        width: 48,
                        height: 48,
                        background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                      }}
                    >
                      <LockOutlinedIcon />
                    </Avatar>
                    <Typography variant="h5" fontWeight={700}>
                      Вход в систему
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      Авторизуйтесь для доступа к аналитике
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
    </Box>
  );
}

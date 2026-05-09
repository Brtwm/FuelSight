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
    icon: <DashboardOutlinedIcon sx={{ fontSize: 24 }} />,
    title: 'KPI и риски',
    description: 'Мгновенный обзор ключевых метрик и критических алертов',
  },
  {
    icon: <TimelineOutlinedIcon sx={{ fontSize: 24 }} />,
    title: 'Прогноз спроса',
    description: 'Прогноз с оценкой качества и сценарным анализом',
  },
  {
    icon: <InsightsOutlinedIcon sx={{ fontSize: 24 }} />,
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
        background:
          'radial-gradient(circle at 18% 18%, rgba(56, 213, 255, 0.13), transparent 30%), radial-gradient(circle at 82% 84%, rgba(245, 177, 63, 0.1), transparent 34%), #05070B',
      }}
    >
      <Box
        className="cinematic-grid"
        sx={{
          position: 'absolute',
          inset: 0,
          opacity: 0.48,
          maskImage: 'linear-gradient(90deg, black, black 58%, transparent)',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          inset: { xs: '8% -35% 12% -28%', md: '12% 37% 10% -10%' },
          border: `1px solid ${alpha(theme.palette.primary.main, 0.12)}`,
          transform: 'skewY(-8deg)',
          background:
            'linear-gradient(90deg, transparent 0 18%, rgba(56, 213, 255, 0.12) 18% 18.4%, transparent 18.4% 44%, rgba(245, 177, 63, 0.14) 44% 44.3%, transparent 44.3% 100%)',
          pointerEvents: 'none',
          opacity: 0.64,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: { xs: '14%', md: '20%' },
          left: { xs: '8%', md: '7%' },
          width: { xs: 220, md: 460 },
          height: { xs: 220, md: 360 },
          borderRadius: 2,
          border: `1px solid ${alpha('#F5B13F', 0.14)}`,
          background:
            'linear-gradient(135deg, rgba(245, 177, 63, 0.08), transparent 38%), linear-gradient(45deg, transparent 48%, rgba(56, 213, 255, 0.18) 49%, transparent 50%)',
          transform: 'rotate(-12deg)',
          pointerEvents: 'none',
          opacity: 0.42,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          width: 10,
          height: 10,
          borderRadius: '50%',
          top: { xs: '30%', md: '31%' },
          left: { xs: '30%', md: '30%' },
          backgroundColor: '#F5B13F',
          boxShadow: '0 0 0 8px rgba(245,177,63,0.08), 0 0 34px rgba(245,177,63,0.38)',
          pointerEvents: 'none',
          animation: 'pulseGlow 3.5s ease-in-out infinite',
        }}
      />

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
          <Box className="animate-in">
            <Stack spacing={3}>
              <Stack spacing={1}>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 800,
                    fontSize: { xs: '2.5rem', sm: '3.25rem', md: '3.75rem' },
                    fontFamily: "'Unbounded', 'IBM Plex Sans', sans-serif",
                    background: `linear-gradient(135deg, ${theme.palette.text.primary}, #38D5FF 48%, #F5B13F)`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    lineHeight: 1.1,
                  }}
                >
                  FuelSight
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: alpha('#FBBF24', 0.7),
                    fontWeight: 600,
                    letterSpacing: 0,
                    textTransform: 'uppercase',
                    fontSize: '0.7rem',
                  }}
                >
                  Аналитическая платформа
                </Typography>
              </Stack>
              <Typography
                variant="h6"
                sx={{
                  color: 'text.secondary',
                  fontSize: { xs: '1rem', sm: '1.15rem' },
                  fontWeight: 400,
                  maxWidth: 420,
                  lineHeight: 1.6,
                  fontFamily: "'IBM Plex Sans', sans-serif",
                }}
              >
                Управление спросом, маржой и прогнозирование
                в <Box component="span" sx={{ color: '#FBBF24', fontWeight: 500 }}>нефтепродуктовом</Box> бизнесе
              </Typography>

              <Stack spacing={2} sx={{ pt: 1 }}>
                {features.map((feature, index) => (
                  <Stack
                    key={feature.title}
                    direction="row"
                    spacing={2}
                    alignItems="flex-start"
                    className={`animate-in animate-delay-${index + 2}`}
                  >
                    <Box
                      sx={{
                        p: 1,
                        borderRadius: 2.5,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.12)}, ${alpha('#F5B13F', 0.06)})`,
                        border: `1px solid ${alpha(theme.palette.primary.main, 0.16)}`,
                        color: theme.palette.primary.light,
                        display: 'flex',
                        flexShrink: 0,
                        animation: 'pulseGlow 4s ease-in-out infinite',
                        animationDelay: `${index * 0.5}s`,
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Stack spacing={0.25}>
                      <Typography variant="subtitle2" fontWeight={700}>
                        {feature.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.4, fontSize: '0.82rem' }}>
                        {feature.description}
                      </Typography>
                    </Stack>
                  </Stack>
                ))}
              </Stack>
            </Stack>
          </Box>

          {/* Login card */}
          <Box className="animate-in animate-delay-3">
            <Card
              sx={{
                maxWidth: 420,
                mx: { xs: 'auto', md: 0 },
                ml: { md: 'auto' },
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                backgroundColor: alpha('#0B1017', 0.78),
                backdropFilter: 'blur(22px)',
                '&::after': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: '15%',
                  right: '15%',
                  height: '2px',
                  background: `linear-gradient(90deg, transparent, ${alpha('#F5B13F', 0.58)}, ${alpha(theme.palette.primary.main, 0.44)}, transparent)`,
                  borderRadius: '0 0 2px 2px',
                },
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
                        background: `linear-gradient(135deg, ${theme.palette.primary.main}, #FBBF24)`,
                        color: '#061018',
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

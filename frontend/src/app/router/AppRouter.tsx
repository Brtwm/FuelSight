import { CircularProgress, Stack, Typography } from '@mui/material';
import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { ProtectedRoute } from '../../features/auth/components/ProtectedRoute';

const LoginPage = lazy(async () => ({ default: (await import('../../pages/LoginPage')).LoginPage }));
const ImportPage = lazy(async () => ({ default: (await import('../../pages/ImportPage')).ImportPage }));
const DashboardPage = lazy(async () => ({ default: (await import('../../pages/DashboardPage')).DashboardPage }));
const SalesAnalyticsPage = lazy(
  async () => ({ default: (await import('../../pages/SalesAnalyticsPage')).SalesAnalyticsPage }),
);
const MarginAnalyticsPage = lazy(
  async () => ({ default: (await import('../../pages/MarginAnalyticsPage')).MarginAnalyticsPage }),
);
const ForecastPage = lazy(
  async () => ({ default: (await import('../../pages/ForecastPage')).ForecastPage }),
);
const NewsPage = lazy(async () => ({ default: (await import('../../pages/NewsPage')).NewsPage }));

function RouteLoadingFallback() {
  return (
    <Stack spacing={2} alignItems="center" justifyContent="center" sx={{ py: 8 }}>
      <CircularProgress size={28} />
      <Typography color="text.secondary">Загружаем экран...</Typography>
    </Stack>
  );
}

export function AppRouter() {
  return (
    <Suspense fallback={<RouteLoadingFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route
            path="import"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <ImportPage />
              </ProtectedRoute>
            }
          />
          <Route path="analytics/sales" element={<SalesAnalyticsPage />} />
          <Route path="analytics/margin" element={<MarginAnalyticsPage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="news" element={<NewsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}


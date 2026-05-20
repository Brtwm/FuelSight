import { CircularProgress, Stack, Typography } from '@mui/material';
import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { useAuth } from '../../features/auth/AuthProvider';
import { ProtectedRoute } from '../../features/auth/components/ProtectedRoute';
import { getDefaultRouteForRole } from '../../features/auth/access';
import { PageStub } from '../../pages/PageStub';

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

function ReportsPage() {
  return (
    <PageStub
      title="Управленческие отчёты"
      description="Сводный раздел для аналитических и управленческих отчётов FuelSight."
    />
  );
}

function DefaultRedirect() {
  const { isAuthenticated, user } = useAuth();
  return <Navigate to={isAuthenticated ? getDefaultRouteForRole(user?.role) : '/login'} replace />;
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
          <Route index element={<DefaultRedirect />} />
          <Route
            path="dashboard"
            element={(
              <ProtectedRoute routeKey="dashboard">
                <DashboardPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="executive/dashboard"
            element={(
              <ProtectedRoute routeKey="dashboard">
                <DashboardPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="import"
            element={
              <ProtectedRoute routeKey="import">
                <ImportPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="analytics/sales"
            element={(
              <ProtectedRoute routeKey="salesAnalytics">
                <SalesAnalyticsPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="analytics/margin"
            element={(
              <ProtectedRoute routeKey="marginAnalytics">
                <MarginAnalyticsPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="forecast"
            element={(
              <ProtectedRoute routeKey="forecast">
                <ForecastPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="news"
            element={(
              <ProtectedRoute routeKey="news">
                <NewsPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="reports"
            element={(
              <ProtectedRoute routeKey="reports">
                <ReportsPage />
              </ProtectedRoute>
            )}
          />
        </Route>
        <Route path="*" element={<DefaultRedirect />} />
      </Routes>
    </Suspense>
  );
}


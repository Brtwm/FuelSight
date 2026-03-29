import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { ProtectedRoute } from '../../features/auth/components/ProtectedRoute';
import { DashboardPage } from '../../pages/DashboardPage';
import { ForecastPage } from '../../pages/ForecastPage';
import { ImportPage } from '../../pages/ImportPage';
import { LoginPage } from '../../pages/LoginPage';
import { MarginAnalyticsPage } from '../../pages/MarginAnalyticsPage';
import { NewsPage } from '../../pages/NewsPage';
import { SalesAnalyticsPage } from '../../pages/SalesAnalyticsPage';

export function AppRouter() {
  return (
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
  );
}


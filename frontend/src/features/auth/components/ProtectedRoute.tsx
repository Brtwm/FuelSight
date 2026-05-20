import { Alert, Box, CircularProgress, Stack, Typography } from '@mui/material';
import type { PropsWithChildren } from 'react';
import { Navigate } from 'react-router-dom';
import type { UserRole } from '../../../lib/api/auth.types';
import { useAuth } from '../AuthProvider';
import { canAccessRole, canAccessRoute, type RouteKey } from '../access';

type ProtectedRouteProps = PropsWithChildren<{
  allowedRoles?: UserRole[];
  routeKey?: RouteKey;
}>;

export function ProtectedRoute({ allowedRoles, routeKey, children }: ProtectedRouteProps) {
  const { status, isAuthenticated, user } = useAuth();

  if (status === 'loading') {
    return (
      <Box sx={{ minHeight: '60vh', display: 'grid', placeItems: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  const hasAccess = routeKey
    ? canAccessRoute(user.role, routeKey)
    : canAccessRole(user.role, allowedRoles);

  if (!hasAccess) {
    return (
      <Box sx={{ p: 4 }}>
        <Stack spacing={2} maxWidth={560}>
          <Typography variant="h4" fontWeight={700}>
            Доступ ограничен
          </Typography>
          <Alert severity="error">У вашей роли нет доступа к этому разделу (HTTP 403).</Alert>
        </Stack>
      </Box>
    );
  }

  return <>{children}</>;
}

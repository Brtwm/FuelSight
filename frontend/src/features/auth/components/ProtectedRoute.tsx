import { Navigate } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import { Alert, Box, Stack, Typography } from '@mui/material';
import { useAuth } from '../AuthProvider';
import type { UserRole } from '../AuthProvider';

type ProtectedRouteProps = PropsWithChildren<{
  allowedRoles?: UserRole[];
}>;

export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
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


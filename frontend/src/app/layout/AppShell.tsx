import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import NewspaperOutlinedIcon from '@mui/icons-material/NewspaperOutlined';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import {
  AppBar,
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  FreshnessBadgeGroup,
  SourceModeBadge,
} from '../../components/common';
import { useAuth } from '../../features/auth/AuthProvider';
import { API_BASE_URL } from '../../lib/config/env';
import { checkBackendHealth } from '../../lib/api/client';
import type { AuthUser } from '../../lib/api/auth.types';
import { parseApiEnvelope } from '../../lib/api/http';
import {
  AppShellSlotsProvider,
  useAppShellSlots,
} from './AppShellSlotsContext';

const drawerWidth = 252;

type NavItem = {
  label: string;
  path: string;
  roles: Array<'admin' | 'analyst'>;
  icon: ReactElement;
};

const navItems: NavItem[] = [
  { label: 'KPI', path: '/dashboard', roles: ['admin', 'analyst'], icon: <DashboardOutlinedIcon /> },
  { label: 'Импорт', path: '/import', roles: ['admin'], icon: <DownloadOutlinedIcon /> },
  { label: 'Продажи', path: '/analytics/sales', roles: ['admin', 'analyst'], icon: <AssessmentOutlinedIcon /> },
  { label: 'Маржа', path: '/analytics/margin', roles: ['admin', 'analyst'], icon: <InsightsOutlinedIcon /> },
  { label: 'Прогноз', path: '/forecast', roles: ['admin', 'analyst'], icon: <TimelineOutlinedIcon /> },
  { label: 'Сводка', path: '/news', roles: ['admin', 'analyst'], icon: <NewspaperOutlinedIcon /> },
];

function AppShellContent() {
  const { user, logout, authFetch } = useAuth();
  const { slots } = useAppShellSlots();
  const location = useLocation();
  const navigate = useNavigate();

  const healthQuery = useQuery({
    queryKey: ['backend-health'],
    queryFn: checkBackendHealth,
    refetchInterval: 30000,
  });

  const sessionQuery = useQuery({
    queryKey: ['auth-session'],
    queryFn: async () => {
      const response = await authFetch(`${API_BASE_URL}/auth/me`, { method: 'GET' });
      return parseApiEnvelope<AuthUser>(response);
    },
    enabled: Boolean(user),
    refetchInterval: 30000,
  });

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ ml: `${drawerWidth}px`, width: `calc(100% - ${drawerWidth}px)` }}>
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            FuelSight
          </Typography>
          <Chip
            label={healthQuery.data?.ok ? 'Backend online' : 'Backend unavailable'}
            size="small"
            color={healthQuery.data?.ok ? 'success' : 'warning'}
            variant="outlined"
          />
          <Chip
            label={sessionQuery.isError ? 'Session check failed' : 'Session active'}
            size="small"
            color={sessionQuery.isError ? 'warning' : 'success'}
            variant="outlined"
          />
          <FreshnessBadgeGroup
            dataFreshness={slots.dataFreshness}
            modelFreshness={slots.modelFreshness}
            newsFreshness={slots.newsFreshness}
            showFallback
          />
          <SourceModeBadge title="LLM" mode={slots.llmMode} showFallback />
          <SourceModeBadge
            title="Indicators"
            mode={slots.externalIndicatorsMode}
            showFallback
          />
          <Chip label={user?.role ?? 'guest'} size="small" />
          <Button color="inherit" onClick={() => void logout()}>
            Выйти
          </Button>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar>
          <Typography variant="h6">FuelSight</Typography>
        </Toolbar>
        <Divider />
        <List>
          {navItems
            .filter((item) => user && item.roles.includes(user.role))
            .map((item) => (
              <ListItemButton
                key={item.path}
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, ml: `${drawerWidth}px` }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}

export function AppShell() {
  const location = useLocation();
  return (
    <AppShellSlotsProvider routeKey={location.pathname}>
      <AppShellContent />
    </AppShellSlotsProvider>
  );
}


import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import MenuOutlinedIcon from '@mui/icons-material/MenuOutlined';
import NewspaperOutlinedIcon from '@mui/icons-material/NewspaperOutlined';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import {
  AppBar,
  Box,
  BottomNavigation,
  BottomNavigationAction,
  Button,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useQuery } from '@tanstack/react-query';
import type { ReactElement, ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
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
const mobileBottomNavHeight = 64;

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

function isRouteSelected(itemPath: string, pathname: string): boolean {
  return pathname === itemPath || pathname.startsWith(`${itemPath}/`);
}

function compactChipSx(compact: boolean) {
  if (!compact) {
    return undefined;
  }
  return {
    height: 22,
    '& .MuiChip-label': {
      px: 0.75,
      fontSize: '0.68rem',
      fontWeight: 600,
    },
  };
}

function AppShellContent() {
  const { user, logout, authFetch } = useAuth();
  const { slots } = useAppShellSlots();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobileShell = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

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

  useEffect(() => {
    setMobileDrawerOpen(false);
  }, [location.pathname]);

  const visibleNavItems = useMemo(
    () => navItems.filter((item) => user && item.roles.includes(user.role)),
    [user],
  );

  const mobilePrimaryNavItems = useMemo(
    () => visibleNavItems.filter((item) => item.path !== '/import'),
    [visibleNavItems],
  );

  const mobileNavValue = useMemo(
    () =>
      mobilePrimaryNavItems.find((item) => isRouteSelected(item.path, location.pathname))?.path
      ?? false,
    [location.pathname, mobilePrimaryNavItems],
  );

  const compact = isMobileShell;

  const healthChipLabel = healthQuery.data?.ok
    ? (compact ? 'BE ok' : 'Backend online')
    : (compact ? 'BE down' : 'Backend unavailable');
  const sessionChipLabel = sessionQuery.isError
    ? (compact ? 'Sess warn' : 'Session check failed')
    : (compact ? 'Sess ok' : 'Session active');

  const handleNavigate = (path: string) => {
    navigate(path);
    setMobileDrawerOpen(false);
  };

  const drawerContent: ReactNode = (
    <>
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h6">FuelSight</Typography>
        {isMobileShell ? (
          <IconButton
            size="small"
            aria-label="Закрыть меню"
            onClick={() => setMobileDrawerOpen(false)}
          >
            <CloseOutlinedIcon fontSize="small" />
          </IconButton>
        ) : null}
      </Toolbar>
      <Divider />
      <List>
        {visibleNavItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={isRouteSelected(item.path, location.pathname)}
            onClick={() => handleNavigate(item.path)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        sx={{
          ml: isMobileShell ? 0 : `${drawerWidth}px`,
          width: isMobileShell ? '100%' : `calc(100% - ${drawerWidth}px)`,
          zIndex: (themeArg) => themeArg.zIndex.drawer + 1,
        }}
      >
        <Toolbar
          sx={{
            alignItems: 'flex-start',
            minHeight: 'auto !important',
            py: 1.25,
          }}
        >
          <Stack spacing={1} sx={{ width: '100%' }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
              <Stack direction="row" spacing={0.75} alignItems="center">
                {isMobileShell ? (
                  <IconButton
                    color="inherit"
                    size="small"
                    aria-label="Открыть меню"
                    onClick={() => setMobileDrawerOpen(true)}
                  >
                    <MenuOutlinedIcon fontSize="small" />
                  </IconButton>
                ) : null}
                <Typography variant="h6" sx={{ lineHeight: 1.2 }}>
                  FuelSight
                </Typography>
              </Stack>
              <Stack direction="row" spacing={0.75} alignItems="center">
                <Chip
                  label={user?.role ?? 'guest'}
                  size="small"
                  sx={compactChipSx(compact)}
                />
                <Button
                  color="inherit"
                  size="small"
                  startIcon={!compact ? <LogoutOutlinedIcon fontSize="small" /> : undefined}
                  onClick={() => void logout()}
                  sx={{ minWidth: 'auto', px: compact ? 1 : 1.5 }}
                >
                  Выйти
                </Button>
              </Stack>
            </Stack>

            <Stack
              direction="row"
              spacing={0.75}
              alignItems="center"
              useFlexGap
              sx={{
                overflowX: 'auto',
                pb: 0.25,
                '&::-webkit-scrollbar': { display: 'none' },
                scrollbarWidth: 'none',
              }}
            >
              <Chip
                label={healthChipLabel}
                size="small"
                color={healthQuery.data?.ok ? 'success' : 'warning'}
                variant="outlined"
                sx={compactChipSx(compact)}
              />
              <Chip
                label={sessionChipLabel}
                size="small"
                color={sessionQuery.isError ? 'warning' : 'success'}
                variant="outlined"
                sx={compactChipSx(compact)}
              />
              <FreshnessBadgeGroup
                dataFreshness={slots.dataFreshness}
                modelFreshness={slots.modelFreshness}
                newsFreshness={slots.newsFreshness}
                showFallback
                compact={compact}
              />
              <SourceModeBadge
                title="LLM"
                compactTitle="LLM"
                mode={slots.llmMode}
                showFallback
                compact={compact}
              />
              <SourceModeBadge
                title="Indicators"
                compactTitle="Ind"
                mode={slots.externalIndicatorsMode}
                showFallback
                compact={compact}
              />
            </Stack>
          </Stack>
        </Toolbar>
      </AppBar>
      {isMobileShell ? (
        <Drawer
          anchor="left"
          open={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
          variant="temporary"
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
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
          {drawerContent}
        </Drawer>
      )}

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          px: { xs: 1.5, sm: 2, md: 3 },
          py: { xs: 2, md: 3 },
          ml: isMobileShell ? 0 : `${drawerWidth}px`,
          pt: { xs: 14, md: 16 },
          pb: isMobileShell
            ? `calc(${mobileBottomNavHeight}px + env(safe-area-inset-bottom) + 16px)`
            : 3,
        }}
      >
        <Outlet />
      </Box>

      {isMobileShell ? (
        <BottomNavigation
          showLabels
          value={mobileNavValue}
          onChange={(_event, value) => {
            if (typeof value === 'string') {
              handleNavigate(value);
            }
          }}
          sx={{
            position: 'fixed',
            left: 0,
            right: 0,
            bottom: 0,
            height: mobileBottomNavHeight,
            pb: 'env(safe-area-inset-bottom)',
            borderTop: '1px solid',
            borderColor: 'divider',
            zIndex: (themeArg) => themeArg.zIndex.drawer + 2,
          }}
        >
          {mobilePrimaryNavItems.map((item) => (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              value={item.path}
              icon={item.icon}
            />
          ))}
        </BottomNavigation>
      ) : null}
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


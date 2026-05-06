import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
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
import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import type { ReactElement, ReactNode } from 'react';
import { useMemo, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import {
  AppShellSlotsProvider,
} from './AppShellSlotsContext';

const drawerWidth = 260;
const mobileBottomNavHeight = 56;

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

function AppShellContent() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobileShell = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

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

  const handleNavigate = (path: string) => {
    navigate(path);
    setMobileDrawerOpen(false);
  };

  const roleLabel = user?.role === 'admin' ? 'Администратор' : 'Аналитик';

  const drawerContent: ReactNode = (
    <>
      <Toolbar
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          px: 2.5,
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 800,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          FuelSight
        </Typography>
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
      <List sx={{ px: 0.5, pt: 1 }}>
        {visibleNavItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={isRouteSelected(item.path, location.pathname)}
            onClick={() => handleNavigate(item.path)}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
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
            minHeight: { xs: 52, md: 56 },
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ width: '100%' }}>
            <Stack direction="row" spacing={1} alignItems="center">
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
              {isMobileShell ? (
                <Typography
                  variant="subtitle1"
                  sx={{
                    fontWeight: 800,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  FuelSight
                </Typography>
              ) : null}
            </Stack>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                label={roleLabel}
                size="small"
                sx={{
                  backgroundColor: alpha(theme.palette.primary.main, 0.15),
                  color: theme.palette.primary.light,
                  fontWeight: 600,
                  fontSize: '0.72rem',
                }}
              />
              <Button
                color="inherit"
                size="small"
                startIcon={!isMobileShell ? <LogoutOutlinedIcon fontSize="small" /> : undefined}
                onClick={() => void logout()}
                sx={{ minWidth: 'auto', px: isMobileShell ? 1 : 1.5, textTransform: 'none' }}
              >
                Выйти
              </Button>
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
          boxSizing: 'border-box',
          flexGrow: 1,
          minWidth: 0,
          overflowX: 'hidden',
          px: { xs: 1.5, sm: 2, md: 3 },
          py: { xs: 2, md: 3 },
          ml: isMobileShell ? 0 : `${drawerWidth}px`,
          width: isMobileShell ? '100%' : `calc(100% - ${drawerWidth}px)`,
          pt: { xs: 9, md: 10 },
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
            boxSizing: 'border-box',
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

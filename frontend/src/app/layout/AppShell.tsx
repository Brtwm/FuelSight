import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import InsertChartOutlinedIcon from '@mui/icons-material/InsertChartOutlined';
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
  NAVIGATION_ITEMS,
  ROLE_LABELS,
  canAccessRoute,
  getNavLabel,
  type NavigationItem,
  type RouteKey,
} from '../../features/auth/access';
import { designTokens } from '../../theme/theme';

const drawerWidth = 248;
const mobileBottomNavHeight = 48;

type NavItem = NavigationItem & {
  path: string;
  routeKey: RouteKey;
  icon: ReactElement;
};

const navItems: NavItem[] = [
  {
    ...NAVIGATION_ITEMS[0],
    icon: <DashboardOutlinedIcon />,
  },
  {
    ...NAVIGATION_ITEMS[1],
    icon: <DownloadOutlinedIcon />,
  },
  {
    ...NAVIGATION_ITEMS[2],
    icon: <AssessmentOutlinedIcon />,
  },
  {
    ...NAVIGATION_ITEMS[3],
    icon: <InsightsOutlinedIcon />,
  },
  {
    ...NAVIGATION_ITEMS[4],
    icon: <TimelineOutlinedIcon />,
  },
  {
    ...NAVIGATION_ITEMS[5],
    icon: <NewspaperOutlinedIcon />,
  },
  {
    ...NAVIGATION_ITEMS[6],
    icon: <InsertChartOutlinedIcon />,
  },
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
    () => navItems.filter((item) => canAccessRoute(user?.role, item.routeKey)),
    [user],
  );

  const mobilePrimaryNavItems = useMemo(
    () => visibleNavItems,
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

  const roleLabel = user?.role ? ROLE_LABELS[user.role] : 'Пользователь';

  const drawerContent: ReactNode = (
    <>
      <Toolbar
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          px: 2,
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 800,
            fontFamily: "'Unbounded', 'IBM Plex Sans', sans-serif",
            color: designTokens.textMain,
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
            <ListItemText primary={getNavLabel(item, user?.role)} />
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
            minHeight: 56,
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
                    fontFamily: "'Unbounded', 'IBM Plex Sans', sans-serif",
                    color: designTokens.textMain,
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
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  borderColor: alpha(theme.palette.primary.main, 0.22),
                  color: theme.palette.text.primary,
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
          pt: { xs: 8, md: 9 },
          pb: isMobileShell
            ? `calc(${mobileBottomNavHeight}px + env(safe-area-inset-bottom) + 8px)`
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
              label={getNavLabel(item, user?.role)}
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
  return <AppShellContent />;
}

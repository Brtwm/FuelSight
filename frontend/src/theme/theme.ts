import { createTheme, alpha } from '@mui/material/styles';

// ── Design tokens ──────────────────────────────────────────────────────────
const BRAND = {
  primary: '#3B82F6',      // blue-500
  primaryDark: '#2563EB',  // blue-600
  secondary: '#06B6D4',    // cyan-500
  accent: '#8B5CF6',       // violet-500
  success: '#10B981',      // emerald-500
  warning: '#F59E0B',      // amber-500
  error: '#EF4444',        // red-500
  info: '#06B6D4',

  bg: '#0B1120',           // deepest background
  surface: '#111827',      // card / panel background
  surfaceLight: '#1E293B', // elevated surface
  border: 'rgba(255,255,255,0.08)',
  borderHover: 'rgba(255,255,255,0.14)',
};

export const appTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: BRAND.primary,
      dark: BRAND.primaryDark,
    },
    secondary: {
      main: BRAND.secondary,
    },
    success: {
      main: BRAND.success,
    },
    warning: {
      main: BRAND.warning,
    },
    error: {
      main: BRAND.error,
    },
    info: {
      main: BRAND.info,
    },
    background: {
      default: BRAND.bg,
      paper: BRAND.surface,
    },
    divider: BRAND.border,
  },
  typography: {
    fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    h3: { fontWeight: 800, letterSpacing: '-0.02em' },
    h4: { fontWeight: 700, letterSpacing: '-0.01em' },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
    subtitle1: { fontWeight: 600 },
    body2: { lineHeight: 1.6 },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    `0 1px 3px ${alpha('#000', 0.3)}, 0 1px 2px ${alpha('#000', 0.2)}`,
    `0 4px 6px ${alpha('#000', 0.25)}`,
    `0 6px 12px ${alpha('#000', 0.3)}`,
    `0 8px 16px ${alpha('#000', 0.3)}`,
    `0 12px 24px ${alpha('#000', 0.35)}`,
    `0 16px 32px ${alpha('#000', 0.35)}`,
    `0 20px 40px ${alpha('#000', 0.4)}`,
    `0 24px 48px ${alpha('#000', 0.4)}`,
    ...Array(16).fill('none') as string[],
  ] as unknown as typeof createTheme extends (o: infer O) => unknown ? O extends { shadows?: infer S } ? S : never : never,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage: `radial-gradient(ellipse 80% 50% at 50% -20%, ${alpha(BRAND.primary, 0.12)}, transparent)`,
        },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: alpha(BRAND.bg, 0.8),
          backdropFilter: 'blur(12px)',
          borderBottom: `1px solid ${BRAND.border}`,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: BRAND.surface,
          borderRight: `1px solid ${BRAND.border}`,
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: alpha(BRAND.surfaceLight, 0.5),
          border: `1px solid ${BRAND.border}`,
          backdropFilter: 'blur(8px)',
          transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
          '&:hover': {
            borderColor: BRAND.borderHover,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          fontSize: '0.75rem',
        },
        outlined: {
          borderColor: BRAND.border,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        contained: {
          fontWeight: 600,
          textTransform: 'none' as const,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: `0 4px 12px ${alpha(BRAND.primary, 0.35)}`,
          },
        },
        outlined: {
          textTransform: 'none' as const,
          borderColor: BRAND.border,
          '&:hover': {
            borderColor: BRAND.borderHover,
            backgroundColor: alpha(BRAND.primary, 0.06),
          },
        },
        text: {
          textTransform: 'none' as const,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: BRAND.border,
            },
            '&:hover fieldset': {
              borderColor: BRAND.borderHover,
            },
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 8px',
          '&.Mui-selected': {
            backgroundColor: alpha(BRAND.primary, 0.15),
            '&:hover': {
              backgroundColor: alpha(BRAND.primary, 0.2),
            },
          },
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          backgroundColor: alpha(BRAND.bg, 0.9),
          backdropFilter: 'blur(12px)',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          fontWeight: 600,
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: BRAND.border,
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          backgroundColor: alpha('#fff', 0.05),
        },
      },
    },
  },
});

// Export tokens for chart components
export const chartPalette = {
  primary: BRAND.primary,
  secondary: BRAND.secondary,
  accent: BRAND.accent,
  success: BRAND.success,
  warning: BRAND.warning,
  error: BRAND.error,
  gridLine: 'rgba(255,255,255,0.06)',
  axisLabel: 'rgba(255,255,255,0.5)',
  axisLine: 'rgba(255,255,255,0.1)',
  tooltipBg: alpha(BRAND.surface, 0.95),
  tooltipBorder: BRAND.border,
  areaOpacity: 0.12,
  series: [
    BRAND.primary,     // #3B82F6
    BRAND.secondary,   // #06B6D4
    BRAND.accent,      // #8B5CF6
    BRAND.success,     // #10B981
    BRAND.warning,     // #F59E0B
    '#EC4899',         // pink-500
    '#F97316',         // orange-500
  ],
};

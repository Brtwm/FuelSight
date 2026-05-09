import { createTheme, alpha } from '@mui/material/styles';

// ── Cinematic Dark design tokens ────────────────────────────────────────────
export const designTokens = {
  bgCanvas: '#05070B',
  bgPanel: '#0B1017',
  bgPanelElevated: '#111A24',
  lineSoft: 'rgba(203, 213, 225, 0.09)',
  lineHot: 'rgba(245, 177, 63, 0.42)',
  accentAmber: '#F5B13F',
  accentAmberDark: '#D88A1E',
  signalCyan: '#38D5FF',
  signalCyanDark: '#0891B2',
  marginGreen: '#35D07F',
  riskRed: '#FF5D5D',
  textMain: '#EEF4F8',
  textMuted: 'rgba(238, 244, 248, 0.64)',
  textFaint: 'rgba(238, 244, 248, 0.42)',
  violet: '#9D7CFF',
  steel: '#8EA4B8',
} as const;

const BRAND = {
  primary: designTokens.signalCyan,
  primaryDark: designTokens.signalCyanDark,
  accent: designTokens.accentAmber,
  accentDark: designTokens.accentAmberDark,
  secondary: designTokens.marginGreen,
  violet: designTokens.violet,
  rose: designTokens.riskRed,
  success: designTokens.marginGreen,
  warning: designTokens.accentAmber,
  error: designTokens.riskRed,
  info: designTokens.signalCyan,

  bg: designTokens.bgCanvas,
  bgSubtle: '#080D13',
  surface: designTokens.bgPanel,
  surfaceLight: designTokens.bgPanelElevated,
  border: designTokens.lineSoft,
  borderHover: designTokens.lineHot,
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
    text: {
      primary: designTokens.textMain,
      secondary: designTokens.textMuted,
    },
    divider: BRAND.border,
  },
  typography: {
    fontFamily: "'IBM Plex Sans', system-ui, -apple-system, sans-serif",
    h3: { fontWeight: 700, letterSpacing: 0, fontFamily: "'Unbounded', 'IBM Plex Sans', sans-serif" },
    h4: { fontWeight: 700, letterSpacing: 0, fontFamily: "'Unbounded', 'IBM Plex Sans', sans-serif" },
    h5: { fontWeight: 700, letterSpacing: 0, fontFamily: "'Unbounded', 'IBM Plex Sans', sans-serif" },
    h6: { fontWeight: 700, fontFamily: "'IBM Plex Sans', sans-serif" },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    body1: { fontFamily: "'IBM Plex Sans', sans-serif", lineHeight: 1.6 },
    body2: { fontFamily: "'IBM Plex Sans', sans-serif", lineHeight: 1.6 },
    button: { fontFamily: "'IBM Plex Sans', sans-serif", fontWeight: 700 },
    caption: { fontFamily: "'IBM Plex Sans', sans-serif" },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    `0 1px 3px ${alpha('#000', 0.4)}, 0 1px 2px ${alpha('#000', 0.3)}`,
    `0 4px 8px ${alpha('#000', 0.35)}`,
    `0 6px 12px ${alpha('#000', 0.35)}`,
    `0 8px 16px ${alpha('#000', 0.35)}`,
    `0 12px 24px ${alpha('#000', 0.4)}`,
    `0 16px 32px ${alpha('#000', 0.4)}`,
    `0 20px 40px ${alpha('#000', 0.45)}`,
    `0 24px 48px ${alpha('#000', 0.45)}`,
    ...Array(16).fill('none') as string[],
  ] as unknown as typeof createTheme extends (o: infer O) => unknown ? O extends { shadows?: infer S } ? S : never : never,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage: `
            radial-gradient(ellipse 80% 48% at 50% -18%, ${alpha(BRAND.primary, 0.1)}, transparent 62%),
            radial-gradient(ellipse 42% 34% at 88% 100%, ${alpha(BRAND.accent, 0.07)}, transparent 68%),
            linear-gradient(180deg, ${BRAND.bg}, ${BRAND.bgSubtle})
          `,
          color: designTokens.textMain,
        },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: alpha(BRAND.bg, 0.9),
          backdropFilter: 'blur(16px)',
          borderBottom: `1px solid ${BRAND.border}`,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: `linear-gradient(90deg, transparent, ${alpha(BRAND.accent, 0.36)}, ${alpha(BRAND.primary, 0.28)}, transparent)`,
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: BRAND.surface,
          borderRight: `1px solid ${BRAND.border}`,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            bottom: 0,
            width: '2px',
            background: `linear-gradient(180deg, ${BRAND.accent}, ${BRAND.primary}, ${BRAND.secondary})`,
            opacity: 0.72,
          },
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: alpha(BRAND.surfaceLight, 0.62),
          border: `1px solid ${BRAND.border}`,
          backgroundImage: `linear-gradient(180deg, ${alpha('#fff', 0.035)}, transparent 44%)`,
          backdropFilter: 'blur(10px)',
          transition: 'border-color 0.2s ease, box-shadow 0.2s ease, transform 0.16s ease',
          position: 'relative' as const,
          overflow: 'hidden' as const,
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: 0,
            borderRadius: 'inherit',
            padding: '1px',
            background: `linear-gradient(135deg, ${alpha(BRAND.primary, 0.22)}, ${alpha(BRAND.accent, 0.18)}, ${alpha(BRAND.secondary, 0.12)})`,
            WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            WebkitMaskComposite: 'xor',
            maskComposite: 'exclude',
            pointerEvents: 'none',
            opacity: 0,
            transition: 'opacity 0.3s ease',
          },
          '&:hover': {
            borderColor: alpha(BRAND.accent, 0.22),
            boxShadow: `0 18px 48px ${alpha('#000', 0.28)}`,
            '&::before': {
              opacity: 1,
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          fontSize: '0.72rem',
          fontFamily: "'IBM Plex Sans', sans-serif",
          borderRadius: 6,
        },
        outlined: {
          borderColor: alpha(BRAND.accent, 0.15),
        },
        colorPrimary: {
          background: alpha(BRAND.primary, 0.12),
          color: BRAND.primary,
          borderColor: alpha(BRAND.primary, 0.2),
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        contained: {
          fontWeight: 700,
          textTransform: 'none' as const,
          boxShadow: 'none',
          background: `linear-gradient(135deg, ${BRAND.accent}, ${BRAND.primary})`,
          color: '#061018',
          transition: 'box-shadow 0.3s ease, transform 0.15s ease',
          '&:hover': {
            boxShadow: `0 8px 22px ${alpha(BRAND.accent, 0.24)}, 0 0 26px ${alpha(BRAND.primary, 0.18)}`,
            background: `linear-gradient(135deg, ${BRAND.accent}, ${BRAND.primary})`,
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        outlined: {
          textTransform: 'none' as const,
          borderColor: BRAND.border,
          '&:hover': {
            borderColor: BRAND.borderHover,
            backgroundColor: alpha(BRAND.accent, 0.04),
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
              transition: 'border-color 0.2s ease',
            },
            '&:hover fieldset': {
              borderColor: alpha(BRAND.accent, 0.2),
            },
            '&.Mui-focused fieldset': {
              borderColor: BRAND.primary,
            },
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          margin: '2px 8px',
          transition: 'all 0.2s ease',
          '&.Mui-selected': {
            background: alpha(BRAND.primary, 0.09),
            boxShadow: `inset 2px 0 0 ${BRAND.accent}, 0 0 18px ${alpha(BRAND.primary, 0.08)}`,
            '&:hover': {
              background: alpha(BRAND.primary, 0.12),
            },
          },
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          backgroundColor: alpha(BRAND.bg, 0.94),
          backdropFilter: 'blur(16px)',
          height: 48,
        },
      },
    },
    MuiBottomNavigationAction: {
      styleOverrides: {
        root: {
          minWidth: 0,
          padding: '4px 2px 3px',
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.62rem',
            lineHeight: 1.1,
            whiteSpace: 'nowrap',
          },
          '& .MuiSvgIcon-root': {
            fontSize: 20,
          },
          '&.Mui-selected': {
            color: BRAND.accent,
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backdropFilter: 'blur(8px)',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          fontWeight: 600,
          fontFamily: "'IBM Plex Sans', sans-serif",
          '&.Mui-selected': {
            color: BRAND.accent,
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          backgroundColor: BRAND.accent,
          height: 2,
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
          backgroundColor: alpha('#fff', 0.04),
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottomColor: BRAND.border,
        },
        head: {
          fontWeight: 700,
          fontFamily: "'IBM Plex Sans', sans-serif",
          color: designTokens.textMuted,
          fontSize: '0.75rem',
          textTransform: 'uppercase' as const,
          letterSpacing: 0,
        },
        body: {
          fontFamily: "'JetBrains Mono', 'IBM Plex Sans', monospace",
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
  gridLine: 'rgba(142,164,184,0.1)',
  axisLabel: 'rgba(238,244,248,0.56)',
  axisLine: 'rgba(238,244,248,0.12)',
  tooltipBg: alpha(BRAND.bg, 0.96),
  tooltipBorder: alpha(BRAND.accent, 0.32),
  areaOpacity: 0.1,
  series: [
    BRAND.primary,     // #38D5FF cyan
    BRAND.secondary,   // #35D07F green
    BRAND.violet,      // #9D7CFF violet
    BRAND.accent,      // #F5B13F amber
    BRAND.rose,        // #FF5D5D red
    '#38BDF8',         // sky-400
    '#FB923C',         // orange-400
  ],
};

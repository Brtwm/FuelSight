import { createTheme } from '@mui/material/styles';

export const appTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0a4e8a',
    },
    success: {
      main: '#1b7f3a',
    },
    warning: {
      main: '#9b6a00',
    },
    error: {
      main: '#b3261e',
    },
    background: {
      default: '#f5f7fa',
    },
  },
  shape: {
    borderRadius: 10,
  },
});

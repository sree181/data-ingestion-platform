import { createTheme } from '@mui/material/styles';

// Sophisticated Gray Theme - Based on Trendy Gray Palette Reference
export const sophisticatedGrayTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#495057',        // Gunmetal Gray
      light: '#6C757D',       // Medium Gray
      dark: '#343A40',        // Dark Gray
      contrastText: '#FFFFFF'
    },
    secondary: {
      main: '#69369E',        // Purple & Gray accent
      light: '#7951A8',       // Light Purple
      dark: '#565454',        // Dark Violet-Gray
      contrastText: '#FFFFFF'
    },
    background: {
      default: '#F8F9FA',     // Light Gray background
      paper: '#FFFFFF',       // Pure white for cards
      secondary: '#E9ECEF',   // Secondary background
    },
    text: {
      primary: '#1a202c',     // Dark text for readability
      secondary: '#4a5568',   // Medium text for secondary content
      disabled: '#ADB5BD',    // Light gray text for disabled
    },
    success: {
      main: '#2e7d32',        // Green for success
      light: '#4caf50',
      dark: '#1b5e20',
    },
    error: {
      main: '#d32f2f',        // Red for errors
      light: '#ef5350',
      dark: '#c62828',
    },
    warning: {
      main: '#ed6c02',        // Orange for warnings
      light: '#ff9800',
      dark: '#e65100',
    },
    info: {
      main: '#0288d1',        // Blue for info
      light: '#03a9f4',
      dark: '#01579b',
    },
    divider: '#DEE2E6',       // Light gray divider
    action: {
      hover: 'rgba(73, 80, 87, 0.04)',
      selected: 'rgba(73, 80, 87, 0.08)',
      disabled: 'rgba(73, 80, 87, 0.26)',
      disabledBackground: 'rgba(73, 80, 87, 0.12)',
    },
    // Custom gray scale for consistent usage
    grey: {
      50: '#F8F9FA',
      100: '#E9ECEF',
      200: '#DEE2E6',
      300: '#CED4DA',
      400: '#ADB5BD',
      500: '#6C757D',
      600: '#495057',
      700: '#343A40',
      800: '#232323',
      900: '#1F262A',
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", "Roboto", "Helvetica Neue", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '-0.01em',
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '-0.005em',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '-0.005em',
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.4,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 500,
          padding: '8px 16px',
          fontFamily: 'Inter',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(73, 80, 87, 0.15)',
          },
        },
        contained: {
          background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
          color: '#FFFFFF !important', // Force white text for all contained buttons
          '&:hover': {
            background: 'linear-gradient(135deg, #343A40 0%, #212529 100%)',
            color: '#FFFFFF !important', // Maintain white text on hover
          },
          '&:disabled': {
            background: 'rgba(0, 0, 0, 0.12)',
            color: 'rgba(0, 0, 0, 0.26) !important',
          },
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
          color: '#FFFFFF !important',
          '&:hover': {
            background: 'linear-gradient(135deg, #343A40 0%, #212529 100%)',
            color: '#FFFFFF !important',
          },
        },
        containedSecondary: {
          background: 'linear-gradient(135deg, #69369E 0%, #565454 100%)',
          color: '#FFFFFF !important',
          '&:hover': {
            background: 'linear-gradient(135deg, #565454 0%, #4a3f4a 100%)',
            color: '#FFFFFF !important',
          },
        },
        containedSuccess: {
          background: 'linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)',
          color: '#FFFFFF !important',
          '&:hover': {
            background: 'linear-gradient(135deg, #1b5e20 0%, #0d4f15 100%)',
            color: '#FFFFFF !important',
          },
        },
        containedError: {
          background: 'linear-gradient(135deg, #d32f2f 0%, #c62828 100%)',
          color: '#FFFFFF !important',
          '&:hover': {
            background: 'linear-gradient(135deg, #c62828 0%, #b71c1c 100%)',
            color: '#FFFFFF !important',
          },
        },
        containedWarning: {
          background: 'linear-gradient(135deg, #ed6c02 0%, #e65100 100%)',
          color: '#FFFFFF !important',
          '&:hover': {
            background: 'linear-gradient(135deg, #e65100 0%, #d84315 100%)',
            color: '#FFFFFF !important',
          },
        },
        containedInfo: {
          background: 'linear-gradient(135deg, #0288d1 0%, #01579b 100%)',
          color: '#FFFFFF !important',
          '&:hover': {
            background: 'linear-gradient(135deg, #01579b 0%, #014c7f 100%)',
            color: '#FFFFFF !important',
          },
        },
        outlined: {
          borderColor: '#DEE2E6',
          color: '#495057',
          backgroundColor: 'transparent',
          '&:hover': {
            borderColor: '#495057',
            backgroundColor: 'rgba(73, 80, 87, 0.04)',
            color: '#495057',
          },
        },
        text: {
          color: '#495057',
          '&:hover': {
            backgroundColor: 'rgba(73, 80, 87, 0.04)',
            color: '#495057',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 12px rgba(73, 80, 87, 0.08)',
          border: '1px solid rgba(222, 226, 230, 0.6)',
          backgroundColor: '#FFFFFF',
          '&:hover': {
            boxShadow: '0 4px 20px rgba(73, 80, 87, 0.12)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundColor: '#FFFFFF',
          boxShadow: '0 1px 8px rgba(73, 80, 87, 0.06)',
        },
        elevation1: {
          boxShadow: '0 1px 8px rgba(73, 80, 87, 0.06)',
        },
        elevation2: {
          boxShadow: '0 2px 12px rgba(73, 80, 87, 0.08)',
        },
        elevation3: {
          boxShadow: '0 4px 20px rgba(73, 80, 87, 0.12)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontFamily: 'Inter',
          fontWeight: 500,
        },
        outlined: {
          borderColor: '#DEE2E6',
          color: '#495057',
          backgroundColor: '#F8F9FA',
          '&:hover': {
            backgroundColor: '#E9ECEF',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: '#FFFFFF',
            '& fieldset': {
              borderColor: '#DEE2E6',
            },
            '&:hover fieldset': {
              borderColor: '#6C757D',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#495057',
            },
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #DEE2E6',
        },
        indicator: {
          backgroundColor: '#495057',
          height: 3,
          borderRadius: '3px 3px 0 0',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontFamily: 'Inter',
          fontWeight: 500,
          color: '#6C757D',
          '&.Mui-selected': {
            color: '#495057',
            fontWeight: 600,
          },
          '&:hover': {
            color: '#495057',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: '#212529',
          boxShadow: '0 1px 8px rgba(73, 80, 87, 0.06)',
          borderBottom: '1px solid #DEE2E6',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#FFFFFF',
          borderRight: '1px solid #DEE2E6',
          boxShadow: '2px 0 8px rgba(73, 80, 87, 0.06)',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 8px',
          '&:hover': {
            backgroundColor: 'rgba(73, 80, 87, 0.04)',
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(73, 80, 87, 0.08)',
            '&:hover': {
              backgroundColor: 'rgba(73, 80, 87, 0.12)',
            },
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontFamily: 'Inter',
        },
        standardInfo: {
          backgroundColor: '#E3F2FD',
          color: '#0C4377',
          border: '1px solid #BBDEFB',
        },
        standardSuccess: {
          backgroundColor: '#E8F5E8',
          color: '#2E7D32',
          border: '1px solid #C8E6C8',
        },
        standardWarning: {
          backgroundColor: '#FFF3E0',
          color: '#F57C00',
          border: '1px solid #FFCC02',
        },
        standardError: {
          backgroundColor: '#FFEBEE',
          color: '#C62828',
          border: '1px solid #FFCDD2',
        },
      },
    },
  },
});

// Dark theme variant for future use
export const sophisticatedGrayDarkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#6C757D',
      light: '#ADB5BD',
      dark: '#495057',
      contrastText: '#FFFFFF'
    },
    secondary: {
      main: '#7951A8',
      light: '#9DA9AD',
      dark: '#69369E',
      contrastText: '#FFFFFF'
    },
    background: {
      default: '#1F262A',
      paper: '#232323',
      secondary: '#343A40',
    },
    text: {
      primary: '#F8F9FA',
      secondary: '#ADB5BD',
      disabled: '#6C757D',
    },
    divider: '#495057',
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", "Roboto", "Helvetica Neue", "Arial", sans-serif',
    // Same typography structure as light theme but optimized for dark mode
  },
  components: {
    // Dark theme component overrides
  },
});

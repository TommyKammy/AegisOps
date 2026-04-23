import { createTheme } from "@mui/material/styles";

export const operatorTheme = createTheme({
  cssVariables: true,
  palette: {
    mode: "light",
    primary: {
      main: "#1f3a5f",
      dark: "#142742",
      light: "#4f688b",
    },
    secondary: {
      main: "#0f7a6c",
      dark: "#0a5248",
      light: "#4aa195",
    },
    error: {
      main: "#a63b32",
    },
    info: {
      main: "#225f8f",
    },
    success: {
      main: "#276443",
    },
    warning: {
      main: "#9a6400",
    },
    background: {
      default: "#eef2f6",
      paper: "#fdfdfb",
    },
    divider: "#d4dde7",
    text: {
      primary: "#162433",
      secondary: "#4c5d73",
    },
  },
  shape: {
    borderRadius: 16,
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    button: {
      fontWeight: 600,
      letterSpacing: "0.01em",
      textTransform: "none",
    },
    body1: {
      lineHeight: 1.65,
    },
    body2: {
      lineHeight: 1.6,
    },
    h4: {
      fontWeight: 700,
      letterSpacing: "-0.02em",
    },
    h6: {
      fontWeight: 700,
      letterSpacing: "-0.01em",
    },
  },
  components: {
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 14,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage:
            "linear-gradient(135deg, rgba(20,39,66,0.98), rgba(34,95,143,0.92))",
          boxShadow: "0 14px 30px rgba(20, 39, 66, 0.18)",
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 999,
          paddingInline: 18,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage:
            "linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,249,252,0.94))",
          boxShadow: "0 14px 28px rgba(22, 36, 51, 0.08)",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 600,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
        },
      },
    },
  },
});

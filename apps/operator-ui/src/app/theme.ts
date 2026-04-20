import { createTheme } from "@mui/material/styles";

export const operatorTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1f3a5f",
    },
    secondary: {
      main: "#0f7a6c",
    },
    background: {
      default: "#f5f7fb",
      paper: "#ffffff",
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
});

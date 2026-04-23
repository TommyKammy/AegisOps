import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes("/node_modules/@mui/") ||
            id.includes("/node_modules/@emotion/")
          ) {
            return "mui-vendor";
          }

          if (
            id.includes("/node_modules/react-admin/") ||
            id.includes("/node_modules/ra-core/") ||
            id.includes("/node_modules/ra-ui-materialui/")
          ) {
            return "react-admin-vendor";
          }

          return undefined;
        },
      },
    },
  },
  server: {
    port: 4173,
  },
});

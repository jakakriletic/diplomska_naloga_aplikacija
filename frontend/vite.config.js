import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Med razvojem (npm run dev) preusmeri /api na backend.
// V produkciji to opravi nginx.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendProxyTarget =
    env.VITE_BACKEND_PROXY_TARGET ?? "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": {
          target: backendProxyTarget,
          changeOrigin: true
        }
      }
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/setupTests.ts"
    }
  };
});

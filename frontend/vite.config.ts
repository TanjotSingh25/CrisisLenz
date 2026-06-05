import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on 0.0.0.0 so it works inside Docker too
    port: 5173,
    watch: {
      usePolling: true, // reliable file-watching on Windows / Docker bind mounts
    },
  },
});

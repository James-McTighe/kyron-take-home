import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/cite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0', // Necessary for Docker port mapping
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://server:8000', // Targets the backend container name
        changeOrigin: true,
        secure: false,
      },
    },
  },
});

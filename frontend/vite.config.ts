import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// No Docker o alvo é o serviço `backend`; rodando no host, o backend local (em IPv4:
// a porta publicada pelo compose só escuta em 127.0.0.1).
const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000'
// Bind mounts do Docker Desktop (Windows/macOS) não repassam eventos de arquivo.
const usePolling = process.env.VITE_USE_POLLING === 'true'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
    ...(usePolling && { watch: { usePolling: true, interval: 300 } }),
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    restoreMocks: true,
    unstubGlobals: true,
  },
})

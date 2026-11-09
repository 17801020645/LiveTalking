import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/console/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/offline': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/api/v1': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/api/recordings': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/api/asset': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
      '/record': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },

      '/api/live': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/api/avatar': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/api/assets': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/api/asr': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/offer': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/human': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
      '/interrupt_talk': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true, headers: { Origin: 'https://192.168.31.75:8010' } },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})

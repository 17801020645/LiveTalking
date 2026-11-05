import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/console/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/offline': { target: 'http://192.168.31.75:8012', changeOrigin: true },
      '/api/live': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
      '/api/assets': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
      '/api/asr': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
      '/offer': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
      '/human': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
      '/interrupt_talk': { target: 'https://192.168.31.75:8010', secure: false, changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})

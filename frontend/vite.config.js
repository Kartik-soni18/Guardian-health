import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/Guardian-health/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://4l16rbxyai.execute-api.ap-southeast-2.amazonaws.com/default',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})

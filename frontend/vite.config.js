import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // tout /api/* est relaye vers le backend Django (nom du service docker)
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})

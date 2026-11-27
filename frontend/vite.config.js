import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // toute requete /api/* est relayee vers le backend Django.
      // 'backend' est le nom du service docker-compose : Docker le resout
      // en IP du conteneur. Resultat : une seule URL (localhost:5173)
      // pour le front ET l'API -> meme origine, pas de probleme CORS.
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})

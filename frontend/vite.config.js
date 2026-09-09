import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // sockjs-client (dépendance de la connexion WebSocket temps réel) est
  // écrit pour Node.js et référence "global", absent des navigateurs.
  // Webpack le fournissait automatiquement ; Vite ne le fait pas par
  // défaut -- on le définit explicitement comme alias de "window".
  define: {
    global: 'window',
  },
})
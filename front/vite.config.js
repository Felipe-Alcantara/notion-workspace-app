import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // O Django serve o bundle abaixo de /static/frontend/.
  base: '/static/frontend/',
  build: {
    // O artefato entra no pacote Python e é servido pelo Django em produção.
    outDir: '../server/static/frontend',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

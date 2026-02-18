import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Expose on all network interfaces (0.0.0.0)
    port: 3000,
    allowedHosts: ['yupiterit.uz'],
    proxy: {
      '/api': {
        target: 'http://yupiterit.uz',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://yupiterit.uz',
        ws: true,
      },
    },
  },
})

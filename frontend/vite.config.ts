import path from 'node:path'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [
    tanstackRouter({ target: 'react', autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // The mount tests render the whole app, charts included, and recharts is
    // slow under jsdom — several seconds for a page with a curve and a pie.
    // The default 5s turns that cost into flakes rather than failures.
    testTimeout: 20000,
    globals: false,
    include: ['src/**/*.test.{ts,tsx}'],
  },
  server: {
    // The backend is the origin of truth for /api; proxying keeps the client
    // free of hardcoded hosts and avoids CORS in dev. Override the target with
    // VITE_API_TARGET when port 8000 is taken by another project.
    proxy: {
      '/api': process.env.VITE_API_TARGET ?? 'http://localhost:8000',
    },
  },
})

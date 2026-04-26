import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['e2e/**', '**/e2e/**', '**/node_modules/**'],
    setupFiles: ['./src/test/setup.ts'],
    testTimeout: 10000,
  },
  build: {
    chunkSizeWarningLimit: 1400,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replaceAll('\\', '/');
          if (!normalizedId.includes('/node_modules/')) {
            return undefined;
          }
          if (
            normalizedId.includes('/react/') ||
            normalizedId.includes('/react-dom/') ||
            normalizedId.includes('/react-router-dom/')
          ) {
            return 'react';
          }
          if (
            normalizedId.includes('/@mui/') ||
            normalizedId.includes('/@emotion/')
          ) {
            return 'mui';
          }
          if (
            normalizedId.includes('/echarts/') ||
            normalizedId.includes('/echarts-for-react/')
          ) {
            return 'charts';
          }
          if (normalizedId.includes('/@tanstack/react-query/')) {
            return 'query';
          }
          if (
            normalizedId.includes('/react-hook-form/') ||
            normalizedId.includes('/@hookform/resolvers/') ||
            normalizedId.includes('/zod/')
          ) {
            return 'forms';
          }
          return undefined;
        },
      },
    },
  },
})

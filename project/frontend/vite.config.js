const { defineConfig } = require('vite');
const react = require('@vitejs/plugin-react');
const { resolve } = require('path');

module.exports = defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../desktop/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  server: {
    port: 3001,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/stream': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        secure: false,
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
});
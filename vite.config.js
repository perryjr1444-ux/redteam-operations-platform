import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import path from 'path';

export default defineConfig({
  plugins: [preact()],
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        // Main islands bundle
        islands: './frontend/islands.js',
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './frontend'),
      'react': 'preact/compat',
      'react-dom': 'preact/compat'
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5172',
      '/ws': {
        target: 'ws://localhost:5172',
        ws: true
      }
    }
  }
});

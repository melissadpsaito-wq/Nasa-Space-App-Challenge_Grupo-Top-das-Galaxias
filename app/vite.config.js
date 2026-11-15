import { defineConfig } from 'vite';
import { resolve } from 'node:path';

// GitHub Pages serve em /<repo>/; em dev a base é '/'.
// Domínio próprio (D17): build com VITE_BASE=/ .
const REPO_BASE = '/Nasa-Space-App-Challenge_Grupo-Top-das-Galaxias/';

export default defineConfig(({ command }) => ({
  base: process.env.BASE_PATH ?? '/Nasa-Space-App-Challenge_Grupo-Top-das-Galaxias',
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      input: { index: resolve(__dirname, 'index.html'), mapa: resolve(__dirname, 'mapa.html') },
    },
  },
}));

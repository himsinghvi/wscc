import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// PWA (feature 10): makes the site installable ("download as app") and, once
// installed, it opens as a standalone window that is still the web app.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'robots.txt'],
      manifest: {
        name: 'WSCC — Weekend Cricket League',
        short_name: 'WSCC',
        description: 'Availability voting, rankings, scheduling & tournaments for the weekend cricket league.',
        theme_color: '#0d6efd',
        background_color: '#0b1324',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/'),
            handler: 'NetworkFirst',
            options: { cacheName: 'app-shell' },
          },
        ],
      },
    }),
  ],
  // In dev (vite + uvicorn separately), proxy /api to the backend keeping the prefix.
  server: { port: 5173, proxy: { '/api': { target: 'http://localhost:8077', changeOrigin: true } } },
})

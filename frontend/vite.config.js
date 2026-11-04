import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export function canonicalAuthOrigin(req, res, next) {
  const match = /^127\.0\.0\.1(?::(\d+))?$/.exec(req.headers.host || '');
  if (match && req.method === 'GET' && req.headers.accept?.includes('text/html') && req.url?.startsWith('/') && !req.url.startsWith('/api/')) {
    res.writeHead(307, { Location: `http://localhost${match[1] ? ':' + match[1] : ''}${req.url}`, 'Cache-Control':'no-store' });
    res.end(); return;
  }
  next();
}
export default defineConfig({
  plugins: [react(), { name:'canonical-local-auth-origin', configureServer(server) { server.middlewares.use(canonicalAuthOrigin); }, configurePreviewServer(server) { server.middlewares.use(canonicalAuthOrigin); } }],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});

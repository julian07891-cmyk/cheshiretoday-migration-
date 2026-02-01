const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy ads.txt to backend for Ezoic redirect
  app.use(
    '/ads.txt',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
      pathRewrite: {
        '^/ads.txt': '/api/ads.txt',
      },
    })
  );
  
  // Proxy robots.txt to backend
  app.use(
    '/robots.txt',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
      pathRewrite: {
        '^/robots.txt': '/api/robots.txt',
      },
    })
  );
};

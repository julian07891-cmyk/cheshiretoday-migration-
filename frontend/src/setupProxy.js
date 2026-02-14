const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  // IMPORTANT:
  // Do NOT mount at "/api" or "/ws" because Express strips the prefix.
  // Instead, proxy by "context" so the full path is preserved.
  app.use(
    createProxyMiddleware(["/api", "/ws"], {
      target: "http://127.0.0.1:8000",
      changeOrigin: true,
      ws: true,
    })
  );
};

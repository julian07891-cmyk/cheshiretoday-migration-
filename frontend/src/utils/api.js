export const getApiUrl = () => {
  // If explicitly set at build time, always prefer it
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }

  if (typeof window !== "undefined") {
    const { hostname, origin } = window.location;

    // Local dev: frontend :3000, backend :8000
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return "http://127.0.0.1:8000";
    }

    // Render split-deploy: frontend and backend are on different origins
    // If frontend hostname contains "frontend", derive backend hostname automatically.
    if (hostname.endsWith("onrender.com") && hostname.includes("frontend")) {
      const backendHost = hostname.replace("frontend", "backend");
      return "https://" + backendHost;
    }

    // Default: same-origin (useful once you reverse-proxy backend under the main domain)
    return origin;
  }

  return "";
};

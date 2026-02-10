export const getApiUrl = () => {
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }

  if (typeof window !== "undefined") {
    const { hostname } = window.location;

    // Local dev: frontend :3000, backend :8000
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return "http://127.0.0.1:8000";
    }

    // Production: same origin
    return window.location.origin;
  }

  return "";
};

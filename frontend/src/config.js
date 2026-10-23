/**
 * Centralized API configuration for Claro.
 * Dynamically resolves API base address for localhost, local network (mobile devices),
 * or production deployments.
 */

export function getApiBase() {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }

  // Vite development or preview port
  if (window.location.port === "5173" || window.location.port === "4173") {
    // Vite proxy forwards /health, /documents, etc.
    return "";
  }

  // Same origin when served through backend
  if (window.location.port === "8000") {
    return "";
  }

  // If accessing from a mobile device on local Wi-Fi (e.g. 192.168.x.x:5173 or other port)
  if (
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1" &&
    window.location.hostname !== ""
  ) {
    // If not proxied, point to host on port 8000
    if (window.location.port !== "") {
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return "";
  }

  return "http://127.0.0.1:8000";
}

export const API_BASE = getApiBase();

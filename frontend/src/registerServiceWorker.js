/**
 * PWA Service Worker Registration & Installation Manager
 */

let deferredPrompt = null;
let installableListeners = [];

export function registerServiceWorker() {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
    return;
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        // Check for updates
        registration.addEventListener("updatefound", () => {
          const installingWorker = registration.installing;
          if (installingWorker) {
            installingWorker.addEventListener("statechange", () => {
              if (
                installingWorker.state === "installed" &&
                navigator.serviceWorker.controller
              ) {
                // New content available, dispatch update event
                window.dispatchEvent(new CustomEvent("claro:pwa-update-ready"));
              }
            });
          }
        });
      })
      .catch((error) => {
        console.warn("[PWA] Service Worker registration failed:", error);
      });
  });

  // Capture install prompt
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installableListeners.forEach((callback) => callback(true));
    window.dispatchEvent(new CustomEvent("claro:pwa-installable", { detail: { installable: true } }));
  });

  // Track install completion
  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    installableListeners.forEach((callback) => callback(false));
    window.dispatchEvent(new CustomEvent("claro:pwa-installed"));
  });
}

export function subscribeInstallable(callback) {
  installableListeners.push(callback);
  if (deferredPrompt) {
    callback(true);
  }
  return () => {
    installableListeners = installableListeners.filter((cb) => cb !== callback);
  };
}

export async function promptPwaInstall() {
  if (!deferredPrompt) {
    return false;
  }
  deferredPrompt.prompt();
  const choiceResult = await deferredPrompt.userChoice;
  if (choiceResult.outcome === "accepted") {
    deferredPrompt = null;
    return true;
  }
  return false;
}

export function isStandalone() {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true ||
    document.referrer.includes("android-app://")
  );
}

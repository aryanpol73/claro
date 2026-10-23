import React from "react";
import { IconSparkles } from "./Icons";
import { promptPwaInstall } from "../registerServiceWorker";
import logoImg from "../assets/claro-logo-sm.png";

export function InstallPromptModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const isIos =
    typeof navigator !== "undefined" &&
    /iPad|iPhone|iPod/.test(navigator.userAgent) &&
    !window.MSStream;

  async function handleInstallClick() {
    const installed = await promptPwaInstall();
    if (installed) {
      onClose();
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card animate-fade-in"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "440px", padding: "28px 24px" }}
      >
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <div
            style={{
              width: "72px",
              height: "72px",
              margin: "0 auto 14px auto",
              borderRadius: "18px",
              overflow: "hidden",
              boxShadow: "0 8px 24px -4px var(--primary-glow)",
              border: "1.5px solid var(--border-accent)",
              background: "#090b10",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <img
              src={logoImg}
              alt="Claro Logo"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
          <h3 style={{ fontSize: "19px", fontWeight: "700", marginBottom: "6px" }}>
            Install Claro App
          </h3>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
            Experience Claro as an ultra-fast, standalone Progressive Web App on your phone, tablet, or desktop.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "10px",
            marginBottom: "24px",
            background: "var(--bg-elevated)",
            padding: "14px 16px",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "13px" }}>
            <span style={{ color: "var(--emerald)" }}>✓</span>
            <span>Full-screen standalone window with zero browser bars</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "13px" }}>
            <span style={{ color: "var(--emerald)" }}>✓</span>
            <span>Optimized touch gestures and bottom navigation</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "13px" }}>
            <span style={{ color: "var(--emerald)" }}>✓</span>
            <span>Fast offline shell precaching & instant resumption</span>
          </div>
        </div>

        {isIos ? (
          <div
            style={{
              padding: "12px 14px",
              background: "var(--primary-light)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-accent)",
              fontSize: "12.5px",
              lineHeight: "1.5",
              color: "var(--text-primary)",
              marginBottom: "18px",
            }}
          >
            <strong>To install on iOS Safari:</strong>
            <ol style={{ paddingLeft: "18px", marginTop: "6px" }}>
              <li>Tap the <strong>Share</strong> button in Safari toolbar.</li>
              <li>Scroll down and tap <strong>"Add to Home Screen"</strong>.</li>
            </ol>
          </div>
        ) : (
          <button
            onClick={handleInstallClick}
            className="pwa-install-btn"
            style={{
              width: "100%",
              padding: "12px",
              background: "var(--primary)",
              color: "#ffffff",
              borderRadius: "var(--radius-md)",
              fontWeight: "600",
              fontSize: "14px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              marginBottom: "12px",
              boxShadow: "var(--shadow-md)",
            }}
          >
            <IconSparkles size={16} />
            <span>Install to Device</span>
          </button>
        )}

        <button
          onClick={onClose}
          style={{
            width: "100%",
            padding: "10px",
            color: "var(--text-muted)",
            fontSize: "13px",
            textAlign: "center",
          }}
        >
          Maybe later
        </button>
      </div>
    </div>
  );
}

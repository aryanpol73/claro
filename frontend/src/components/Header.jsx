import React from "react";
import {
  IconSparkles,
  IconLayers,
  IconBookOpen,
  IconFilePdf,
  IconSun,
  IconMoon,
  IconShieldCheck,
  IconShieldAlert,
  IconUploadCloud,
  IconDownload,
} from "./Icons";
import logoImg from "../assets/claro-logo-sm.png";

export function Header({
  activeMode,
  setActiveMode,
  systemStatus,
  onOpenSetup,
  documentCount = 0,
  theme,
  toggleTheme,
  onOpenMobileSidebar,
  onOpenInstall,
  isInstallable = false,
}) {
  const isConfigured =
    (systemStatus?.llm_configured ||
      systemStatus?.groq_configured ||
      systemStatus?.gemini_configured) &&
    systemStatus?.pinecone_configured;

  const modes = [
    { id: "qa", label: "Research Q&A", icon: IconSparkles },
    { id: "synthesis", label: "Paper Synthesis", icon: IconLayers },
    { id: "reader", label: "Document Reader", icon: IconBookOpen },
    { id: "library", label: "Library", icon: IconFilePdf },
  ];

  return (
    <header className="app-header glass-panel">
      {/* Brand & Identity + Mobile Menu Toggle */}
      <div className="header-brand-group">
        {/* Mobile Sidebar Toggle Button */}
        <button
          onClick={onOpenMobileSidebar}
          className="header-mobile-sidebar-btn"
          title="Open Papers Drawer"
          type="button"
          aria-label="Toggle Document Library Drawer"
        >
          <IconUploadCloud size={18} />
          {documentCount > 0 && <span className="mobile-badge">{documentCount}</span>}
        </button>

        <div className="header-logo-badge">
          <img
            src={logoImg}
            alt="Claro Logo"
            className="header-logo-img"
          />
        </div>

        <div className="header-brand-text">
          <div className="brand-title-row">
            <span className="brand-title">CLARO</span>
            <span className="version-badge">v1.0</span>
          </div>
          <span className="brand-subtitle">Academic Research Workspace</span>
        </div>
      </div>

      {/* Desktop Navigation Modes (Hidden on Mobile) */}
      <nav className="header-desktop-nav" aria-label="Desktop Navigation Modes">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isActive = activeMode === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode.id)}
              className={`header-mode-btn ${isActive ? "active" : ""}`}
              title={mode.label}
              type="button"
            >
              <Icon size={16} />
              <span>{mode.label}</span>
              {mode.id === "library" && documentCount > 0 && (
                <span className="badge-count">{documentCount}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Actions & Status */}
      <div className="header-actions-group">
        {/* PWA Install Button (if available or manual install guide) */}
        {onOpenInstall && (
          <button
            onClick={onOpenInstall}
            className={`header-action-btn install-app-btn ${isInstallable ? "ready-to-install" : ""}`}
            title={isInstallable ? "Click to install Claro PWA" : "Install Claro PWA"}
            type="button"
          >
            <IconDownload size={15} />
            <span className="btn-label-desktop">Install App</span>
            {isInstallable && <span className="install-pulse-dot" />}
          </button>
        )}

        {/* Status Pill */}
        <button
          onClick={onOpenSetup}
          className={`header-status-pill ${isConfigured ? "ready" : "needs-setup"}`}
          title={isConfigured ? "Services connected and operational" : "Configure API Keys"}
          type="button"
        >
          {isConfigured ? <IconShieldCheck size={14} /> : <IconShieldAlert size={14} />}
          <span className="status-text">{isConfigured ? "System Ready" : "Setup Keys"}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="header-icon-btn"
          title={theme === "dark" ? "Switch to Scholarly Light" : "Switch to Obsidian Dark"}
          type="button"
          aria-label="Toggle Theme"
        >
          {theme === "dark" ? <IconSun size={17} /> : <IconMoon size={17} />}
        </button>
      </div>
    </header>
  );
}

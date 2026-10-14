import React from "react";
import {
  IconLogo,
  IconSparkles,
  IconLayers,
  IconBookOpen,
  IconFilePdf,
  IconSun,
  IconMoon,
  IconShieldCheck,
  IconShieldAlert,
} from "./Icons";

export function Header({
  activeMode,
  setActiveMode,
  systemStatus,
  onOpenSetup,
  documentCount = 0,
  theme,
  toggleTheme,
}) {
  const isConfigured = (systemStatus?.llm_configured || systemStatus?.groq_configured || systemStatus?.gemini_configured) && systemStatus?.pinecone_configured;

  const modes = [
    { id: "qa", label: "Research Q&A", icon: IconSparkles },
    { id: "synthesis", label: "Paper Synthesis", icon: IconLayers },
    { id: "reader", label: "Document Reader", icon: IconBookOpen },
    { id: "library", label: "Library", icon: IconFilePdf },
  ];

  return (
    <header style={styles.header} className="glass-panel">
      {/* Brand & Identity */}
      <div style={styles.brandGroup}>
        <div style={styles.logoBadge}>
          <IconLogo size={24} />
        </div>
        <div>
          <div style={styles.brandTitleRow}>
            <span style={styles.brandTitle}>CLARO</span>
            <span style={styles.versionBadge}>v1.0</span>
          </div>
          <span style={styles.brandSubtitle}>Academic Research Workspace</span>
        </div>
      </div>

      {/* Navigation Modes */}
      <nav style={styles.navModes}>
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isActive = activeMode === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode.id)}
              style={{
                ...styles.modeButton,
                ...(isActive ? styles.modeButtonActive : {}),
              }}
              title={mode.label}
            >
              <Icon size={16} />
              <span>{mode.label}</span>
              {mode.id === "library" && documentCount > 0 && (
                <span style={styles.badgeCount}>{documentCount}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Actions & Status */}
      <div style={styles.actionsGroup}>
        {/* Status Pill */}
        <button
          onClick={onOpenSetup}
          style={{
            ...styles.statusPill,
            backgroundColor: isConfigured ? "var(--emerald-bg)" : "var(--amber-bg)",
            borderColor: isConfigured ? "var(--emerald-border)" : "var(--amber-border)",
            color: isConfigured ? "var(--emerald)" : "var(--amber)",
          }}
          title={isConfigured ? "Services connected and operational" : "Configure API Keys"}
        >
          {isConfigured ? <IconShieldCheck size={14} /> : <IconShieldAlert size={14} />}
          <span>{isConfigured ? "System Ready" : "Setup Keys"}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          style={styles.iconButton}
          title={theme === "dark" ? "Switch to Scholarly Light" : "Switch to Obsidian Dark"}
        >
          {theme === "dark" ? <IconSun size={17} /> : <IconMoon size={17} />}
        </button>
      </div>
    </header>
  );
}

const styles = {
  header: {
    height: "64px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    borderBottom: "1px solid var(--border-subtle)",
    zIndex: 30,
    userSelect: "none",
  },
  brandGroup: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  logoBadge: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "36px",
    height: "36px",
    borderRadius: "var(--radius-md)",
    background: "rgba(99, 102, 241, 0.12)",
    border: "1px solid var(--border-accent)",
  },
  brandTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  brandTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: "19px",
    fontWeight: "800",
    letterSpacing: "0.08em",
    color: "var(--text-primary)",
    background: "linear-gradient(135deg, #ffffff 40%, #a5b4fc 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
  },
  versionBadge: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    fontWeight: "600",
    padding: "1px 6px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    border: "1px solid var(--border-accent)",
  },
  brandSubtitle: {
    fontSize: "12px",
    color: "var(--text-muted)",
    display: "block",
    marginTop: "-2px",
  },
  navModes: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    backgroundColor: "var(--bg-card)",
    padding: "4px",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--border-subtle)",
  },
  modeButton: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "7px 14px",
    fontSize: "13.5px",
    fontWeight: "500",
    color: "var(--text-secondary)",
    borderRadius: "var(--radius-md)",
    transition: "all var(--trans-fast)",
  },
  modeButtonActive: {
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-primary)",
    fontWeight: "600",
    boxShadow: "var(--shadow-sm)",
  },
  badgeCount: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    padding: "1px 6px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
  },
  actionsGroup: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  statusPill: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "5px 12px",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "var(--radius-full)",
    border: "1px solid",
    transition: "all var(--trans-fast)",
  },
  iconButton: {
    width: "36px",
    height: "36px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "var(--radius-md)",
    color: "var(--text-secondary)",
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-subtle)",
  },
};

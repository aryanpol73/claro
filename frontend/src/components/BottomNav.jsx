import React from "react";
import {
  IconSparkles,
  IconLayers,
  IconBookOpen,
  IconFilePdf,
  IconUploadCloud,
} from "./Icons";

export function BottomNav({
  activeMode,
  setActiveMode,
  documentCount = 0,
  onOpenMobileSidebar,
  isMobileSidebarOpen = false,
}) {
  const navItems = [
    {
      id: "qa",
      label: "Q&A",
      icon: IconSparkles,
      onClick: () => setActiveMode("qa"),
      isActive: activeMode === "qa" && !isMobileSidebarOpen,
    },
    {
      id: "synthesis",
      label: "Synthesis",
      icon: IconLayers,
      onClick: () => setActiveMode("synthesis"),
      isActive: activeMode === "synthesis" && !isMobileSidebarOpen,
    },
    {
      id: "sidebar",
      label: "Papers",
      icon: IconUploadCloud,
      onClick: onOpenMobileSidebar,
      isActive: isMobileSidebarOpen,
      badge: documentCount > 0 ? documentCount : null,
      highlight: true,
    },
    {
      id: "reader",
      label: "Reader",
      icon: IconBookOpen,
      onClick: () => setActiveMode("reader"),
      isActive: activeMode === "reader" && !isMobileSidebarOpen,
    },
    {
      id: "library",
      label: "Library",
      icon: IconFilePdf,
      onClick: () => setActiveMode("library"),
      isActive: activeMode === "library" && !isMobileSidebarOpen,
    },
  ];

  return (
    <nav className="bottom-nav-bar" aria-label="Mobile Navigation">
      <div className="bottom-nav-inner">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.isActive;
          return (
            <button
              key={item.id}
              onClick={item.onClick}
              className={`bottom-nav-item ${active ? "active" : ""} ${
                item.highlight ? "highlight-action" : ""
              }`}
              title={item.label}
              type="button"
            >
              <div className="bottom-nav-icon-wrap">
                <Icon size={20} />
                {item.badge !== null && item.badge !== undefined && (
                  <span className="bottom-nav-badge">{item.badge}</span>
                )}
                {active && <span className="bottom-nav-indicator" />}
              </div>
              <span className="bottom-nav-label">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

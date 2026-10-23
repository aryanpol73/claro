import React, { useState, useRef } from "react";
import {
  IconSearch,
  IconUploadCloud,
  IconFilePdf,
  IconTrash,
  IconEye,
  IconSparkles,
  IconBookOpen,
  IconRefresh,
} from "./Icons";

export function Sidebar({
  documents = [],
  selectedDocumentId,
  onSelectDocument,
  multiSelectedIds = [],
  onToggleMultiSelect,
  onUploadFile,
  onDeleteDocument,
  onOpenReader,
  onRefresh,
  isUploading,
  collapsed = false,
  mobileOpen = false,
  onCloseMobile,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const filteredDocs = documents.filter((doc) => {
    const name = doc.original_filename || doc.name || "";
    return name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave() {
    setIsDragOver(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUploadFile(e.dataTransfer.files[0]);
    }
  }

  function handleFileChange(e) {
    if (e.target.files && e.target.files.length > 0) {
      onUploadFile(e.target.files[0]);
      e.target.value = "";
    }
  }

  function handleScopeAndClose(docId) {
    onSelectDocument(docId);
    if (onCloseMobile) onCloseMobile();
  }

  function handleReaderAndClose(docId) {
    onOpenReader(docId);
    if (onCloseMobile) onCloseMobile();
  }

  if (collapsed && !mobileOpen) return null;

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        {/* Mobile Drawer Top Bar */}
        <div className="sidebar-mobile-header">
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <IconBookOpen size={18} style={{ color: "var(--primary)" }} />
            <span style={{ fontWeight: "700", fontSize: "14px" }}>Library Papers</span>
            <span className="badge-count">{documents.length}</span>
          </div>
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="sidebar-mobile-close-btn"
              title="Close drawer"
              type="button"
            >
              ✕
            </button>
          )}
        </div>
      {/* Upload Drop Zone */}
      <div style={styles.uploadSection}>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            ...styles.dropZone,
            borderColor: isDragOver ? "var(--primary)" : "var(--border-medium)",
            backgroundColor: isDragOver ? "var(--primary-light)" : "var(--bg-card)",
          }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx,.pptx,.ppt"
            style={{ display: "none" }}
          />
          <div style={styles.uploadIconWrap}>
            <IconUploadCloud size={20} className={isUploading ? "animate-spin" : ""} />
          </div>
          <div>
            <div style={styles.uploadTextPrimary}>
              {isUploading ? "Ingesting & indexing..." : "Upload Academic Paper"}
            </div>
            <div style={styles.uploadTextSub}>Drag & drop PDF / DOCX / PPTX (max 50 MB)</div>
          </div>
        </div>
      </div>

      {/* Library Controls & Search */}
      <div style={styles.controlsSection}>
        <div style={styles.searchWrap}>
          <IconSearch size={15} style={styles.searchIcon} />
          <input
            type="text"
            placeholder="Filter papers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={styles.searchInput}
          />
        </div>
        <button
          onClick={onRefresh}
          style={styles.refreshBtn}
          title="Refresh library"
        >
          <IconRefresh size={14} />
        </button>
      </div>

      {/* Scope Status Pill */}
      <div style={styles.scopeBanner}>
        {selectedDocumentId ? (
          <div style={styles.scopedPill}>
            <span>Scoped to 1 paper</span>
            <button
              onClick={() => onSelectDocument("")}
              style={styles.clearScopeBtn}
              title="Search across all papers"
            >
              Reset to All
            </button>
          </div>
        ) : (
          <div style={styles.allScopedPill}>
            <span>Scope: All {documents.length} Papers</span>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div style={styles.documentsList}>
        {filteredDocs.length === 0 ? (
          <div style={styles.emptyState}>
            <IconBookOpen size={32} style={{ color: "var(--text-muted)", marginBottom: "8px" }} />
            <div style={styles.emptyTitle}>No documents yet</div>
            <p style={styles.emptySub}>
              {searchQuery ? "No papers matched your search." : "Drop research papers above to index and ask questions."}
            </p>
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const docId = doc.document_id;
            const isScoped = selectedDocumentId === docId;
            const isMultiSelected = multiSelectedIds.includes(docId);
            const title = doc.original_filename || doc.name || "Untitled Paper";
            const pages = doc.total_pages ? `${doc.total_pages} pp` : null;
            const chunks = doc.total_chunks ? `${doc.total_chunks} chunks` : null;
            const size = doc.size_mb ? `${doc.size_mb} MB` : null;

            return (
              <div
                key={docId}
                style={{
                  ...styles.docCard,
                  borderColor: isScoped ? "var(--primary)" : "var(--border-subtle)",
                  backgroundColor: isScoped ? "rgba(99, 102, 241, 0.08)" : "var(--bg-card)",
                }}
              >
                {/* Header row */}
                <div style={styles.cardHeader}>
                  <div style={styles.checkboxTitleWrap}>
                    <input
                      type="checkbox"
                      checked={isMultiSelected}
                      onChange={() => onToggleMultiSelect(docId)}
                      style={styles.checkbox}
                      title="Select for multi-paper synthesis/comparison"
                    />
                    <div style={styles.docIconWrap}>
                      <IconFilePdf size={16} />
                    </div>
                    <span style={styles.docTitle} title={title}>
                      {title}
                    </span>
                  </div>
                </div>

                {/* Metadata badges */}
                <div style={styles.metaRow}>
                  {pages && <span style={styles.metaBadge}>{pages}</span>}
                  {chunks && <span style={styles.metaBadge}>{chunks}</span>}
                  {size && <span style={styles.metaBadge}>{size}</span>}
                  {doc.status === "failed" && (
                    <span style={{ ...styles.metaBadge, color: "var(--rose)" }}>Error</span>
                  )}
                </div>

                {/* Actions row */}
                <div style={styles.cardActions}>
                  <button
                    onClick={() => {
                      if (isScoped) {
                        onSelectDocument("");
                      } else {
                        handleScopeAndClose(docId);
                      }
                    }}
                    style={{
                      ...styles.actionBtn,
                      color: isScoped ? "var(--primary)" : "var(--text-secondary)",
                      backgroundColor: isScoped ? "var(--primary-light)" : "var(--bg-elevated)",
                    }}
                    title={isScoped ? "Clear single-paper filter" : "Ask questions scoped only to this paper"}
                  >
                    <IconSparkles size={13} />
                    <span>{isScoped ? "Scoped" : "Scope Q&A"}</span>
                  </button>

                  <button
                    onClick={() => handleReaderAndClose(docId)}
                    style={styles.actionBtnSecondary}
                    title="Read & inspect PDF document"
                  >
                    <IconEye size={13} />
                    <span>Read</span>
                  </button>

                  <button
                    onClick={() => onDeleteDocument(docId, title)}
                    style={styles.deleteBtn}
                    title="Delete document and purge vectors"
                  >
                    <IconTrash size={13} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
    </>
  );
}

const styles = {
  sidebar: {
    width: "330px",
    minWidth: "330px",
    height: "100%",
    backgroundColor: "var(--bg-sidebar)",
    borderRight: "1px solid var(--border-subtle)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  uploadSection: {
    padding: "16px 16px 8px 16px",
  },
  dropZone: {
    padding: "16px 14px",
    borderRadius: "var(--radius-lg)",
    border: "1.5px dashed var(--border-medium)",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    cursor: "pointer",
    transition: "all var(--trans-fast)",
  },
  uploadIconWrap: {
    width: "36px",
    height: "36px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  uploadTextPrimary: {
    fontSize: "13px",
    fontWeight: "600",
    color: "var(--text-primary)",
  },
  uploadTextSub: {
    fontSize: "11px",
    color: "var(--text-muted)",
    marginTop: "2px",
  },
  controlsSection: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 16px",
  },
  searchWrap: {
    position: "relative",
    flex: 1,
  },
  searchIcon: {
    position: "absolute",
    left: "10px",
    top: "50%",
    transform: "translateY(-50%)",
    color: "var(--text-muted)",
    pointerEvents: "none",
  },
  searchInput: {
    width: "100%",
    padding: "7px 10px 7px 32px",
    fontSize: "13px",
    borderRadius: "var(--radius-md)",
  },
  refreshBtn: {
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-subtle)",
    color: "var(--text-secondary)",
  },
  scopeBanner: {
    padding: "4px 16px 8px 16px",
  },
  scopedPill: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "4px 10px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    fontSize: "12px",
    fontWeight: "600",
  },
  clearScopeBtn: {
    fontSize: "11px",
    color: "var(--primary)",
    textDecoration: "underline",
    fontWeight: "500",
  },
  allScopedPill: {
    padding: "4px 10px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-muted)",
    fontSize: "12px",
    fontWeight: "500",
  },
  documentsList: {
    flex: 1,
    overflowY: "auto",
    padding: "0 16px 16px 16px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  emptyState: {
    padding: "40px 16px",
    textAlign: "center",
    color: "var(--text-muted)",
  },
  emptyTitle: {
    fontSize: "14px",
    fontWeight: "600",
    color: "var(--text-secondary)",
    marginBottom: "4px",
  },
  emptySub: {
    fontSize: "12px",
    lineHeight: "1.4",
  },
  docCard: {
    padding: "12px",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--border-subtle)",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    transition: "all var(--trans-fast)",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  checkboxTitleWrap: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    overflow: "hidden",
    flex: 1,
  },
  checkbox: {
    accentColor: "var(--primary)",
    cursor: "pointer",
  },
  docIconWrap: {
    color: "var(--primary)",
    flexShrink: 0,
    display: "flex",
  },
  docTitle: {
    fontSize: "13px",
    fontWeight: "600",
    color: "var(--text-primary)",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  metaRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    flexWrap: "wrap",
  },
  metaBadge: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    padding: "2px 6px",
    borderRadius: "4px",
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-muted)",
  },
  cardActions: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginTop: "2px",
  },
  actionBtn: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "4px 8px",
    fontSize: "11.5px",
    fontWeight: "600",
    borderRadius: "var(--radius-sm)",
    transition: "all var(--trans-fast)",
  },
  actionBtnSecondary: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "4px 8px",
    fontSize: "11.5px",
    fontWeight: "500",
    color: "var(--text-secondary)",
    backgroundColor: "var(--bg-elevated)",
    borderRadius: "var(--radius-sm)",
  },
  deleteBtn: {
    marginLeft: "auto",
    padding: "4px 6px",
    color: "var(--text-muted)",
    borderRadius: "var(--radius-sm)",
    transition: "color var(--trans-fast)",
  },
};

import React, { useState } from "react";
import {
  IconFilePdf,
  IconSearch,
  IconSparkles,
  IconEye,
  IconDownload,
  IconTrash,
  IconBookOpen,
} from "./Icons";
import { getApiBase } from "../config";

export function LibraryView({
  documents = [],
  onSelectDoc,
  onScopeToDoc,
  onDeleteDoc,
}) {
  const [search, setSearch] = useState("");

  const filtered = documents.filter((d) => {
    const name = d.original_filename || d.name || "";
    return name.toLowerCase().includes(search.toLowerCase());
  });

  const totalPages = documents.reduce((acc, d) => acc + (d.total_pages || 0), 0);
  const totalChunks = documents.reduce((acc, d) => acc + (d.total_chunks || 0), 0);
  const totalMb = documents.reduce((acc, d) => acc + (d.size_mb || 0), 0);

  return (
    <div style={styles.container}>
      {/* Header & Stats Banner */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Academic Document Library</h2>
          <p style={styles.subtitle}>
            Organize, inspect, and manage indexed research publications and vector embeddings.
          </p>
        </div>

        {/* Aggregate Stats */}
        <div style={styles.statsRow}>
          <div style={styles.statCard}>
            <div style={styles.statNum}>{documents.length}</div>
            <div style={styles.statLabel}>Documents</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNum}>{totalPages}</div>
            <div style={styles.statLabel}>Indexed Pages</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNum}>{totalChunks}</div>
            <div style={styles.statLabel}>Vector Chunks</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNum}>{totalMb.toFixed(1)} MB</div>
            <div style={styles.statLabel}>Total Storage</div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div style={styles.filterBar}>
        <div style={styles.searchWrap}>
          <IconSearch size={16} style={styles.searchIcon} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search papers by filename or topic..."
            style={styles.searchInput}
          />
        </div>
      </div>

      {/* Table of Documents */}
      <div style={styles.tableWrap}>
        {filtered.length === 0 ? (
          <div style={styles.emptyState}>
            <IconBookOpen size={36} style={{ color: "var(--text-muted)", marginBottom: "8px" }} />
            <h4>No documents found</h4>
            <p>Upload a document from the sidebar to populate the library.</p>
          </div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr style={styles.thRow}>
                <th style={{ ...styles.th, width: "40%" }}>Document Title</th>
                <th style={styles.th}>Pages</th>
                <th style={styles.th}>Chunks</th>
                <th style={styles.th}>Size</th>
                <th style={styles.th}>Uploaded</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((doc) => {
                const title = doc.original_filename || doc.name;
                const pdfUrl = `${getApiBase()}/documents/${doc.document_id}/file`;
                const dateStr = doc.uploaded_at
                  ? new Date(doc.uploaded_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })
                  : "—";

                return (
                  <tr key={doc.document_id} style={styles.tr}>
                    <td style={styles.td}>
                      <div style={styles.docCell}>
                        <IconFilePdf size={18} style={{ color: "var(--primary)", flexShrink: 0 }} />
                        <span style={styles.docName} title={title}>
                          {title}
                        </span>
                      </div>
                    </td>
                    <td style={styles.td}>{doc.total_pages || "—"}</td>
                    <td style={styles.td}>{doc.total_chunks || "—"}</td>
                    <td style={styles.td}>{doc.size_mb ? `${doc.size_mb} MB` : "—"}</td>
                    <td style={styles.td}>{dateStr}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      <div style={styles.rowActions}>
                        <button
                          onClick={() => onScopeToDoc(doc.document_id, title)}
                          style={styles.actionBtnPrimary}
                          title="Ask questions on this paper"
                        >
                          <IconSparkles size={12} />
                          <span>Scope Q&A</span>
                        </button>
                        <button
                          onClick={() => onSelectDoc(doc.document_id)}
                          style={styles.actionBtn}
                          title="Open in Document Reader"
                        >
                          <IconEye size={12} />
                          <span>Read</span>
                        </button>
                        <a
                          href={pdfUrl}
                          target="_blank"
                          rel="noreferrer"
                          style={styles.actionBtn}
                          title="Download PDF"
                        >
                          <IconDownload size={12} />
                        </a>
                        <button
                          onClick={() => onDeleteDoc(doc.document_id, title)}
                          style={styles.deleteBtn}
                          title="Delete from disk and Pinecone"
                        >
                          <IconTrash size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    height: "100%",
    overflow: "hidden",
    backgroundColor: "var(--bg-app)",
    padding: "24px 32px",
    gap: "20px",
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "16px",
  },
  title: {
    fontSize: "22px",
    fontWeight: "700",
  },
  subtitle: {
    fontSize: "14px",
    color: "var(--text-secondary)",
    marginTop: "2px",
  },
  statsRow: {
    display: "flex",
    gap: "12px",
  },
  statCard: {
    padding: "10px 18px",
    backgroundColor: "var(--bg-card)",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--border-subtle)",
    textAlign: "center",
  },
  statNum: {
    fontSize: "18px",
    fontWeight: "800",
    color: "var(--primary)",
    fontFamily: "var(--font-mono)",
  },
  statLabel: {
    fontSize: "11px",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    fontFamily: "var(--font-mono)",
    marginTop: "2px",
  },
  filterBar: {
    display: "flex",
    alignItems: "center",
  },
  searchWrap: {
    position: "relative",
    width: "360px",
  },
  searchIcon: {
    position: "absolute",
    left: "12px",
    top: "50%",
    transform: "translateY(-50%)",
    color: "var(--text-muted)",
  },
  searchInput: {
    width: "100%",
    padding: "8px 12px 8px 36px",
    fontSize: "13.5px",
    borderRadius: "var(--radius-md)",
  },
  tableWrap: {
    flex: 1,
    overflowY: "auto",
    backgroundColor: "var(--bg-card)",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--border-subtle)",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    textAlign: "left",
  },
  thRow: {
    borderBottom: "1px solid var(--border-subtle)",
    backgroundColor: "var(--bg-elevated)",
  },
  th: {
    padding: "12px 16px",
    fontSize: "12px",
    fontFamily: "var(--font-mono)",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    fontWeight: "600",
  },
  tr: {
    borderBottom: "1px solid var(--border-subtle)",
    transition: "background var(--trans-fast)",
  },
  td: {
    padding: "14px 16px",
    fontSize: "13.5px",
    color: "var(--text-secondary)",
  },
  docCell: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  docName: {
    fontWeight: "600",
    color: "var(--text-primary)",
    maxWidth: "340px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  rowActions: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: "8px",
  },
  actionBtnPrimary: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "4px 10px",
    fontSize: "11.5px",
    fontWeight: "600",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    borderRadius: "var(--radius-sm)",
  },
  actionBtn: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "4px 8px",
    fontSize: "11.5px",
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-secondary)",
    borderRadius: "var(--radius-sm)",
  },
  deleteBtn: {
    padding: "4px 8px",
    color: "var(--rose)",
    borderRadius: "var(--radius-sm)",
  },
  emptyState: {
    padding: "60px 20px",
    textAlign: "center",
    color: "var(--text-muted)",
  },
};

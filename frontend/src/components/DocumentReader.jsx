import React, { useState } from "react";
import {
  IconFilePdf,
  IconSparkles,
  IconDownload,
  IconCopy,
  IconCheck,
  IconBookOpen,
} from "./Icons";
import { getApiBase } from "../config";

export function DocumentReader({
  documents = [],
  activeDocId,
  onSelectDoc,
  targetPage = 1,
  onScopeToDoc,
}) {
  const selectedDoc =
    (activeDocId ? documents.find((d) => d.document_id === activeDocId) : null) ||
    documents[0] ||
    null;

  const [summary, setSummary] = useState(null);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  const activeSummary = summary || selectedDoc?.summary || null;

  async function handleGenerateBrief() {
    if (!selectedDoc) return;
    setIsSummarizing(true);
    try {
      const res = await fetch(`${getApiBase()}/documents/${selectedDoc.document_id}/summarize`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.summary) {
        setSummary(data.summary);
      } else if (data.error) {
        alert(data.error);
      }
    } catch (e) {
      console.error("Summarization error:", e);
      alert("Failed to generate executive brief.");
    } finally {
      setIsSummarizing(false);
    }
  }

  function copyHash() {
    if (!selectedDoc?.document_id) return;
    navigator.clipboard.writeText(selectedDoc.document_id);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  }

  if (documents.length === 0) {
    return (
      <div style={styles.emptyContainer}>
        <IconBookOpen size={44} style={{ color: "var(--text-muted)", marginBottom: "16px" }} />
        <h3 style={styles.emptyTitle}>No Academic Documents Loaded</h3>
        <p style={styles.emptySub}>
          Upload a research PDF or DOCX using the sidebar to read documents and inspect evidence.
        </p>
      </div>
    );
  }

  const pdfUrl = selectedDoc
    ? `${getApiBase()}/documents/${selectedDoc.document_id}/file#page=${targetPage || 1}`
    : "";

  return (
    <div style={styles.container}>
      {/* Top Document Selector Bar */}
      <div style={styles.selectorBar} className="glass-panel">
        <div style={styles.selectorLeft}>
          <IconFilePdf size={18} style={{ color: "var(--primary)" }} />
          <select
            value={selectedDoc?.document_id || ""}
            onChange={(e) => {
              const doc = documents.find((d) => d.document_id === e.target.value);
              setSummary(doc?.summary || null);
              if (onSelectDoc) onSelectDoc(e.target.value);
            }}
            style={styles.docSelect}
          >
            {documents.map((d) => (
              <option key={d.document_id} value={d.document_id}>
                {d.original_filename || d.name} ({d.total_pages || '?'} pp)
              </option>
            ))}
          </select>
        </div>

        <div style={styles.selectorRight}>
          <button
            onClick={() => onScopeToDoc(selectedDoc?.document_id, selectedDoc?.original_filename || selectedDoc?.name)}
            style={styles.scopeBtn}
          >
            <IconSparkles size={14} />
            <span>Ask This Paper</span>
          </button>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            style={styles.downloadLink}
            title="Open PDF in new browser tab"
          >
            <IconDownload size={14} />
            <span>Open Raw PDF</span>
          </a>
        </div>
      </div>

      {/* Main Split View: PDF Viewer + Academic Brief */}
      <div style={styles.splitView}>
        {/* PDF Frame */}
        <div style={styles.viewerPane}>
          {pdfUrl ? (
            <iframe
              key={`${selectedDoc?.document_id}-${targetPage || 1}`}
              src={pdfUrl}
              title={selectedDoc?.original_filename || "Document Viewer"}
              style={styles.iframe}
            />
          ) : (
            <div style={styles.emptyFrame}>Select a document to preview.</div>
          )}
        </div>

        {/* Document Metadata & Executive Brief Pane */}
        <div style={styles.detailsPane}>
          {selectedDoc && (
            <div style={styles.detailsContent}>
              <div style={styles.metaCard}>
                <h3 style={styles.metaTitle}>{selectedDoc.original_filename || selectedDoc.name}</h3>

                <div style={styles.statsGrid}>
                  <div style={styles.statBox}>
                    <div style={styles.statLabel}>Pages</div>
                    <div style={styles.statVal}>{selectedDoc.total_pages || "—"}</div>
                  </div>
                  <div style={styles.statBox}>
                    <div style={styles.statLabel}>Chunks</div>
                    <div style={styles.statVal}>{selectedDoc.total_chunks || "—"}</div>
                  </div>
                  <div style={styles.statBox}>
                    <div style={styles.statLabel}>File Size</div>
                    <div style={styles.statVal}>{selectedDoc.size_mb ? `${selectedDoc.size_mb} MB` : "—"}</div>
                  </div>
                </div>

                <div style={styles.hashRow}>
                  <span style={styles.hashLabel}>SHA-256:</span>
                  <code style={styles.hashCode} title={selectedDoc.document_id}>
                    {selectedDoc.document_id.slice(0, 16)}…{selectedDoc.document_id.slice(-8)}
                  </code>
                  <button onClick={copyHash} style={styles.copyHashBtn} title="Copy full SHA-256 hash">
                    {copiedHash ? <IconCheck size={12} /> : <IconCopy size={12} />}
                  </button>
                </div>
              </div>

              {/* Executive Brief Section */}
              <div style={styles.briefCard}>
                <div style={styles.briefHeader}>
                  <h4 style={styles.briefTitle}>Academic Executive Brief</h4>
                  <button
                    onClick={handleGenerateBrief}
                    disabled={isSummarizing}
                    style={{
                      ...styles.generateBriefBtn,
                      opacity: isSummarizing ? 0.6 : 1,
                    }}
                  >
                    <IconSparkles size={13} className={isSummarizing ? "animate-spin" : ""} />
                    <span>{isSummarizing ? "Analyzing..." : activeSummary ? "Regenerate" : "Generate Brief"}</span>
                  </button>
                </div>

                {isSummarizing ? (
                  <div style={styles.summarizingBox}>
                    <div className="animate-spin" style={styles.briefSpinner} />
                    <p style={styles.briefLoadingText}>
                      Extracting key objectives, methodology, contributions, and limitations...
                    </p>
                  </div>
                ) : activeSummary ? (
                  <div style={styles.summaryBody}>
                    {activeSummary}
                  </div>
                ) : (
                  <div style={styles.noSummaryBox}>
                    <p style={styles.noSummaryText}>
                      No executive brief generated yet for this paper. Click <strong>Generate Brief</strong> to extract a structured academic breakdown.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
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
  },
  selectorBar: {
    padding: "10px 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid var(--border-subtle)",
  },
  selectorLeft: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  docSelect: {
    padding: "6px 12px",
    fontSize: "13.5px",
    fontWeight: "600",
    borderRadius: "var(--radius-md)",
    maxWidth: "420px",
  },
  selectorRight: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  scopeBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 14px",
    fontSize: "12.5px",
    fontWeight: "600",
    backgroundColor: "var(--primary)",
    color: "#ffffff",
    borderRadius: "var(--radius-md)",
  },
  downloadLink: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 12px",
    fontSize: "12.5px",
    color: "var(--text-secondary)",
    backgroundColor: "var(--bg-elevated)",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--border-subtle)",
  },
  splitView: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },
  viewerPane: {
    flex: 1,
    height: "100%",
    backgroundColor: "#1e1e24",
    borderRight: "1px solid var(--border-subtle)",
  },
  iframe: {
    width: "100%",
    height: "100%",
    border: "none",
  },
  emptyFrame: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    color: "var(--text-muted)",
  },
  detailsPane: {
    width: "420px",
    minWidth: "380px",
    height: "100%",
    overflowY: "auto",
    padding: "20px",
    backgroundColor: "var(--bg-sidebar)",
  },
  detailsContent: {
    display: "flex",
    flexDirection: "column",
    gap: "18px",
  },
  metaCard: {
    padding: "18px",
    backgroundColor: "var(--bg-card)",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--border-subtle)",
  },
  metaTitle: {
    fontSize: "16px",
    fontWeight: "700",
    marginBottom: "14px",
    wordBreak: "break-word",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: "8px",
    marginBottom: "14px",
  },
  statBox: {
    padding: "8px 10px",
    backgroundColor: "var(--bg-elevated)",
    borderRadius: "var(--radius-md)",
    textAlign: "center",
  },
  statLabel: {
    fontSize: "10.5px",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    fontFamily: "var(--font-mono)",
  },
  statVal: {
    fontSize: "14px",
    fontWeight: "700",
    color: "var(--text-primary)",
    marginTop: "2px",
  },
  hashRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "11.5px",
  },
  hashLabel: {
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
  },
  hashCode: {
    color: "var(--primary)",
    fontSize: "11px",
  },
  copyHashBtn: {
    color: "var(--text-muted)",
    padding: "2px 4px",
  },
  briefCard: {
    padding: "18px",
    backgroundColor: "var(--bg-card)",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--border-subtle)",
  },
  briefHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "14px",
  },
  briefTitle: {
    fontSize: "13.5px",
    fontWeight: "700",
    fontFamily: "var(--font-heading)",
  },
  generateBriefBtn: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "4px 10px",
    fontSize: "11.5px",
    fontWeight: "600",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    borderRadius: "var(--radius-sm)",
  },
  summaryBody: {
    fontSize: "13px",
    lineHeight: "1.65",
    color: "var(--text-secondary)",
    whiteSpace: "pre-line",
  },
  noSummaryBox: {
    padding: "24px 12px",
    textAlign: "center",
  },
  noSummaryText: {
    fontSize: "12.5px",
    color: "var(--text-muted)",
    lineHeight: "1.5",
  },
  summarizingBox: {
    padding: "30px 12px",
    textAlign: "center",
  },
  briefSpinner: {
    width: "24px",
    height: "24px",
    borderRadius: "50%",
    border: "2px solid var(--primary-light)",
    borderTopColor: "var(--primary)",
    margin: "0 auto 10px auto",
  },
  briefLoadingText: {
    fontSize: "12px",
    color: "var(--text-muted)",
  },
  emptyContainer: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px",
    textAlign: "center",
  },
  emptyTitle: {
    fontSize: "18px",
    fontWeight: "600",
    marginBottom: "8px",
  },
  emptySub: {
    fontSize: "14px",
    color: "var(--text-secondary)",
    maxWidth: "480px",
  },
};

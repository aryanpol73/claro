import React, { useState } from "react";
import {
  IconX,
  IconShieldCheck,
  IconShieldAlert,
  IconRefresh,
  IconExternalLink,
  IconSparkles,
} from "./Icons";
import { getApiBase } from "../config";

export function SetupModal({ isOpen, onClose, systemStatus, onRefresh }) {
  const [groqKey, setGroqKey] = useState("");
  const [googleKey, setGoogleKey] = useState("");
  const [pineconeKey, setPineconeKey] = useState("");
  const [pineconeIndex, setPineconeIndex] = useState("academic-files-rag");
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStatus, setIndexStatus] = useState(null);

  if (!isOpen) return null;

  const groqOk = systemStatus?.groq_configured || systemStatus?.llm_configured;
  const pineconeOk = systemStatus?.pinecone_configured;

  async function handleSaveCredentials(e) {
    if (e) e.preventDefault();
    if (!groqKey.trim() && !pineconeKey.trim() && !googleKey.trim()) return;
    setIsSaving(true);
    setSaveStatus(null);
    try {
      const res = await fetch(`${getApiBase()}/config/keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          groq_api_key: groqKey.trim() || undefined,
          google_api_key: googleKey.trim() || undefined,
          pinecone_api_key: pineconeKey.trim() || undefined,
          pinecone_index_name: pineconeIndex.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setSaveStatus({ type: "success", message: "API credentials saved and activated!" });
        setGroqKey("");
        setGoogleKey("");
        setPineconeKey("");
        if (onRefresh) onRefresh();
      } else {
        setSaveStatus({ type: "error", message: data.detail || "Failed to save credentials." });
      }
    } catch (err) {
      console.error("Save credentials error:", err);
      setSaveStatus({ type: "error", message: "Network error saving credentials." });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleIndexAll() {
    setIsIndexing(true);
    setIndexStatus(null);
    try {
      const res = await fetch(`${getApiBase()}/documents/index-all`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        setIndexStatus({ type: "success", message: `Indexed ${data.indexed_count} documents into vector store.` });
        if (onRefresh) onRefresh();
      } else {
        setIndexStatus({ type: "error", message: data.detail || "Indexing failed." });
      }
    } catch (err) {
      console.error("Index all error:", err);
      setIndexStatus({ type: "error", message: "Network error triggering indexing." });
    } finally {
      setIsIndexing(false);
    }
  }

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()} className="animate-fade-in">
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.titleGroup}>
            <h3 style={styles.title}>System Architecture & Credentials</h3>
            <p style={styles.subtitle}>Configure Groq and Pinecone for Claro research workspace.</p>
          </div>
          <button onClick={onClose} style={styles.closeBtn}>
            <IconX size={18} />
          </button>
        </div>

        {/* Status items */}
        <div style={styles.body}>
          {/* Groq item */}
          <div style={styles.statusCard}>
            <div style={styles.cardTop}>
              <div style={styles.serviceName}>
                <strong>Groq LLM Platform</strong>
                <span style={styles.serviceRole}>High-Speed Inference & Cite-or-Refuse Generation</span>
              </div>
              <span
                style={{
                  ...styles.statusTag,
                  backgroundColor: groqOk ? "var(--emerald-bg)" : "var(--amber-bg)",
                  color: groqOk ? "var(--emerald)" : "var(--amber)",
                  borderColor: groqOk ? "var(--emerald-border)" : "var(--amber-border)",
                }}
              >
                {groqOk ? <IconShieldCheck size={13} /> : <IconShieldAlert size={13} />}
                <span>{groqOk ? "Configured" : "Key Missing"}</span>
              </span>
            </div>
            {!groqOk && (
              <div style={styles.helpText}>
                <span>Get a free, high-rate-limit key from Groq Console:</span>
                <a
                  href="https://console.groq.com/keys"
                  target="_blank"
                  rel="noreferrer"
                  style={styles.keyLink}
                >
                  <span>Get Groq API Key</span>
                  <IconExternalLink size={12} />
                </a>
              </div>
            )}
          </div>

          {/* Pinecone item */}
          <div style={styles.statusCard}>
            <div style={styles.cardTop}>
              <div style={styles.serviceName}>
                <strong>Pinecone Vector Database</strong>
                <span style={styles.serviceRole}>Serverless Vector Storage & Hybrid Retrieval</span>
              </div>
              <span
                style={{
                  ...styles.statusTag,
                  backgroundColor: pineconeOk ? "var(--emerald-bg)" : "var(--amber-bg)",
                  color: pineconeOk ? "var(--emerald)" : "var(--amber)",
                  borderColor: pineconeOk ? "var(--emerald-border)" : "var(--amber-border)",
                }}
              >
                {pineconeOk ? <IconShieldCheck size={13} /> : <IconShieldAlert size={13} />}
                <span>{pineconeOk ? "Configured" : "Key Missing"}</span>
              </span>
            </div>
            {!pineconeOk && (
              <div style={styles.helpText}>
                <span>Get a free serverless index from Pinecone:</span>
                <a
                  href="https://app.pinecone.io/"
                  target="_blank"
                  rel="noreferrer"
                  style={styles.keyLink}
                >
                  <span>Get Pinecone API Key</span>
                  <IconExternalLink size={12} />
                </a>
              </div>
            )}
          </div>

          {/* Interactive Credential Input Card */}
          <div style={styles.formCard}>
            <h4 style={styles.formTitle}>Connect API Keys</h4>
            <p style={styles.formDesc}>
              Enter your Groq and Pinecone keys below to activate vector retrieval and grounded synthesis.
            </p>

            <form onSubmit={handleSaveCredentials} style={styles.form}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Groq API Key</label>
                <input
                  type="password"
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  placeholder={groqOk ? "•••••••••••••••••••••••• (Configured)" : "Paste gsk_... key"}
                  style={styles.input}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Pinecone API Key</label>
                <input
                  type="password"
                  value={pineconeKey}
                  onChange={(e) => setPineconeKey(e.target.value)}
                  placeholder={pineconeOk ? "•••••••••••••••••••••••• (Configured)" : "Paste pcsk_... key"}
                  style={styles.input}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Pinecone Index Name</label>
                <input
                  type="text"
                  value={pineconeIndex}
                  onChange={(e) => setPineconeIndex(e.target.value)}
                  placeholder="academic-files-rag"
                  style={styles.input}
                />
              </div>

              {saveStatus && (
                <div
                  style={{
                    ...styles.feedback,
                    color: saveStatus.type === "success" ? "var(--emerald)" : "var(--rose)",
                  }}
                >
                  {saveStatus.message}
                </div>
              )}

              <button
                type="submit"
                disabled={isSaving || (!groqKey.trim() && !pineconeKey.trim() && !googleKey.trim())}
                style={{
                  ...styles.submitBtn,
                  opacity: (!groqKey.trim() && !pineconeKey.trim() && !googleKey.trim()) || isSaving ? 0.6 : 1,
                }}
              >
                {isSaving ? "Saving & Connecting..." : "Save & Activate Keys"}
              </button>
            </form>
          </div>

          {/* Batch Index Action (if vector store is configured) */}
          {pineconeOk && (
            <div style={styles.indexSection}>
              <button
                type="button"
                onClick={handleIndexAll}
                disabled={isIndexing}
                style={styles.indexAllBtn}
              >
                <IconSparkles size={14} />
                <span>{isIndexing ? "Indexing Library..." : "Index All Pending Documents"}</span>
              </button>
              {indexStatus && (
                <span
                  style={{
                    fontSize: "12px",
                    color: indexStatus.type === "success" ? "var(--emerald)" : "var(--rose)",
                  }}
                >
                  {indexStatus.message}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <button onClick={onRefresh} style={styles.refreshBtn}>
            <IconRefresh size={14} />
            <span>Re-check Services</span>
          </button>
          <button onClick={onClose} style={styles.doneBtn}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    backdropFilter: "blur(6px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 100,
    padding: "20px",
  },
  modal: {
    width: "100%",
    maxWidth: "540px",
    maxHeight: "90vh",
    backgroundColor: "var(--bg-card)",
    borderRadius: "var(--radius-xl)",
    border: "1px solid var(--border-medium)",
    boxShadow: "var(--shadow-lg)",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    padding: "20px 24px",
    borderBottom: "1px solid var(--border-subtle)",
  },
  titleGroup: {
    flex: 1,
  },
  title: {
    fontSize: "17px",
    fontWeight: "700",
  },
  subtitle: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    marginTop: "2px",
  },
  closeBtn: {
    color: "var(--text-muted)",
    padding: "4px",
    background: "none",
    border: "none",
    cursor: "pointer",
  },
  body: {
    padding: "20px 24px",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    overflowY: "auto",
  },
  statusCard: {
    padding: "14px 16px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-elevated)",
    border: "1px solid var(--border-subtle)",
  },
  cardTop: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  serviceName: {
    display: "flex",
    flexDirection: "column",
    fontSize: "14px",
  },
  serviceRole: {
    fontSize: "11.5px",
    color: "var(--text-muted)",
    marginTop: "1px",
  },
  statusTag: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "3px 8px",
    borderRadius: "var(--radius-full)",
    fontSize: "11.5px",
    fontWeight: "600",
    border: "1px solid",
  },
  helpText: {
    marginTop: "10px",
    paddingTop: "8px",
    borderTop: "1px solid var(--border-subtle)",
    fontSize: "12px",
    color: "var(--text-secondary)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "8px",
  },
  keyLink: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "12px",
    fontWeight: "600",
    color: "var(--primary)",
    textDecoration: "none",
  },
  formCard: {
    padding: "16px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-app)",
    border: "1px solid var(--border-subtle)",
  },
  formTitle: {
    fontSize: "13.5px",
    fontWeight: "700",
    marginBottom: "4px",
  },
  formDesc: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    marginBottom: "12px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  inputGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  label: {
    fontSize: "12px",
    fontWeight: "600",
    color: "var(--text-secondary)",
  },
  input: {
    padding: "8px 12px",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-medium)",
    color: "var(--text-primary)",
    fontSize: "12.5px",
    fontFamily: "inherit",
    outline: "none",
  },
  submitBtn: {
    marginTop: "6px",
    padding: "9px 16px",
    backgroundColor: "var(--primary)",
    color: "#ffffff",
    fontWeight: "600",
    fontSize: "13px",
    borderRadius: "var(--radius-md)",
    border: "none",
    cursor: "pointer",
  },
  feedback: {
    fontSize: "12px",
    fontWeight: "600",
  },
  indexSection: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 16px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-elevated)",
    border: "1px solid var(--border-subtle)",
  },
  indexAllBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 14px",
    backgroundColor: "var(--emerald)",
    color: "#ffffff",
    borderRadius: "var(--radius-md)",
    border: "none",
    fontSize: "12.5px",
    fontWeight: "600",
    cursor: "pointer",
  },
  footer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 24px",
    borderTop: "1px solid var(--border-subtle)",
    backgroundColor: "var(--bg-sidebar)",
    marginTop: "auto",
  },
  refreshBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "12.5px",
    color: "var(--text-secondary)",
    padding: "6px 10px",
    background: "none",
    border: "none",
    cursor: "pointer",
  },
  doneBtn: {
    padding: "7px 18px",
    backgroundColor: "var(--primary)",
    color: "#ffffff",
    fontWeight: "600",
    fontSize: "13px",
    borderRadius: "var(--radius-md)",
    border: "none",
    cursor: "pointer",
  },
};

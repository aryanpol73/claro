import React, { useState } from "react";
import {
  IconLayers,
  IconCompare,
  IconSparkles,
  IconDownload,
  IconCopy,
  IconCheck,
  IconFilePdf,
} from "./Icons";

export function SynthesisWorkspace({
  documents = [],
  multiSelectedIds = [],
  onToggleMultiSelect,
  onRunSynthesis,
  isSynthesizing = false,
  synthesisResult = null,
}) {
  const [topic, setTopic] = useState("");
  const [copied, setCopied] = useState(false);

  const presetTemplates = [
    {
      label: "Compare Methods",
      prompt: "Compare the core research objectives, assumptions, and methodologies across these works.",
    },
    {
      label: "Datasets & Metrics",
      prompt: "Contrast experimental datasets, evaluation benchmarks, and reported performance metrics.",
    },
    {
      label: "Consensus & Conflicts",
      prompt: "Identify points of consensus, conflicting findings, and unsolved limitations between sources.",
    },
    {
      label: "Historical Trajectory",
      prompt: "Synthesize the historical trajectory and evolving state-of-the-art across these papers.",
    },
  ];

  function handleSubmit(e) {
    if (e) e.preventDefault();
    if (!topic.trim() || isSynthesizing) return;

    onRunSynthesis(topic.trim(), multiSelectedIds);
  }

  function copyResult() {
    if (!synthesisResult?.answer) return;
    navigator.clipboard.writeText(synthesisResult.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadReport() {
    if (!synthesisResult?.answer) return;
    const content = `# Claro Academic Synthesis Report\n\n**Topic:** ${topic}\n**Date:** ${new Date().toISOString()}\n**Documents Synthesized:** ${multiSelectedIds.length > 0 ? `${multiSelectedIds.length} selected papers` : "All library documents"}\n\n${synthesisResult.answer}\n\n## References\n${(synthesisResult.citations || []).map((c, i) => `[${i + 1}] ${c.source} (Page ${c.page || 'N/A'}):\n> ${c.snippet}\n`).join("\n")}`;
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `claro_synthesis_report_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function renderFormattedSynthesis(text, citations = []) {
    if (!text) return null;
    const lines = text.split("\n");
    return lines.map((line, lIdx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        return <div key={lIdx} style={{ height: "8px" }} />;
      }
      if (trimmed.startsWith("### ")) {
        return (
          <h4 key={lIdx} style={styles.sectionHeading}>
            {trimmed.replace("### ", "")}
          </h4>
        );
      }
      if (trimmed.startsWith("## ")) {
        return (
          <h3 key={lIdx} style={styles.majorHeading}>
            {trimmed.replace("## ", "")}
          </h3>
        );
      }

      const parts = line.split(/(\[\d+\])/g);
      return (
        <p key={lIdx} style={styles.synthesisParagraph}>
          {parts.map((part, pIdx) => {
            const match = part.match(/\[(\d+)\]/);
            if (match) {
              const idx = parseInt(match[1], 10);
              const cite = citations[idx - 1];
              return (
                <span
                  key={pIdx}
                  style={styles.inlineCitationPill}
                  title={cite ? `${cite.source} (Page ${cite.page || 'N/A'})` : `Source [${idx}]`}
                >
                  {part}
                </span>
              );
            }
            return part;
          })}
        </p>
      );
    });
  }

  return (
    <div style={styles.container}>
      {/* Configuration Header */}
      <div style={styles.configHeader}>
        <div style={styles.titleRow}>
          <div style={styles.iconWrap}>
            <IconLayers size={22} />
          </div>
          <div>
            <h2 style={styles.title}>Multi-Paper Knowledge Synthesis</h2>
            <p style={styles.subtitle}>
              Synthesize findings across research papers. Claro contrasts methodologies, maps consensus,
              and isolates conflicting evidence with strict citations.
            </p>
          </div>
        </div>

        {/* Paper Selector Pills */}
        <div style={styles.paperSelectorSection}>
          <div style={styles.selectorLabel}>
            Target Papers ({multiSelectedIds.length > 0 ? `${multiSelectedIds.length} selected` : "All papers in library"}):
          </div>
          <div style={styles.paperChipsWrap}>
            {documents.length === 0 ? (
              <span style={styles.noPapersText}>Upload papers to enable multi-paper synthesis.</span>
            ) : (
              documents.map((doc) => {
                const isSelected = multiSelectedIds.includes(doc.document_id);
                const title = doc.original_filename || doc.name;
                return (
                  <button
                    key={doc.document_id}
                    onClick={() => onToggleMultiSelect(doc.document_id)}
                    style={{
                      ...styles.paperChip,
                      backgroundColor: isSelected ? "var(--primary)" : "var(--bg-elevated)",
                      color: isSelected ? "#ffffff" : "var(--text-secondary)",
                      borderColor: isSelected ? "var(--primary)" : "var(--border-subtle)",
                    }}
                  >
                    <IconFilePdf size={13} />
                    <span style={styles.chipText}>{title}</span>
                    {isSelected && <IconCheck size={12} />}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Synthesis Form */}
        <form onSubmit={handleSubmit} style={styles.synthesisForm}>
          <div style={styles.inputWrap}>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter a synthesis objective or research question to compare across papers..."
              rows={3}
              style={styles.textarea}
              disabled={isSynthesizing}
            />
          </div>

          <div style={styles.formFooter}>
            <div style={styles.presetGroup}>
              <span style={styles.presetLabel}>Academic Templates:</span>
              <div style={styles.presetButtons}>
                {presetTemplates.map((template, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setTopic(template.prompt)}
                    style={styles.presetBtn}
                  >
                    {template.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={!topic.trim() || isSynthesizing}
              style={{
                ...styles.synthesizeBtn,
                opacity: !topic.trim() || isSynthesizing ? 0.6 : 1,
              }}
            >
              <IconSparkles size={16} />
              <span>{isSynthesizing ? "Synthesizing Papers..." : "Generate Synthesis"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Synthesis Result Canvas */}
      <div style={styles.resultCanvas}>
        {isSynthesizing ? (
          <div style={styles.loadingContainer}>
            <div className="animate-spin" style={styles.spinner} />
            <h3 style={styles.loadingTitle}>Conducting Multi-Document Synthesis...</h3>
            <p style={styles.loadingSub}>
              Aggregating passages across selected documents, aligning comparative metrics,
              and formatting evidence with inline citations.
            </p>
          </div>
        ) : synthesisResult ? (
          <div style={styles.resultCard} className="animate-fade-in">
            <div style={styles.resultToolbar}>
              <div style={styles.resultStatus}>
                <span style={styles.statusBadge}>Verified Multi-Document Synthesis</span>
              </div>
              <div style={styles.toolbarActions}>
                <button onClick={copyResult} style={styles.toolBtn}>
                  {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </button>
                <button onClick={downloadReport} style={styles.toolBtn}>
                  <IconDownload size={14} />
                  <span>Download Report</span>
                </button>
              </div>
            </div>

            <div style={styles.resultBody}>
              {renderFormattedSynthesis(synthesisResult.answer, synthesisResult.citations)}
            </div>

            {/* Citations */}
            {synthesisResult.citations && synthesisResult.citations.length > 0 && (
              <div style={styles.citationsSection}>
                <h4 style={styles.citationsHeader}>
                  Synthesized Evidence Sources ({synthesisResult.citations.length})
                </h4>
                <div style={styles.citationsList}>
                  {synthesisResult.citations.map((c, i) => (
                    <div key={i} style={styles.citationRow}>
                      <span style={styles.citeIndex}>[{i + 1}]</span>
                      <div style={styles.citeDetails}>
                        <div style={styles.citeSourceRow}>
                          <strong style={{ color: "var(--text-primary)" }}>{c.source}</strong>
                          {c.page && <span style={styles.pageTag}>Page {c.page}</span>}
                        </div>
                        <p style={styles.citeSnippet}>"{c.snippet}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={styles.placeholderState}>
            <IconCompare size={40} style={{ color: "var(--text-muted)", marginBottom: "12px" }} />
            <h3 style={styles.placeholderTitle}>Select Papers & Define a Synthesis Objective</h3>
            <p style={styles.placeholderSub}>
              Choose 2 or more papers above or click a template to contrast methodologies,
              results, and theoretical findings in a structured academic overview.
            </p>
          </div>
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
  },
  configHeader: {
    padding: "20px 32px",
    borderBottom: "1px solid var(--border-subtle)",
    backgroundColor: "var(--bg-card)",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  titleRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "14px",
  },
  iconWrap: {
    width: "42px",
    height: "42px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  title: {
    fontSize: "20px",
    fontWeight: "700",
  },
  subtitle: {
    fontSize: "13.5px",
    color: "var(--text-secondary)",
    marginTop: "2px",
    maxWidth: "760px",
  },
  paperSelectorSection: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  selectorLabel: {
    fontSize: "12px",
    fontFamily: "var(--font-mono)",
    color: "var(--text-muted)",
    fontWeight: "600",
  },
  paperChipsWrap: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
  },
  paperChip: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "5px 10px",
    borderRadius: "var(--radius-full)",
    fontSize: "12px",
    fontWeight: "500",
    border: "1px solid",
    transition: "all var(--trans-fast)",
  },
  chipText: {
    maxWidth: "180px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  noPapersText: {
    fontSize: "12.5px",
    color: "var(--text-muted)",
  },
  synthesisForm: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  inputWrap: {
    width: "100%",
  },
  textarea: {
    width: "100%",
    padding: "12px 16px",
    fontSize: "14px",
    lineHeight: "1.5",
    borderRadius: "var(--radius-md)",
    resize: "vertical",
    minHeight: "72px",
  },
  formFooter: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "12px",
  },
  presetGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  presetLabel: {
    fontSize: "11.5px",
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
  },
  presetButtons: {
    display: "flex",
    gap: "6px",
  },
  presetBtn: {
    fontSize: "11.5px",
    padding: "3px 8px",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-secondary)",
    border: "1px solid var(--border-subtle)",
  },
  synthesizeBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "10px 20px",
    backgroundColor: "var(--primary)",
    color: "#ffffff",
    fontWeight: "600",
    fontSize: "13.5px",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-sm)",
  },
  resultCanvas: {
    flex: 1,
    overflowY: "auto",
    padding: "24px 32px",
  },
  loadingContainer: {
    padding: "60px 20px",
    textAlign: "center",
    maxWidth: "520px",
    margin: "0 auto",
  },
  spinner: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    border: "3px solid var(--primary-light)",
    borderTopColor: "var(--primary)",
    margin: "0 auto 18px auto",
  },
  loadingTitle: {
    fontSize: "17px",
    fontWeight: "600",
    marginBottom: "8px",
  },
  loadingSub: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    lineHeight: "1.5",
  },
  resultCard: {
    maxWidth: "920px",
    margin: "0 auto",
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-subtle)",
    borderRadius: "var(--radius-lg)",
    padding: "28px 32px",
    boxShadow: "var(--shadow-md)",
  },
  resultToolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid var(--border-subtle)",
    paddingBottom: "16px",
    marginBottom: "20px",
  },
  resultStatus: {
    display: "flex",
    alignItems: "center",
  },
  statusBadge: {
    fontSize: "12px",
    fontFamily: "var(--font-mono)",
    fontWeight: "600",
    padding: "4px 10px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--emerald-bg)",
    color: "var(--emerald)",
    border: "1px solid var(--emerald-border)",
  },
  toolbarActions: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  toolBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 12px",
    fontSize: "12px",
    color: "var(--text-secondary)",
    backgroundColor: "var(--bg-elevated)",
    borderRadius: "var(--radius-sm)",
  },
  resultBody: {
    fontSize: "15px",
    lineHeight: "1.75",
    color: "var(--text-primary)",
  },
  sectionHeading: {
    fontSize: "15px",
    fontWeight: "700",
    color: "var(--primary)",
    marginTop: "16px",
    marginBottom: "6px",
  },
  majorHeading: {
    fontSize: "17px",
    fontWeight: "800",
    color: "var(--text-primary)",
    marginTop: "20px",
    marginBottom: "8px",
    borderBottom: "1px solid var(--border-subtle)",
    paddingBottom: "4px",
  },
  synthesisParagraph: {
    fontSize: "13.5px",
    lineHeight: "1.65",
    color: "var(--text-primary)",
    marginBottom: "8px",
  },
  inlineCitationPill: {
    display: "inline-flex",
    alignItems: "center",
    padding: "1px 6px",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    fontSize: "11px",
    fontWeight: "700",
    margin: "0 2px",
    verticalAlign: "baseline",
    cursor: "help",
  },
  citationsSection: {
    marginTop: "28px",
    borderTop: "1px solid var(--border-subtle)",
    paddingTop: "20px",
  },
  citationsHeader: {
    fontSize: "13px",
    fontFamily: "var(--font-mono)",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: "14px",
  },
  citationsList: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  citationRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
    padding: "10px 14px",
    backgroundColor: "var(--bg-elevated)",
    borderRadius: "var(--radius-md)",
  },
  citeIndex: {
    fontFamily: "var(--font-mono)",
    fontSize: "12px",
    fontWeight: "700",
    color: "var(--primary)",
  },
  citeDetails: {
    flex: 1,
  },
  citeSourceRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "4px",
    fontSize: "13px",
  },
  pageTag: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    padding: "1px 5px",
    borderRadius: "3px",
    backgroundColor: "var(--bg-card)",
    color: "var(--text-muted)",
  },
  citeSnippet: {
    fontSize: "12.5px",
    color: "var(--text-secondary)",
    fontStyle: "italic",
    lineHeight: "1.4",
  },
  placeholderState: {
    padding: "80px 20px",
    textAlign: "center",
    maxWidth: "540px",
    margin: "0 auto",
  },
  placeholderTitle: {
    fontSize: "18px",
    fontWeight: "600",
    marginBottom: "8px",
  },
  placeholderSub: {
    fontSize: "13.5px",
    color: "var(--text-secondary)",
    lineHeight: "1.6",
  },
};

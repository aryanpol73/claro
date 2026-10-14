import React, { useState, useRef, useEffect } from "react";
import {
  IconSparkles,
  IconShieldCheck,
  IconShieldAlert,
  IconCopy,
  IconCheck,
  IconDownload,
  IconEye,
} from "./Icons";

export function ChatWorkspace({
  messages = [],
  onAskQuestion,
  isAsking = false,
  selectedDocumentId,
  selectedDocumentName,
  onClearScope,
  onOpenReader,
}) {
  const [inputQuestion, setInputQuestion] = useState("");
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [activeCitationIndex, setActiveCitationIndex] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const suggestedPrompts = [
    "What is the core problem and research contribution of this work?",
    "Summarize the methodology, architecture, and datasets used.",
    "What are the key empirical results and performance metrics?",
    "What limitations or open questions are acknowledged?",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAsking]);

  function handleSubmit(e) {
    if (e) e.preventDefault();
    if (!inputQuestion.trim() || isAsking) return;

    onAskQuestion(inputQuestion.trim());
    setInputQuestion("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleInputResize(e) {
    setInputQuestion(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  }

  function copyAnswer(text, index) {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  }

  function downloadNote(msg) {
    const content = `# Claro Academic Research Note\n\n**Question:** ${msg.question}\n\n**Answer:**\n${msg.answer}\n\n**Grounded:** ${msg.grounded ? "Verified Evidence" : "Cite-or-Refuse Refusal"}\n\n## Citations\n${(msg.citations || []).map((c, i) => `[${i + 1}] ${c.source} (Page ${c.page || 'N/A'}):\n> ${c.snippet}\n`).join("\n")}`;
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `claro_research_note_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Render text with clickable citation pills for [1], [2]
  function renderFormattedAnswer(text, citations = []) {
    if (!text) return null;
    const parts = text.split(/(\[\d+\])/g);

    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const index = parseInt(match[1], 10);
        const citation = citations[index - 1];
        return (
          <button
            key={i}
            onClick={() => setActiveCitationIndex(index)}
            style={{
              ...styles.citationPill,
              backgroundColor: activeCitationIndex === index ? "var(--primary)" : "var(--primary-light)",
              color: activeCitationIndex === index ? "#ffffff" : "var(--primary)",
            }}
            title={citation ? `${citation.source} (Page ${citation.page || 'N/A'})` : `Source [${index}]`}
          >
            {part}
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  }

  return (
    <div style={styles.workspace}>
      {/* Top Scope Banner */}
      <div style={styles.topBanner}>
        <div style={styles.scopeIndicator}>
          <span style={styles.scopeLabel}>RESEARCH CONTEXT:</span>
          {selectedDocumentId ? (
            <div style={styles.scopeTag}>
              <span>{selectedDocumentName || "Selected Document"}</span>
              <button onClick={onClearScope} style={styles.clearScopeBtn}>
                ✕ Reset to all papers
              </button>
            </div>
          ) : (
            <div style={styles.scopeTagAll}>
              <span>Entire Paper Collection (Cross-Document Search)</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages Stream */}
      <div style={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div style={styles.welcomeContainer}>
            <div style={styles.welcomeHero}>
              <div style={styles.welcomeIconWrap}>
                <IconSparkles size={32} />
              </div>
              <h2 style={styles.welcomeTitle}>Grounded Academic Intelligence</h2>
              <p style={styles.welcomeSubtitle}>
                Ask deep questions about your papers. Claro synthesizes evidence with strict
                <strong style={{ color: "var(--text-primary)" }}> cite-or-refuse</strong> grounding, 
                pointing you directly to the exact page and source passage.
              </p>
            </div>

            {/* Suggested prompts */}
            <div style={styles.suggestedSection}>
              <div style={styles.suggestedHeader}>Suggested Academic Inquiries</div>
              <div style={styles.promptGrid}>
                {suggestedPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setInputQuestion(prompt);
                      textareaRef.current?.focus();
                    }}
                    style={styles.promptChip}
                  >
                    <span>{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} style={styles.messageTurn} className="animate-fade-in">
              {/* User Question Card */}
              <div style={styles.userCard}>
                <div style={styles.questionText}>{msg.question}</div>
                {msg.scopedDocumentName && (
                  <div style={styles.scopedQuestionBadge}>
                    Scoped to: {msg.scopedDocumentName}
                  </div>
                )}
              </div>

              {/* Claro Answer Card */}
              <div style={styles.assistantCard}>
                {/* Status Bar */}
                <div style={styles.answerStatusBar}>
                  <div style={styles.statusBadgeWrap}>
                    {msg.grounded ? (
                      <span style={styles.groundedBadge}>
                        <IconShieldCheck size={14} />
                        <span>Verified Grounded</span>
                      </span>
                    ) : (
                      <span style={styles.refusedBadge}>
                        <IconShieldAlert size={14} />
                        <span>Cite-or-Refuse: Insufficient Evidence</span>
                      </span>
                    )}
                  </div>

                  <div style={styles.answerActions}>
                    <button
                      onClick={() => copyAnswer(msg.answer, index)}
                      style={styles.actionBtn}
                      title="Copy Answer"
                    >
                      {copiedIndex === index ? <IconCheck size={14} /> : <IconCopy size={14} />}
                      <span>{copiedIndex === index ? "Copied" : "Copy"}</span>
                    </button>
                    <button
                      onClick={() => downloadNote(msg)}
                      style={styles.actionBtn}
                      title="Export as Markdown Note"
                    >
                      <IconDownload size={14} />
                      <span>Export Note</span>
                    </button>
                  </div>
                </div>

                {/* Main Answer Text */}
                <div style={styles.answerBody}>
                  {renderFormattedAnswer(msg.answer, msg.citations)}
                </div>

                {/* Citations & Evidence Drawer */}
                {msg.citations && msg.citations.length > 0 && (
                  <div style={styles.citationsSection}>
                    <div style={styles.citationsTitle}>
                      <span>Retrieved Evidence & Passages ({msg.citations.length})</span>
                    </div>

                    <div style={styles.citationsGrid}>
                      {msg.citations.map((c, cIdx) => {
                        const markerIndex = cIdx + 1;
                        const isHighlighted = activeCitationIndex === markerIndex;
                        return (
                          <div
                            key={c.chunk_id || cIdx}
                            style={{
                              ...styles.citationCard,
                              borderColor: isHighlighted ? "var(--primary)" : "var(--border-subtle)",
                              backgroundColor: isHighlighted ? "rgba(99, 102, 241, 0.08)" : "var(--bg-elevated)",
                            }}
                          >
                            <div style={styles.citationHeader}>
                              <div style={styles.citationBadgeGroup}>
                                <span style={styles.citationMarker}>[{markerIndex}]</span>
                                <span style={styles.citationSource} title={c.source}>
                                  {c.source}
                                </span>
                              </div>
                              <div style={styles.citationMetaGroup}>
                                {c.page != null && (
                                  <span style={styles.citationPage}>Page {c.page}</span>
                                )}
                                {c.score != null && (
                                  <span style={styles.citationScore}>
                                    {Math.round(c.score * 100)}% match
                                  </span>
                                )}
                              </div>
                            </div>

                            <blockquote style={styles.citationQuote}>
                              "{c.snippet}"
                            </blockquote>

                            {c.document_id && (
                              <button
                                onClick={() => onOpenReader(c.document_id, c.page)}
                                style={styles.jumpToReaderBtn}
                                title="Open document viewer at this page"
                              >
                                <IconEye size={12} />
                                <span>Inspect in Document Reader</span>
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isAsking && (
          <div style={styles.loadingTurn} className="animate-fade-in">
            <div style={styles.loadingCard}>
              <div style={styles.loadingSpinnerWrap}>
                <div className="animate-spin" style={styles.spinner} />
              </div>
              <div>
                <div style={styles.loadingTitle}>Retrieving Evidence & Synthesizing...</div>
                <div style={styles.loadingSub}>
                  Scanning Pinecone embeddings, applying lexical re-ranking, and verifying grounding against source citations.
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Composer */}
      <div style={styles.composerSection} className="glass-panel">
        <form onSubmit={handleSubmit} style={styles.composerForm}>
          <textarea
            ref={textareaRef}
            value={inputQuestion}
            onChange={handleInputResize}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedDocumentId
                ? `Ask about "${selectedDocumentName}"...`
                : "Ask an academic question across all indexed papers..."
            }
            rows={1}
            style={styles.composerInput}
            disabled={isAsking}
          />
          <button
            type="submit"
            disabled={!inputQuestion.trim() || isAsking}
            style={{
              ...styles.submitBtn,
              opacity: !inputQuestion.trim() || isAsking ? 0.5 : 1,
            }}
          >
            <IconSparkles size={16} />
            <span>Ask Claro</span>
          </button>
        </form>
        <div style={styles.composerFooter}>
          <span>Press <kbd style={styles.kbd}>Enter</kbd> to ask, <kbd style={styles.kbd}>Shift + Enter</kbd> for newline</span>
          {selectedDocumentId && (
            <span style={{ color: "var(--primary)" }}>Scoped search active</span>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  workspace: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    height: "100%",
    overflow: "hidden",
    position: "relative",
    backgroundColor: "var(--bg-app)",
  },
  topBanner: {
    padding: "8px 24px",
    borderBottom: "1px solid var(--border-subtle)",
    backgroundColor: "var(--bg-sidebar)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  scopeIndicator: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  scopeLabel: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    fontWeight: "600",
    color: "var(--text-muted)",
  },
  scopeTag: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "3px 10px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    fontSize: "12px",
    fontWeight: "600",
  },
  clearScopeBtn: {
    fontSize: "11px",
    color: "var(--text-secondary)",
    cursor: "pointer",
  },
  scopeTagAll: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    fontWeight: "500",
  },
  messagesContainer: {
    flex: 1,
    overflowY: "auto",
    padding: "24px 32px",
    display: "flex",
    flexDirection: "column",
    gap: "28px",
  },
  welcomeContainer: {
    maxWidth: "760px",
    margin: "40px auto 0 auto",
    textAlign: "center",
  },
  welcomeHero: {
    marginBottom: "36px",
  },
  welcomeIconWrap: {
    width: "60px",
    height: "60px",
    borderRadius: "var(--radius-xl)",
    backgroundColor: "var(--primary-light)",
    color: "var(--primary)",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "16px",
    boxShadow: "var(--shadow-glow)",
  },
  welcomeTitle: {
    fontSize: "28px",
    fontWeight: "700",
    marginBottom: "10px",
  },
  welcomeSubtitle: {
    fontSize: "15px",
    color: "var(--text-secondary)",
    lineHeight: "1.6",
    maxWidth: "580px",
    margin: "0 auto",
  },
  suggestedSection: {
    textAlign: "left",
  },
  suggestedHeader: {
    fontSize: "12px",
    fontFamily: "var(--font-mono)",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    marginBottom: "12px",
  },
  promptGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "10px",
  },
  promptChip: {
    padding: "14px",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-subtle)",
    color: "var(--text-primary)",
    textAlign: "left",
    fontSize: "13px",
    lineHeight: "1.4",
    transition: "all var(--trans-fast)",
    cursor: "pointer",
  },
  messageTurn: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    maxWidth: "880px",
    width: "100%",
    margin: "0 auto",
  },
  userCard: {
    alignSelf: "flex-end",
    backgroundColor: "var(--primary-hover)",
    color: "#ffffff",
    padding: "12px 18px",
    borderRadius: "16px 16px 2px 16px",
    maxWidth: "80%",
    boxShadow: "var(--shadow-sm)",
  },
  questionText: {
    fontSize: "14.5px",
    lineHeight: "1.5",
    fontWeight: "500",
  },
  scopedQuestionBadge: {
    fontSize: "11px",
    opacity: 0.85,
    marginTop: "4px",
  },
  assistantCard: {
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-subtle)",
    borderRadius: "var(--radius-lg)",
    padding: "20px 24px",
    boxShadow: "var(--shadow-md)",
  },
  answerStatusBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid var(--border-subtle)",
    paddingBottom: "12px",
    marginBottom: "16px",
  },
  statusBadgeWrap: {
    display: "flex",
    alignItems: "center",
  },
  groundedBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 10px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--emerald-bg)",
    border: "1px solid var(--emerald-border)",
    color: "var(--emerald)",
    fontSize: "12px",
    fontWeight: "600",
  },
  refusedBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 10px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--amber-bg)",
    border: "1px solid var(--amber-border)",
    color: "var(--amber)",
    fontSize: "12px",
    fontWeight: "600",
  },
  answerActions: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  actionBtn: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "5px 10px",
    fontSize: "12px",
    color: "var(--text-secondary)",
    backgroundColor: "var(--bg-elevated)",
    borderRadius: "var(--radius-sm)",
  },
  answerBody: {
    fontSize: "15px",
    lineHeight: "1.7",
    color: "var(--text-primary)",
    whiteSpace: "pre-line",
  },
  citationPill: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "var(--font-mono)",
    fontSize: "12px",
    fontWeight: "700",
    padding: "1px 5px",
    margin: "0 2px",
    borderRadius: "4px",
    verticalAlign: "baseline",
    cursor: "pointer",
  },
  citationsSection: {
    marginTop: "24px",
    borderTop: "1px solid var(--border-subtle)",
    paddingTop: "18px",
  },
  citationsTitle: {
    fontSize: "12.5px",
    fontFamily: "var(--font-mono)",
    fontWeight: "600",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: "14px",
  },
  citationsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "12px",
  },
  citationCard: {
    padding: "14px 16px",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--border-subtle)",
    transition: "all var(--trans-fast)",
  },
  citationHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "8px",
  },
  citationBadgeGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  citationMarker: {
    fontFamily: "var(--font-mono)",
    fontSize: "12px",
    fontWeight: "700",
    color: "var(--primary)",
  },
  citationSource: {
    fontSize: "13px",
    fontWeight: "600",
    color: "var(--text-primary)",
  },
  citationMetaGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  citationPage: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    padding: "2px 6px",
    borderRadius: "4px",
    backgroundColor: "var(--bg-card)",
    color: "var(--text-secondary)",
  },
  citationScore: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    color: "var(--emerald)",
  },
  citationQuote: {
    fontSize: "13px",
    lineHeight: "1.5",
    color: "var(--text-secondary)",
    fontStyle: "italic",
    borderLeft: "2px solid var(--border-medium)",
    paddingLeft: "10px",
    margin: "6px 0 10px 0",
  },
  jumpToReaderBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "11.5px",
    color: "var(--primary)",
    fontWeight: "600",
  },
  loadingTurn: {
    maxWidth: "880px",
    width: "100%",
    margin: "0 auto",
  },
  loadingCard: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "18px 24px",
    borderRadius: "var(--radius-lg)",
    backgroundColor: "var(--bg-card)",
    border: "1px solid var(--border-accent)",
  },
  loadingSpinnerWrap: {
    width: "28px",
    height: "28px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  spinner: {
    width: "22px",
    height: "22px",
    borderRadius: "50%",
    border: "2px solid var(--primary-light)",
    borderTopColor: "var(--primary)",
  },
  loadingTitle: {
    fontSize: "14px",
    fontWeight: "600",
    color: "var(--text-primary)",
  },
  loadingSub: {
    fontSize: "12px",
    color: "var(--text-muted)",
    marginTop: "2px",
  },
  composerSection: {
    padding: "16px 32px 20px 32px",
    borderTop: "1px solid var(--border-subtle)",
  },
  composerForm: {
    maxWidth: "880px",
    margin: "0 auto",
    display: "flex",
    alignItems: "flex-end",
    gap: "12px",
    backgroundColor: "var(--bg-card)",
    padding: "8px 12px 8px 16px",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--border-medium)",
    boxShadow: "var(--shadow-sm)",
  },
  composerInput: {
    flex: 1,
    background: "transparent",
    border: "none",
    padding: "6px 0",
    fontSize: "14.5px",
    color: "var(--text-primary)",
    resize: "none",
    lineHeight: "1.5",
    maxHeight: "180px",
    outline: "none",
  },
  submitBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "10px 18px",
    backgroundColor: "var(--primary)",
    color: "#ffffff",
    fontWeight: "600",
    fontSize: "13.5px",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-sm)",
    transition: "all var(--trans-fast)",
  },
  composerFooter: {
    maxWidth: "880px",
    margin: "8px auto 0 auto",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "11px",
    color: "var(--text-muted)",
  },
  kbd: {
    fontFamily: "var(--font-mono)",
    padding: "1px 4px",
    borderRadius: "3px",
    backgroundColor: "var(--bg-elevated)",
    border: "1px solid var(--border-subtle)",
  },
};

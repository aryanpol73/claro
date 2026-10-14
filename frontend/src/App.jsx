import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { ChatWorkspace } from "./components/ChatWorkspace";
import { SynthesisWorkspace } from "./components/SynthesisWorkspace";
import { DocumentReader } from "./components/DocumentReader";
import { LibraryView } from "./components/LibraryView";
import { SetupModal } from "./components/SetupModal";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("claro_theme") || "dark");
  const [activeMode, setActiveMode] = useState("qa");
  const [systemStatus, setSystemStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [multiSelectedIds, setMultiSelectedIds] = useState([]);

  // Q&A Chat State
  const [messages, setMessages] = useState([]);
  const [isAsking, setIsAsking] = useState(false);

  // Ingestion State
  const [isUploading, setIsUploading] = useState(false);

  // Synthesis State
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesisResult, setSynthesisResult] = useState(null);

  // Reader State
  const [readerDocId, setReaderDocId] = useState("");
  const [readerPage, setReaderPage] = useState(1);

  // Setup Modal & Toast
  const [isSetupOpen, setIsSetupOpen] = useState(false);
  const [toast, setToast] = useState(null);

  // Initialize Theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("claro_theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }

  function showToast(message, type = "info") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }

  // Load Status & Documents
  async function fetchStatus() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
      }
    } catch (e) {
      console.warn("Backend not reachable at", API_BASE, e);
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      if (res.ok) {
        const data = await res.json();
        const docs = data.documents || data.files || [];
        setDocuments(docs);
        if (docs.length > 0 && !readerDocId) {
          setReaderDocId(docs[0].document_id);
        }
      }
    } catch (e) {
      console.error("Failed to load documents:", e);
    }
  }

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const statusRes = await fetch(`${API_BASE}/health`);
        if (statusRes.ok && isMounted) {
          const statusData = await statusRes.json();
          setSystemStatus(statusData);
        }
      } catch (err) {
        console.warn("Backend initialization warning:", err);
      }

      try {
        const docsRes = await fetch(`${API_BASE}/documents`);
        if (docsRes.ok && isMounted) {
          const docsData = await docsRes.json();
          const docs = docsData.documents || docsData.files || [];
          setDocuments(docs);
          if (docs.length > 0) {
            setReaderDocId((prev) => prev || docs[0].document_id);
          }
        }
      } catch (err) {
        console.error("Initial documents load error:", err);
      }
    }
    init();
    return () => { isMounted = false; };
  }, []);

  const selectedDocObj = documents.find((d) => d.document_id === selectedDocumentId);
  const selectedDocumentName = selectedDocObj ? (selectedDocObj.original_filename || selectedDocObj.name) : "";

  // File Upload Handler
  async function handleUploadFile(file) {
    if (!file) return;

    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (ext !== ".pdf" && ext !== ".docx") {
      showToast("Only PDF and DOCX documents are supported.", "error");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      showToast("File size exceeds 50 MB limit.", "error");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        if (data.skipped) {
          showToast(`Document already indexed (${data.filename})`, "info");
        } else if (data.needs_indexing) {
          showToast(`"${data.filename}" saved (${data.document?.total_pages || 0} pages). Configure API keys in Setup to index.`, "info");
        } else {
          showToast(`"${data.filename}" indexed successfully (${data.total_pages || 0} pages)!`, "success");
        }
        await fetchDocuments();
        await fetchStatus();
      } else {
        showToast(data.detail || "Upload failed. Please check backend logs.", "error");
      }
    } catch (e) {
      console.error("Upload error:", e);
      showToast("Network error uploading document.", "error");
    } finally {
      setIsUploading(false);
    }
  }

  // Delete Document Handler
  async function handleDeleteDocument(documentId, filename) {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All vectors and physical files will be purged.`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/documents/${documentId}`, {
        method: "DELETE",
      });

      if (res.ok) {
        showToast(`Document "${filename}" deleted.`, "info");
        if (selectedDocumentId === documentId) setSelectedDocumentId("");
        setMultiSelectedIds((prev) => prev.filter((id) => id !== documentId));
        await fetchDocuments();
        await fetchStatus();
      } else {
        const err = await res.json();
        showToast(err.detail || "Failed to delete document.", "error");
      }
    } catch (e) {
      console.error("Delete error:", e);
      showToast("Failed to delete document.", "error");
    }
  }

  // Ask Question Handler
  async function handleAskQuestion(question) {
    if (!question.trim()) return;

    setIsAsking(true);
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          ...(selectedDocumentId ? { document_id: selectedDocumentId } : {}),
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            question,
            answer: data.answer,
            citations: data.citations || [],
            grounded: data.grounded,
            scopedDocumentName: selectedDocumentName || null,
            timestamp: new Date().toISOString(),
          },
        ]);
      } else {
        showToast(data.detail || "Failed to retrieve answer.", "error");
      }
    } catch (e) {
      console.error("Q&A error:", e);
      showToast("Network error communicating with Claro backend.", "error");
    } finally {
      setIsAsking(false);
    }
  }

  // Synthesis Handler
  async function handleRunSynthesis(topic, docIds) {
    setIsSynthesizing(true);
    try {
      const res = await fetch(`${API_BASE}/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          document_ids: docIds && docIds.length > 0 ? docIds : null,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setSynthesisResult(data);
      } else {
        showToast(data.detail || "Synthesis generation failed.", "error");
      }
    } catch (e) {
      console.error("Synthesis error:", e);
      showToast("Network error generating synthesis.", "error");
    } finally {
      setIsSynthesizing(false);
    }
  }

  // Document Reader Navigation
  function handleOpenReader(docId, page = 1) {
    setReaderDocId(docId);
    setReaderPage(page || 1);
    setActiveMode("reader");
  }

  function handleScopeToDoc(docId, name) {
    setSelectedDocumentId(docId);
    setActiveMode("qa");
    showToast(`Search scoped to: "${name}"`, "info");
  }

  function toggleMultiSelect(docId) {
    setMultiSelectedIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  }

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && (
        <div
          style={{
            ...styles.toast,
            backgroundColor:
              toast.type === "error"
                ? "var(--rose)"
                : toast.type === "success"
                ? "var(--emerald)"
                : "var(--primary)",
          }}
          className="animate-fade-in"
        >
          {toast.message}
        </div>
      )}

      {/* Header */}
      <Header
        activeMode={activeMode}
        setActiveMode={setActiveMode}
        systemStatus={systemStatus}
        onOpenSetup={() => setIsSetupOpen(true)}
        documentCount={documents.length}
        theme={theme}
        toggleTheme={toggleTheme}
      />

      {/* Main Workspace Layout */}
      <div className="workspace-layout">
        {/* Document Library Sidebar */}
        <Sidebar
          documents={documents}
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={setSelectedDocumentId}
          multiSelectedIds={multiSelectedIds}
          onToggleMultiSelect={toggleMultiSelect}
          onUploadFile={handleUploadFile}
          onDeleteDocument={handleDeleteDocument}
          onOpenReader={handleOpenReader}
          onRefresh={() => {
            fetchDocuments();
            fetchStatus();
            showToast("Library updated", "info");
          }}
          isUploading={isUploading}
          collapsed={activeMode === "library"}
        />

        {/* Dynamic Mode Center Canvas */}
        <main style={styles.mainCanvas}>
          {activeMode === "qa" && (
            <ChatWorkspace
              messages={messages}
              onAskQuestion={handleAskQuestion}
              isAsking={isAsking}
              selectedDocumentId={selectedDocumentId}
              selectedDocumentName={selectedDocumentName}
              onClearScope={() => setSelectedDocumentId("")}
              onOpenReader={handleOpenReader}
            />
          )}

          {activeMode === "synthesis" && (
            <SynthesisWorkspace
              documents={documents}
              multiSelectedIds={multiSelectedIds}
              onToggleMultiSelect={toggleMultiSelect}
              onRunSynthesis={handleRunSynthesis}
              isSynthesizing={isSynthesizing}
              synthesisResult={synthesisResult}
            />
          )}

          {activeMode === "reader" && (
            <DocumentReader
              documents={documents}
              activeDocId={readerDocId}
              onSelectDoc={setReaderDocId}
              targetPage={readerPage}
              onScopeToDoc={handleScopeToDoc}
            />
          )}

          {activeMode === "library" && (
            <LibraryView
              documents={documents}
              onSelectDoc={handleOpenReader}
              onScopeToDoc={handleScopeToDoc}
              onDeleteDoc={handleDeleteDocument}
            />
          )}
        </main>
      </div>

      {/* Credentials Setup Modal */}
      <SetupModal
        isOpen={isSetupOpen}
        onClose={() => setIsSetupOpen(false)}
        systemStatus={systemStatus}
        onRefresh={() => {
          fetchStatus();
          showToast("Credentials re-verified", "info");
        }}
      />
    </div>
  );
}

const styles = {
  mainCanvas: {
    display: "flex",
    flex: 1,
    height: "100%",
    overflow: "hidden",
    position: "relative",
  },
  toast: {
    position: "fixed",
    top: "76px",
    right: "24px",
    zIndex: 999,
    padding: "10px 18px",
    borderRadius: "var(--radius-md)",
    color: "#ffffff",
    fontSize: "13px",
    fontWeight: "600",
    boxShadow: "var(--shadow-lg)",
  },
};

export default App;
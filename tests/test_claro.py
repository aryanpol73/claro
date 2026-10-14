import io
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from backend.chunking import attach_document_id, split_documents
from backend.document_metadata import add_metadata, generate_document_id
from backend.document_store import delete_document, get_document, list_documents, save_document
from backend.main import app
from backend.pdf_ingestion import load_pdf


def test_generate_document_id():
    """Verify deterministic SHA-256 generation from bytes and streams."""
    content = b"Claro Academic Research Platform Test Document"
    id1 = generate_document_id(content)
    id2 = generate_document_id(io.BytesIO(content))

    assert len(id1) == 64
    assert id1 == id2
    assert id1.isalnum()


def test_add_metadata_preserves_page_numbers():
    """Ensure page numbers are correctly 1-indexed integers and not overwritten with empty strings."""
    docs = [
        Document(page_content="Abstract and Introduction", metadata={"page": 1, "source": "paper.pdf"}),
        Document(page_content="Methodology Section", metadata={"page": 2, "source": "paper.pdf"}),
    ]
    doc_id = "a" * 64
    processed = add_metadata(docs, document_id=doc_id, source_name="Quantum Paper.pdf")

    assert len(processed) == 2
    assert processed[0].metadata["page"] == 1
    assert processed[0].metadata["document_id"] == doc_id
    assert processed[0].metadata["source"] == "Quantum Paper.pdf"
    assert processed[1].metadata["page"] == 2


def test_chunking_and_metadata_attachment():
    """Test text splitting, chunk minimum threshold, and metadata attachment."""
    docs = [
        Document(
            page_content="This is a substantial paragraph discussing retrieval augmented generation techniques in modern research workspaces. " * 5,
            metadata={"page": 1, "source": "rag_study.pdf"}
        )
    ]
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=40)
    assert len(chunks) >= 1

    doc_id = "b" * 64
    attached = attach_document_id(chunks, doc_id)
    assert all(c.metadata["document_id"] == doc_id for c in attached)
    assert attached[0].metadata["chunk_index"] == 0


def test_document_store_lifecycle():
    """Verify document metadata registration, retrieval, and deletion."""
    test_id = "c" * 64
    save_document(
        document_id=test_id,
        original_filename="attention_mechanism.pdf",
        stored_filename=f"{test_id}.pdf",
        size_bytes=1048576,
        file_extension=".pdf",
        total_pages=15,
        total_chunks=42,
        status="ready",
    )

    doc = get_document(test_id)
    assert doc is not None
    assert doc["original_filename"] == "attention_mechanism.pdf"
    assert doc["total_pages"] == 15
    assert doc["size_mb"] == 1.0

    all_docs = list_documents()
    assert any(d["document_id"] == test_id for d in all_docs)

    # Clean up
    deleted = delete_document(test_id)
    assert deleted is True
    assert get_document(test_id) is None


def test_pdf_loading_on_sample_notes():
    """Verify real PDF loading on data/notes.pdf without OCR crashes."""
    pdf_path = Path("data/notes.pdf")
    if pdf_path.exists():
        docs = load_pdf(str(pdf_path))
        assert len(docs) > 0
        assert docs[0].metadata["page"] == 1
        assert "notes.pdf" in docs[0].metadata["source"]


def test_api_root_and_health():
    """Test root and health endpoints via FastAPI TestClient."""
    client = TestClient(app)

    res_root = client.get("/")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["app"] == "Claro"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "ready"
    assert ".pdf" in data_health["allowed_extensions"]


def test_api_upload_validation_rejects_empty_file():
    """Ensure upload endpoint rejects empty files with 400 Bad Request."""
    client = TestClient(app)
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400


def test_api_upload_validation_rejects_invalid_extension():
    """Ensure upload endpoint rejects unallowed file types like .exe."""
    client = TestClient(app)
    files = {"file": ("malicious.exe", b"binary content", "application/octet-stream")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_api_ask_handles_unconfigured_api_key_gracefully():
    """Verify that asking a question without API keys returns a helpful ungrounded response rather than a 500 crash."""
    client = TestClient(app)
    with patch("backend.rag.is_llm_configured", return_value=False), patch("backend.rag.is_gemini_configured", return_value=False):
        response = client.post("/ask", json={"question": "What is attention?"})
        assert response.status_code == 200
        data = response.json()
        assert data["grounded"] is False
        assert len(data["citations"]) == 0
        assert "configuration required" in data["answer"].lower() or "not contain sufficient evidence" in data["answer"].lower()


def test_api_list_and_get_documents():
    """Verify listing documents and retrieving specific document details."""
    client = TestClient(app)
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert any(d["original_filename"] == "notes.pdf" for d in data["documents"])

    # Test file streaming endpoint
    doc_id = "ddb5bb33dea17c3d30778fddd5c96320b2f08faeedc38b35ac5897f45e407c23"
    res_file = client.get(f"/documents/{doc_id}/file")
    assert res_file.status_code == 200
    assert res_file.headers["content-type"] == "application/pdf"


def test_api_synthesize_handles_unconfigured_keys_gracefully():
    """Verify that synthesizing documents without API keys returns an ungrounded response."""
    client = TestClient(app)
    with patch("backend.rag.is_llm_configured", return_value=False), patch("backend.rag.is_gemini_configured", return_value=False):
        response = client.post("/synthesize", json={"topic": "Embedded Systems and RTOS architecture"})
        assert response.status_code == 200
        data = response.json()
        assert data["grounded"] is False
        assert "api_key is required" in data["answer"].lower() or "not contain sufficient evidence" in data["answer"].lower() or "no evidence found" in data["answer"].lower()


def test_api_config_keys_endpoint():
    """Verify that /config/keys safely processes configuration updates."""
    client = TestClient(app)
    res = client.post("/config/keys", json={"pinecone_index_name": "academic-files-rag"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_api_upload_unconfigured_keys_resilient():
    """Verify that uploading a valid PDF when keys are unconfigured stores document and pages cleanly."""
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Claro Academic Testing Document for Resilient Uploads.")
    pdf_bytes = doc.tobytes()
    doc.close()

    client = TestClient(app)
    files = {"file": ("resilient_test.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "resilient_test.pdf"
    assert data["document"]["total_pages"] == 1
    assert data["document"]["status"] in ("pending_index", "ready")

    # Clean up test document from store and disk
    from backend.document_store import delete_document
    delete_document(data["document_id"])
    test_file = Path("backend/uploads") / f"{data['document_id']}.pdf"
    if test_file.exists():
        test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    tests = [
        ("test_generate_document_id", test_generate_document_id),
        ("test_add_metadata_preserves_page_numbers", test_add_metadata_preserves_page_numbers),
        ("test_chunking_and_metadata_attachment", test_chunking_and_metadata_attachment),
        ("test_document_store_lifecycle", test_document_store_lifecycle),
        ("test_api_root_and_health", test_api_root_and_health),
        ("test_api_upload_validation_rejects_empty_file", test_api_upload_validation_rejects_empty_file),
        ("test_api_upload_validation_rejects_invalid_extension", test_api_upload_validation_rejects_invalid_extension),
        ("test_api_ask_handles_unconfigured_api_key_gracefully", test_api_ask_handles_unconfigured_api_key_gracefully),
        ("test_pdf_loading_on_sample_notes", test_pdf_loading_on_sample_notes),
        ("test_api_list_and_get_documents", test_api_list_and_get_documents),
        ("test_api_synthesize_handles_unconfigured_keys_gracefully", test_api_synthesize_handles_unconfigured_keys_gracefully),
        ("test_api_config_keys_endpoint", test_api_config_keys_endpoint),
        ("test_api_upload_unconfigured_keys_resilient", test_api_upload_unconfigured_keys_resilient),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f" PASS: {name}")
            passed += 1
        except Exception as e:
            print(f" FAIL: {name} - {e}")
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed.")
    if failed > 0:
        exit(1)


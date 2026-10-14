import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from backend.main import app
from backend.rag import GroundedAnswer, REFUSE_MESSAGE


def test_end_to_end_ai_rag_workflow():
    """
    Test the complete end-to-end RAG question answering flow:
    query -> embedding -> Pinecone hybrid retrieval -> Gemini structured cite-or-refuse -> response.
    """
    client = TestClient(app)

    fake_matches = [
        {
            "id": "ddb5bb33dea17c3d30778fddd5c96320b2f08faeedc38b35ac5897f45e407c23-chunk-0",
            "score": 0.88,
            "metadata": {
                "text": "An embedded system is a microprocessor-based computer hardware system with software designed to perform a dedicated function.",
                "document_id": "ddb5bb33dea17c3d30778fddd5c96320b2f08faeedc38b35ac5897f45e407c23",
                "source": "notes.pdf",
                "page": 2,
                "chunk_index": 0,
            },
        }
    ]

    mock_llm_output = GroundedAnswer(
        answer="An embedded system is a specialized computing system designed to perform a dedicated task [1].",
        grounded=True,
    )

    with patch("backend.rag.is_gemini_configured", return_value=True), \
         patch("backend.hybrid_search.get_pinecone_index") as mock_pinecone, \
         patch("backend.hybrid_search.get_embeddings") as mock_embeddings, \
         patch("backend.rag._get_llm") as mock_llm_factory:

        # Mock embeddings
        mock_embed_instance = MagicMock()
        mock_embed_instance.embed_query.return_value = [0.1] * 768
        mock_embeddings.return_value = mock_embed_instance

        # Mock Pinecone query
        mock_index_instance = MagicMock()
        mock_index_instance.query.return_value = {"matches": fake_matches}
        mock_pinecone.return_value = mock_index_instance

        # Mock LLM with structured output
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = mock_llm_output
        mock_llm.with_structured_output.return_value = mock_structured
        mock_llm_factory.return_value = mock_llm

        response = client.post(
            "/ask",
            json={"question": "What is an embedded system?", "top_k": 4},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["grounded"] is True
        assert "[1]" in data["answer"]
        assert len(data["citations"]) == 1
        assert data["citations"][0]["source"] == "notes.pdf"
        assert data["citations"][0]["page"] == 2
        assert "dedicated function" in data["citations"][0]["snippet"]


def test_end_to_end_cite_or_refuse_on_insufficient_evidence():
    """
    Verify the Cite-or-Refuse principle: if context lacks evidence, the system refuses to answer.
    """
    client = TestClient(app)

    fake_matches = [
        {
            "id": "chunk-1",
            "score": 0.42,
            "metadata": {
                "text": "Discussion on microcontrollers and register configurations.",
                "document_id": "ddb5bb33dea17c3d30778fddd5c96320b2f08faeedc38b35ac5897f45e407c23",
                "source": "notes.pdf",
                "page": 4,
            },
        }
    ]

    mock_refusal = GroundedAnswer(
        answer=REFUSE_MESSAGE,
        grounded=False,
    )

    with patch("backend.rag.is_gemini_configured", return_value=True), \
         patch("backend.hybrid_search.get_pinecone_index") as mock_pinecone, \
         patch("backend.hybrid_search.get_embeddings") as mock_embeddings, \
         patch("backend.rag._get_llm") as mock_llm_factory:

        mock_embed_instance = MagicMock()
        mock_embed_instance.embed_query.return_value = [0.1] * 768
        mock_embeddings.return_value = mock_embed_instance

        mock_index_instance = MagicMock()
        mock_index_instance.query.return_value = {"matches": fake_matches}
        mock_pinecone.return_value = mock_index_instance

        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = mock_refusal
        mock_llm.with_structured_output.return_value = mock_structured
        mock_llm_factory.return_value = mock_llm

        response = client.post(
            "/ask",
            json={"question": "What is the capital of France?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["grounded"] is False
        assert len(data["citations"]) == 0
        assert REFUSE_MESSAGE in data["answer"]


def test_end_to_end_cross_document_synthesis():
    """
    Verify multi-document synthesis workflow across multiple academic papers.
    """
    client = TestClient(app)

    fake_chunks = [
        {
            "text": "Paper A proposes Priority Ceiling Protocol for real-time scheduling.",
            "chunk_id": "doc1-chunk-0",
            "document_id": "doc1",
            "source": "paper_a.pdf",
            "page": 3,
            "score": 0.91,
        },
        {
            "text": "Paper B analyzes Earliest Deadline First (EDF) dynamic priority bounds.",
            "chunk_id": "doc2-chunk-0",
            "document_id": "doc2",
            "source": "paper_b.pdf",
            "page": 7,
            "score": 0.89,
        },
    ]

    synthesis_markdown = (
        "### Executive Synthesis\n"
        "Both papers address task scheduling guarantees in real-time operating systems [1], [2].\n"
        "### Cross-Source Comparison\n"
        "Paper A investigates fixed-priority protocols with ceiling synchronization [1], whereas Paper B focuses on dynamic EDF guarantees [2]."
    )

    with patch("backend.rag.is_gemini_configured", return_value=True), \
         patch("backend.rag.hybrid_search", return_value=fake_chunks), \
         patch("backend.rag._get_llm") as mock_llm_factory:

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = synthesis_markdown
        mock_llm.invoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        response = client.post(
            "/synthesize",
            json={"topic": "Real-time task scheduling protocols", "document_ids": ["doc1", "doc2"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["grounded"] is True
        assert "Executive Synthesis" in data["answer"]
        assert len(data["citations"]) == 2
        assert data["citations"][0]["source"] == "paper_a.pdf"
        assert data["citations"][1]["source"] == "paper_b.pdf"


def test_end_to_end_executive_brief_summarization():
    """
    Verify executive brief summarization endpoint for a single paper.
    """
    client = TestClient(app)
    doc_id = "ddb5bb33dea17c3d30778fddd5c96320b2f08faeedc38b35ac5897f45e407c23"

    mock_summary_text = (
        "### 1. Research Objective & Problem\n"
        "To teach embedded systems and real-time operating system concepts.\n\n"
        "### 2. Core Methodology & Approach\n"
        "ARM Cortex architectural study and RTOS scheduling algorithms."
    )

    fake_chunks = [
        {"text": "Introduction to Embedded Systems", "page": 1, "document_id": doc_id}
    ]

    with patch("backend.rag.is_gemini_configured", return_value=True), \
         patch("backend.rag.hybrid_search", return_value=fake_chunks), \
         patch("backend.rag._get_llm") as mock_llm_factory:

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = mock_summary_text
        mock_llm.invoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        response = client.post(f"/documents/{doc_id}/summarize")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Research Objective" in data["summary"]


def test_end_to_end_document_ingestion_pipeline():
    """
    Verify complete document ingestion pipeline from file parsing to vector store upsertion.
    """
    import pymupdf
    from pathlib import Path
    from backend.ingestion_pipeline import ingest_document
    from backend.document_store import get_document, delete_document

    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Paper Title: Advanced Transformer Architectures for Academic Retrieval. Section 1: Transformers use self-attention to capture long-range dependencies across text.")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Section 2: Empirical results demonstrate that hybrid retrieval improves top-1 recall by 14.2% over sparse BM25 baselines.")
    temp_pdf_path = Path("backend/uploads/temp_pipeline_test.pdf")
    doc.save(str(temp_pdf_path))
    doc.close()

    try:
        with patch("backend.ingestion_pipeline.get_embeddings") as mock_embed, \
             patch("backend.ingestion_pipeline.delete_vectors_by_document_id") as mock_del, \
             patch("backend.ingestion_pipeline.store_chunks") as mock_store:

            mock_model = MagicMock()
            mock_model.embed_documents.side_effect = lambda texts: [[0.05] * 768 for _ in texts]
            mock_embed.return_value = mock_model
            mock_store.return_value = 2

            result = ingest_document(str(temp_pdf_path), source_name="Transformer Study.pdf")

            assert result["status"] == "ready"
            assert result["total_pages"] == 2
            assert result["total_chunks"] >= 1
            doc_id = result["document_id"]

            stored = get_document(doc_id)
            assert stored is not None
            assert stored["original_filename"] == "Transformer Study.pdf"
            assert stored["total_pages"] == 2

            delete_document(doc_id)
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink(missing_ok=True)


if __name__ == "__main__":
    tests = [
        ("test_end_to_end_ai_rag_workflow", test_end_to_end_ai_rag_workflow),
        ("test_end_to_end_cite_or_refuse_on_insufficient_evidence", test_end_to_end_cite_or_refuse_on_insufficient_evidence),
        ("test_end_to_end_cross_document_synthesis", test_end_to_end_cross_document_synthesis),
        ("test_end_to_end_executive_brief_summarization", test_end_to_end_executive_brief_summarization),
        ("test_end_to_end_document_ingestion_pipeline", test_end_to_end_document_ingestion_pipeline),
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

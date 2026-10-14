import os
from pathlib import Path
from typing import Any, Dict, Optional

from backend.chunking import attach_document_id, split_documents
from backend.config import MAX_FILE_SIZE_MB
from backend.document_loader import load_document
from backend.document_metadata import add_metadata, generate_document_id
from backend.document_store import save_document
from backend.embeddings import get_embeddings
from backend.vectorstore import delete_vectors_by_document_id, store_chunks


def ingest_document(
    file_path: str,
    document_id: Optional[str] = None,
    source_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest a document:
    1. Validates file size.
    2. Computes/validates SHA-256 document_id.
    3. Extracts pages with PyMuPDF/fallback.
    4. Attaches document_id and 1-indexed page metadata.
    5. Splits into overlapping chunks.
    6. Generates vector embeddings using Gemini.
    7. Cleanses stale vectors for this ID in Pinecone, then upserts new ones.
    8. Records document metadata in the document store.
    """
    path_obj = Path(file_path)
    if not path_obj.exists() or not path_obj.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size_bytes = path_obj.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File is too large ({file_size_mb:.1f} MB). Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    if document_id is None:
        with open(file_path, "rb") as file_handle:
            document_id = generate_document_id(file_handle)

    resolved_filename = source_name or path_obj.name

    # 1. Load document pages
    documents = load_document(file_path)
    total_pages = len(documents) if documents else 0

    if not documents:
        save_document(
            document_id=document_id,
            original_filename=resolved_filename,
            stored_filename=path_obj.name,
            size_bytes=file_size_bytes,
            file_extension=path_obj.suffix.lower(),
            total_pages=0,
            total_chunks=0,
            status="failed",
        )
        return {
            "message": "Failed: No readable content extracted from document",
            "document_id": document_id,
            "filename": resolved_filename,
            "total_pages": 0,
            "total_chunks": 0,
            "status": "failed",
        }

    # 2. Add metadata
    documents = add_metadata(
        documents,
        document_id=document_id,
        source_name=resolved_filename,
    )

    # 3. Split into semantic chunks
    chunks = split_documents(documents)
    chunks = attach_document_id(chunks, document_id)
    total_chunks = len(chunks)

    if not chunks:
        save_document(
            document_id=document_id,
            original_filename=resolved_filename,
            stored_filename=path_obj.name,
            size_bytes=file_size_bytes,
            file_extension=path_obj.suffix.lower(),
            total_pages=total_pages,
            total_chunks=0,
            status="failed",
        )
        return {
            "message": "Failed: No text chunks created from pages",
            "document_id": document_id,
            "filename": resolved_filename,
            "total_pages": total_pages,
            "total_chunks": 0,
            "status": "failed",
        }

    # 4. Generate embeddings via Gemini
    embeddings_model = get_embeddings()
    chunk_texts = [chunk.page_content for chunk in chunks]
    embeddings = embeddings_model.embed_documents(chunk_texts)

    # 5. Purge any stale vectors for this document_id (stateful idempotency), then upsert new chunks
    delete_vectors_by_document_id(document_id)
    store_chunks(chunks, embeddings)

    # 6. Save persistent document metadata
    save_document(
        document_id=document_id,
        original_filename=resolved_filename,
        stored_filename=path_obj.name,
        size_bytes=file_size_bytes,
        file_extension=path_obj.suffix.lower(),
        total_pages=total_pages,
        total_chunks=total_chunks,
        status="ready",
    )

    return {
        "message": "Document ingested successfully",
        "document_id": document_id,
        "filename": resolved_filename,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "status": "ready",
    }
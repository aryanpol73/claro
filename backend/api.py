import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from backend.config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    UPLOAD_DIR,
    is_gemini_configured,
    is_groq_configured,
    is_llm_configured,
    is_pinecone_configured,
    update_api_keys,
)
from backend.document_metadata import generate_document_id
from backend.document_store import (
    delete_document as delete_document_meta,
    get_document as get_document_meta,
    list_documents as list_documents_meta,
    save_document,
    update_document_summary,
)
from backend.ingestion_pipeline import ingest_document
from backend.rag import (
    Citation,
    RAGResponse,
    ask_rag,
    summarize_document,
    synthesize_cross_documents,
)
from backend.vectorstore import delete_vectors_by_document_id, document_exists

router = APIRouter()


class QuestionInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    document_id: Optional[str] = Field(
        default=None,
        description="Optional 64-char SHA-256 document_id to scope retrieval.",
    )
    top_k: Optional[int] = Field(default=4, ge=1, le=15)

    @field_validator("document_id", mode="before")
    @classmethod
    def clean_document_id(cls, value: Optional[str]) -> Optional[str]:
        if not value or str(value).strip() == "":
            return None
        cleaned = str(value).strip()
        if len(cleaned) == 64 and cleaned.isalnum():
            return cleaned
        raise ValueError("document_id must be a valid 64-character SHA-256 hex string.")


class SynthesizeInput(BaseModel):
    topic: str = Field(..., min_length=2, max_length=2000)
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of document IDs to synthesize across. If empty, uses whole library.",
    )


class CompareInput(BaseModel):
    document_ids: List[str] = Field(..., min_length=2, max_length=10)
    focus: Optional[str] = Field(
        default="Compare research objectives, methodology, key findings, and limitations.",
        max_length=1000,
    )


class KeysInput(BaseModel):
    groq_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: Optional[str] = None
    llm_model: Optional[str] = None



def _stored_path_for_document(document_id: str, original_filename: Optional[str] = None) -> Path:
    """Map a SHA-256 document_id to a file under uploads/, preserving extension."""
    upload_folder = Path(UPLOAD_DIR)
    if original_filename:
        suffix = Path(original_filename).suffix or ".pdf"
        return upload_folder / f"{document_id}{suffix}"

    matches = list(upload_folder.glob(f"{document_id}.*"))
    if matches:
        return matches[0]
    return upload_folder / f"{document_id}.pdf"


@router.get("/")
def home():
    return {
        "app": "Claro",
        "description": "AI-Powered Academic Research Assistant",
        "version": "1.0.0",
        "status": "operational",
    }


@router.get("/health")
@router.get("/status")
def system_status():
    docs = list_documents_meta()
    return {
        "status": "ready",
        "groq_configured": is_groq_configured(),
        "gemini_configured": is_gemini_configured(),
        "llm_configured": is_llm_configured(),
        "pinecone_configured": is_pinecone_configured(),
        "total_documents": len(docs),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "llm_model": os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
    }


@router.get("/config")
def get_config():
    return {
        "groq_configured": is_groq_configured(),
        "gemini_configured": is_gemini_configured(),
        "llm_configured": is_llm_configured(),
        "pinecone_configured": is_pinecone_configured(),
        "pinecone_index_name": os.getenv("PINECONE_INDEX_NAME", "academic-files-rag"),
        "llm_model": os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
    }


@router.post("/config/keys")
def set_api_keys(payload: KeysInput):
    result = update_api_keys(
        groq_api_key=payload.groq_api_key,
        google_api_key=payload.google_api_key,
        pinecone_api_key=payload.pinecone_api_key,
        pinecone_index_name=payload.pinecone_index_name,
        llm_model=payload.llm_model,
    )
    return {
        "status": "success",
        "message": "Configuration updated successfully",
        **result,
    }


@router.post("/documents/{document_id}/index")
async def index_document_endpoint(document_id: str):
    """Index or re-index a single document into Pinecone."""
    meta = get_document_meta(document_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = _stored_path_for_document(document_id, meta.get("original_filename"))
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored document file not found on disk.")

    if not is_pinecone_configured():
        raise HTTPException(status_code=400, detail="PINECONE_API_KEY is required to index documents.")

    res = await run_in_threadpool(
        ingest_document,
        str(file_path),
        document_id,
        meta.get("original_filename"),
    )
    return {
        "status": "success",
        "message": f"Successfully indexed {res.get('total_chunks', 0)} chunks into vector store.",
        **res,
    }


@router.post("/documents/index-all")
async def index_all_documents_endpoint():
    """Batch-index all documents that are pending index or stored."""
    if not is_pinecone_configured():
        raise HTTPException(status_code=400, detail="PINECONE_API_KEY is required to index documents.")

    docs = list_documents_meta()
    results = []
    for doc in docs:
        doc_id = doc.get("document_id")
        file_path = _stored_path_for_document(doc_id, doc.get("original_filename"))
        if file_path.is_file():
            try:
                res = await run_in_threadpool(
                    ingest_document,
                    str(file_path),
                    doc_id,
                    doc.get("original_filename"),
                )
                results.append({"document_id": doc_id, "status": "success", "chunks": res.get("total_chunks", 0)})
            except Exception as e:
                results.append({"document_id": doc_id, "status": "failed", "error": str(e)})
    return {
        "status": "complete",
        "indexed_count": len([r for r in results if r["status"] == "success"]),
        "results": results,
    }


@router.post("/ask", response_model=RAGResponse)
def ask(request: QuestionInput) -> RAGResponse:
    """Answer a research question using retrieved chunks with cite-or-refuse grounding."""
    try:
        metadata_filter = None
        if request.document_id:
            metadata_filter = {"document_id": request.document_id}

        return ask_rag(
            question=request.question,
            top_k=request.top_k or 4,
            metadata_filter=metadata_filter,
        )
    except Exception as e:
        safe_err = str(e).encode("ascii", "replace").decode("ascii")
        print(f"Error in /ask route: {safe_err}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {safe_err}")


@router.post("/synthesize", response_model=RAGResponse)
def synthesize(request: SynthesizeInput) -> RAGResponse:
    """Synthesize academic findings across multiple papers."""
    try:
        return synthesize_cross_documents(
            topic=request.topic,
            document_ids=request.document_ids,
        )
    except Exception as e:
        safe_err = str(e).encode("ascii", "replace").decode("ascii")
        print(f"Error in /synthesize route: {safe_err}")
        raise HTTPException(status_code=500, detail=f"Failed to synthesize documents: {safe_err}")


@router.post("/compare", response_model=RAGResponse)
def compare(request: CompareInput) -> RAGResponse:
    """Compare two or more selected papers on methods, findings, and limitations."""
    prompt = (
        f"Comparative Analysis Focus: {request.focus}\n"
        f"Compare and contrast the provided documents in terms of objectives, methodology, datasets, and conclusions."
    )
    try:
        return synthesize_cross_documents(
            topic=prompt,
            document_ids=request.document_ids,
        )
    except Exception as e:
        safe_err = str(e).encode("ascii", "replace").decode("ascii")
        print(f"Error in /compare route: {safe_err}")
        raise HTTPException(status_code=500, detail=f"Failed to compare documents: {safe_err}")


@router.post("/config/keys")
def set_keys(payload: KeysInput):
    """Save or update API credentials."""
    from backend.config import update_api_keys
    result = update_api_keys(
        google_api_key=payload.google_api_key,
        pinecone_api_key=payload.pinecone_api_key,
        pinecone_index_name=payload.pinecone_index_name,
    )
    return {
        "status": "success",
        "message": "Configuration updated successfully",
        **result,
    }


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """
    Ingest an academic document using SHA-256 content hashing.
    Duplicate files are idempotently recognized and skipped.
    """
    original_filename = file.filename or "document.pdf"
    file_ext = Path(original_filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        file_size_bytes = len(file_bytes)
        file_size_mb = file_size_bytes / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB} MB.",
            )

        document_id = generate_document_id(file_bytes)
        stored_path = _stored_path_for_document(document_id, original_filename)

        if not stored_path.is_file():
            stored_path.write_bytes(file_bytes)

        # If vector database is not configured yet, save file and extract metadata with pending_index status
        if not is_pinecone_configured():
            from backend.document_loader import load_document
            try:
                pages = await run_in_threadpool(load_document, str(stored_path))
                total_pages = len(pages)
            except Exception:
                total_pages = 0

            meta = save_document(
                document_id=document_id,
                original_filename=original_filename,
                stored_filename=stored_path.name,
                size_bytes=file_size_bytes,
                file_extension=file_ext,
                total_pages=total_pages,
                total_chunks=0,
                status="pending_index",
            )
            return {
                "message": f"Document uploaded ({total_pages} pages). Configure PINECONE_API_KEY in Setup to enable semantic search.",
                "document_id": document_id,
                "filename": original_filename,
                "skipped": False,
                "needs_indexing": True,
                "missing_keys": ["PINECONE_API_KEY"],
                "document": meta,
            }

        # Check if already indexed in Pinecone
        already_indexed = await run_in_threadpool(document_exists, document_id)
        if already_indexed:
            meta = save_document(
                document_id=document_id,
                original_filename=original_filename,
                stored_filename=stored_path.name,
                size_bytes=file_size_bytes,
                file_extension=file_ext,
                status="ready",
            )
            return {
                "message": "Document already indexed",
                "document_id": document_id,
                "filename": original_filename,
                "skipped": True,
                "document": meta,
            }

        # Ingest into vector store and index
        result = await run_in_threadpool(
            ingest_document,
            str(stored_path),
            document_id,
            original_filename,
        )

        doc_meta = get_document_meta(document_id)
        result["filename"] = original_filename
        result["skipped"] = False
        result["document"] = doc_meta
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.post("/documents/{document_id}/index")
async def index_document(document_id: str):
    """Index an uploaded document into Pinecone once API keys are active."""
    if not is_gemini_configured() or not is_pinecone_configured():
        missing = []
        if not is_gemini_configured():
            missing.append("GROQ_API_KEY")
        if not is_pinecone_configured():
            missing.append("PINECONE_API_KEY")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot index: {', '.join(missing)} must be configured in Setup.",
        )
    meta = get_document_meta(document_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found.")

    stored_path = _stored_path_for_document(document_id, meta.get("original_filename"))
    if not stored_path.exists():
        raise HTTPException(status_code=404, detail="Underlying document file not found.")

    result = await run_in_threadpool(
        ingest_document,
        str(stored_path),
        document_id,
        meta.get("original_filename"),
    )
    doc_meta = get_document_meta(document_id)
    result["document"] = doc_meta
    return result


@router.post("/documents/index-all")
async def index_all_documents():
    """Index all unindexed documents in the library."""
    if not is_gemini_configured() or not is_pinecone_configured():
        missing = []
        if not is_gemini_configured():
            missing.append("GROQ_API_KEY")
        if not is_pinecone_configured():
            missing.append("PINECONE_API_KEY")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot index: {', '.join(missing)} must be configured in Setup.",
        )
    docs = list_documents_meta()
    indexed_count = 0
    errors = []
    for doc in docs:
        doc_id = doc["document_id"]
        stored_path = _stored_path_for_document(doc_id, doc.get("original_filename"))
        if stored_path.exists():
            try:
                await run_in_threadpool(
                    ingest_document,
                    str(stored_path),
                    doc_id,
                    doc.get("original_filename"),
                )
                indexed_count += 1
            except Exception as e:
                errors.append(f"{doc.get('original_filename')}: {e}")
    return {
        "indexed_count": indexed_count,
        "total_documents": len(docs),
        "errors": errors,
    }


@router.get("/files")
@router.get("/documents")
def list_files():
    """List all registered academic documents with full metadata."""
    try:
        docs = list_documents_meta()
        # Maintain backward compatibility with older 'name' attribute
        formatted_files = []
        for doc in docs:
            item = dict(doc)
            item["name"] = doc.get("original_filename") or doc.get("stored_filename") or doc.get("document_id")
            item["filename"] = item["name"]
            item["modified"] = doc.get("uploaded_at")
            formatted_files.append(item)
        return {"files": formatted_files, "documents": docs}
    except Exception as e:
        print(f"LIST FILES ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents.")


@router.get("/documents/{document_id}")
def get_document_details(document_id: str):
    """Retrieve detailed metadata for a specific document."""
    meta = get_document_meta(document_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found.")
    return meta


@router.post("/documents/{document_id}/summarize")
def summarize_doc(document_id: str):
    """Generate an Academic Executive Brief for a document."""
    meta = get_document_meta(document_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found.")

    original_filename = meta.get("original_filename", "document.pdf")
    result = summarize_document(document_id, original_filename)

    if result.get("status") == "success" and result.get("summary"):
        update_document_summary(document_id, result["summary"])

    return result


@router.get("/documents/{document_id}/file")
@router.get("/files/{filename}")
def get_file(document_id: Optional[str] = None, filename: Optional[str] = None):
    """Stream/view an uploaded document PDF or DOCX."""
    upload_folder = Path(UPLOAD_DIR).resolve()

    target_path = None
    original_display_name = "document.pdf"

    if document_id and len(document_id) == 64:
        target_path = _stored_path_for_document(document_id).resolve()
        meta = get_document_meta(document_id)
        if meta and meta.get("original_filename"):
            original_display_name = meta["original_filename"]
    elif filename:
        clean_name = Path(filename).name
        target_path = (upload_folder / clean_name).resolve()
        original_display_name = clean_name
        # If filename was a document_id or has document_id prefix, check metadata
        stem = Path(clean_name).stem
        if len(stem) == 64:
            meta = get_document_meta(stem)
            if meta and meta.get("original_filename"):
                original_display_name = meta["original_filename"]

    if not target_path or not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    if not target_path.is_relative_to(upload_folder):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    suffix = target_path.suffix.lower()
    media_type = (
        "application/pdf"
        if suffix == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if suffix == ".docx"
        else "application/octet-stream"
    )

    # Use inline Content-Disposition so browsers can preview PDFs inside an iframe/embed
    headers = {
        "Content-Disposition": f'inline; filename="{original_display_name}"'
    }

    return FileResponse(
        path=target_path,
        media_type=media_type,
        headers=headers,
    )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> dict:
    """
    Remove a document's Pinecone vectors, physical file, and registry metadata.
    Enforces 'No Orphaned Data'.
    """
    if not document_id or not document_id.isalnum() or len(document_id) != 64:
        raise HTTPException(
            status_code=400,
            detail="document_id must be a 64-character SHA-256 hex digest.",
        )

    try:
        # 1. Purge Pinecone vectors
        deleted_vectors = await run_in_threadpool(
            delete_vectors_by_document_id,
            document_id,
        )

        # 2. Delete physical file
        upload_folder = Path(UPLOAD_DIR).resolve()
        file_path = _stored_path_for_document(document_id).resolve()
        file_deleted = False

        if file_path.exists():
            if not file_path.is_relative_to(upload_folder):
                raise HTTPException(status_code=400, detail="Invalid document path.")
            if file_path.is_file():
                file_path.unlink()
                file_deleted = True

        # 3. Clean up metadata store
        meta_deleted = delete_document_meta(document_id)

        if deleted_vectors == 0 and not file_deleted and not meta_deleted:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "deleted_vectors": deleted_vectors,
            "file_deleted": file_deleted,
            "metadata_deleted": meta_deleted,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"DELETE DOCUMENT ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document.")

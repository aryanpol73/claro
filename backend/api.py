import os
from datetime import datetime
from pathlib import Path

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from backend.config import UPLOAD_DIR
from backend.document_metadata import generate_document_id
from backend.ingestion_pipeline import ingest_document
from backend.rag import RAGResponse, ask_rag
from backend.vectorstore import delete_vectors_by_document_id, document_exists

router = APIRouter()


class QuestionInput(BaseModel):
    question: str = Field(..., max_length=2000)
    document_id: Optional[str] = Field(
        default=None,
        description="When set, retrieve only chunks from this SHA-256 document_id.",
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-fA-F]{64}$",
    )

    @field_validator("document_id", mode="before")
    @classmethod
    def empty_document_id(cls, value: Optional[str]) -> Optional[str]:
        if value == "":
            return None
        return value


def _stored_path_for_document(document_id: str, original_filename: str | None = None) -> Path:
    """Map a SHA-256 document_id to a file under uploads/, preserving extension."""
    upload_folder = Path(UPLOAD_DIR)
    if original_filename:
        suffix = Path(original_filename).suffix
        return upload_folder / f"{document_id}{suffix}"

    matches = list(upload_folder.glob(f"{document_id}.*"))
    if matches:
        return matches[0]
    return upload_folder / document_id


@router.get("/")
def home():
    return {"message": "Backend is working!"}


@router.post("/ask", response_model=RAGResponse)
def ask(request: QuestionInput) -> RAGResponse:
    """Answer a question using retrieved chunks, optionally scoped to one document."""
    print("HELLO FROM BACKEND FOLDER!")
    try:
        metadata_filter = None
        if request.document_id:
            metadata_filter = {"document_id": request.document_id}

        return ask_rag(
            request.question,
            metadata_filter=metadata_filter,
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="The server encountered an error.")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """Ingest a document using a SHA-256 content hash as document_id.

    Duplicate bytes are skipped (idempotent). Already-indexed vectors are not rebuilt.
    """
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        document_id = generate_document_id(file_bytes)
        original_filename = file.filename or "document"
        file_path = _stored_path_for_document(document_id, original_filename)

        already_indexed = await run_in_threadpool(document_exists, document_id)
        if already_indexed:
            if not file_path.is_file():
                file_path.write_bytes(file_bytes)
            return {
                "message": "Document already indexed",
                "document_id": document_id,
                "filename": original_filename,
                "skipped": True,
            }

        file_path.write_bytes(file_bytes)

        result = await run_in_threadpool(
            ingest_document,
            str(file_path),
            document_id,
            original_filename,
        )
        result["filename"] = original_filename
        result["skipped"] = False
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the document.")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> dict:
    """Remove a document's Pinecone vectors and its file under uploads/."""
    if not document_id or not document_id.isalnum() or len(document_id) != 64:
        raise HTTPException(
            status_code=400,
            detail="document_id must be a 64-character SHA-256 hex digest.",
        )

    try:
        deleted_vectors = await run_in_threadpool(
            delete_vectors_by_document_id,
            document_id,
        )

        upload_folder = Path(UPLOAD_DIR).resolve()
        file_path = _stored_path_for_document(document_id).resolve()
        file_deleted = False

        if file_path.exists():
            if not file_path.is_relative_to(upload_folder):
                raise HTTPException(status_code=400, detail="Invalid document path.")
            if file_path.is_file():
                file_path.unlink()
                file_deleted = True

        if deleted_vectors == 0 and not file_deleted:
            raise HTTPException(
                status_code=404,
                detail="Document not found in Pinecone or uploads/.",
            )

        return {
            "message": "Document deleted",
            "document_id": document_id,
            "deleted_vectors": deleted_vectors,
            "file_deleted": file_deleted,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"DELETE DOCUMENT ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete the document.")


@router.get("/files")
def list_files():
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        upload_folder = Path(UPLOAD_DIR)
        files = []
        for entry in upload_folder.iterdir():
            if entry.is_file():
                stat = entry.stat()
                files.append({
                    "name": entry.name,
                    "document_id": entry.stem,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        # Show the most recently uploaded files first
        files.sort(key=lambda f: f["modified"], reverse=True)
        return {"files": files}
    except Exception as e:
        print(f"LIST FILES ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to list uploaded files.")


@router.get("/files/{filename}")
def get_file(filename: str):
    upload_folder = Path(UPLOAD_DIR).resolve()
    file_path = (upload_folder / filename).resolve()

    # Safety check: the file must live inside the uploads folder
    if not file_path.is_relative_to(upload_folder):
        raise HTTPException(status_code=400, detail="Invalid file name.")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    media_type = (
        "application/pdf"
        if file_path.suffix.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if file_path.suffix.lower() == ".docx"
        else "application/octet-stream"
    )

    return FileResponse(path=file_path, media_type=media_type, filename=file_path.name)

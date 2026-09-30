import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


from backend.rag import ask_rag
# --- NEW CHANGE: Import the tool that adds documents to your database ---
from backend.ingestion_pipeline import ingest_document
from backend.config import UPLOAD_DIR

router = APIRouter()

class QuestionInput(BaseModel):
    question: str = Field(..., max_length=2000)

@router.get("/")
def home():
    return {"message": "Backend is working!"}

@router.post("/ask")
def ask(request: QuestionInput):
    print("HELLO FROM BACKEND FOLDER!")
    try:
        result = ask_rag(
            request.question
        )
        return result
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="The server encountered an error.")

# --- NEW CHANGE: Create the /upload route to receive the file from React ---
@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    try:
        # 1. Create the uploads folder if it does not exist yet
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 2. Save the uploaded file into that folder
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
            
        # 3. Send the saved file to your database pipeline
        result = ingest_document(file_path)
        
        return result
        
    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the document.")


# --- NEW CHANGE: List all uploaded files so the frontend can show them ---
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


# --- NEW CHANGE: Serve one uploaded file so users can view/download it ---
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
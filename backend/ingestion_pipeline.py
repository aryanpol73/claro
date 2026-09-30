import os

from backend.config import MAX_FILE_SIZE_MB

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

from backend.document_loader import load_document
from backend.document_metadata import add_metadata, generate_document_id
from backend.chunking import attach_document_id, split_documents
from backend.embeddings import get_embeddings
from backend.vectorstore import delete_vectors_by_document_id, store_chunks

def ingest_document(file_path: str, document_id: str | None = None) -> dict:

    # Check file size before starting ingestion
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File is too large. Maximum allowed size is "
            f"{MAX_FILE_SIZE_MB} MB."
        )

    if document_id is None:
        with open(file_path, "rb") as file_handle:
            document_id = generate_document_id(file_handle)

    # 1. Load document
    documents = load_document(file_path)
    # 2. Add metadata
    documents = add_metadata(documents, document_id=document_id)
    print(f"DEBUG 1: Loaded {len(documents) if documents else 0} pages from the PDF.")



    
    # 3. Split into chunks
    chunks = split_documents(documents)
    chunks = attach_document_id(chunks, document_id)
    print(f"DEBUG 2: Created {len(chunks) if chunks else 0} chunks from the pages.")

    #SAFETY CHECK
    if not chunks:
        print("DEBUG 3: No chunks to store, stopping ingestion.")
        return {
            "message": "Failed: No chunks created",
            "document_id": document_id,
            "total_pages": len(documents) if documents else 0,
            "total_chunks": 0
        }
    # 4. Create embeddings
    embeddings_model = get_embeddings()

    embeddings = embeddings_model.embed_documents(
        [chunk.page_content for chunk in chunks]
    )

    # 5. Purge stale vectors for this ID, then upsert the new chunks
    delete_vectors_by_document_id(document_id)
    store_chunks(chunks, embeddings)

    # 6. Return ingestion information
    return {
        "message": "Document ingested successfully",
        "document_id": document_id,
        "total_pages": len(documents),
        "total_chunks": len(chunks)
    }
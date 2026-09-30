import os

from backend.config import MAX_FILE_SIZE_MB

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

from backend.document_loader import load_document
from backend.document_metadata import add_metadata
from backend.chunking import split_documents
from backend.embeddings import get_embeddings
from backend.vectorstore import store_chunks

def ingest_document(file_path):

    # Check file size before starting ingestion
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File is too large. Maximum allowed size is "
            f"{MAX_FILE_SIZE_MB} MB."
        )

    # 1. Load document
    documents = load_document(file_path)
    # 2. Add metadata
    documents = add_metadata(documents)
    print(f"DEBUG 1: Loaded {len(documents) if documents else 0} pages from the PDF.")



    
    # 3. Split into chunks
    chunks = split_documents(documents)
    print(f"DEBUG 2: Created {len(chunks) if chunks else 0} chunks from the pages.")

    #SAFETY CHECK
    if not chunks:
        print("DEBUG 3: No chunks to store, stopping ingestion.")
        return {
            "message": "Failed: No chunks created",
            "total_pages": len(documents) if documents else 0,
            "total_chunks": 0
        }
    # 4. Create embeddings
    embeddings_model = get_embeddings()

    embeddings = embeddings_model.embed_documents(
        [chunk.page_content for chunk in chunks]
    )

    # 5. Store chunks in Pinecone
    store_chunks(chunks, embeddings)

    # 6. Return ingestion information
    return {
        "message": "Document ingested successfully",
        "total_pages": len(documents),
        "total_chunks": len(chunks)
    }
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pinecone import Pinecone

from backend.config import PINECONE_INDEX_NAME, get_pinecone_api_key

load_dotenv()

CHUNK_ID_PREFIX_TEMPLATE = "{document_id}-chunk-"


def get_pinecone_client() -> Pinecone:
    api_key = get_pinecone_api_key()
    if not api_key:
        raise ValueError("PINECONE_API_KEY is not set. Please set PINECONE_API_KEY in your .env file.")
    return Pinecone(api_key=api_key)


def ensure_pinecone_index_exists() -> None:
    """Ensure the Pinecone index exists, creating it serverless if needed."""
    pc = get_pinecone_client()
    index_name = PINECONE_INDEX_NAME
    try:
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            from pinecone import ServerlessSpec
            import time
            pc.create_index(
                name=index_name,
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            for _ in range(15):
                try:
                    desc = pc.describe_index(index_name)
                    status = getattr(desc, "status", None) or {}
                    if isinstance(status, dict) and status.get("ready"):
                        break
                    elif hasattr(status, "ready") and status.ready:
                        break
                except Exception:
                    pass
                time.sleep(1)
            print(f"Created Pinecone index '{index_name}' successfully.")
    except Exception as e:
        print(f"Pinecone index check notice: {e}")


def get_pinecone_index():
    pc = get_pinecone_client()
    try:
        return pc.Index(PINECONE_INDEX_NAME)
    except Exception:
        ensure_pinecone_index_exists()
        return pc.Index(PINECONE_INDEX_NAME)


def _chunk_id_prefix(document_id: str) -> str:
    return CHUNK_ID_PREFIX_TEMPLATE.format(document_id=document_id)


def list_vector_ids_for_document(document_id: str) -> List[str]:
    """Return all Pinecone vector IDs for a SHA-256 document_id."""
    index = get_pinecone_index()
    prefix = _chunk_id_prefix(document_id)
    collected: List[str] = []

    try:
        for page in index.list(prefix=prefix):
            # Pinecone SDK v5+ / v10 can return page as list of strings or page.vectors
            if hasattr(page, "vectors") and page.vectors:
                for item in page.vectors:
                    collected.append(item.id if hasattr(item, "id") else str(item))
            elif isinstance(page, list):
                for item in page:
                    collected.append(item.id if hasattr(item, "id") else str(item))
            elif hasattr(page, "__iter__"):
                for item in page:
                    collected.append(item.id if hasattr(item, "id") else str(item))
    except Exception as e:
        print(f"Warning during vector listing for {document_id}: {e}")

    return collected


def document_exists(document_id: str) -> bool:
    """True if this document_id already has at least one vector in Pinecone."""
    try:
        index = get_pinecone_index()
        prefix = _chunk_id_prefix(document_id)

        for page in index.list(prefix=prefix, limit=1):
            if hasattr(page, "vectors") and page.vectors:
                return True
            if isinstance(page, list) and len(page) > 0:
                return True
            if hasattr(page, "__iter__"):
                for _ in page:
                    return True
        return False
    except Exception as e:
        print(f"Check document_exists failed: {e}")
        return False


def delete_vectors_by_document_id(document_id: str) -> int:
    """Purge every vector whose ID is tied to this document_id. Returns count deleted."""
    vector_ids = list_vector_ids_for_document(document_id)
    if not vector_ids:
        # Also attempt metadata filter delete as fallback if supported
        try:
            index = get_pinecone_index()
            index.delete(filter={"document_id": {"$eq": document_id}})
            return 1
        except Exception:
            return 0

    index = get_pinecone_index()
    batch_size = 500
    for start in range(0, len(vector_ids), batch_size):
        batch = vector_ids[start:start + batch_size]
        index.delete(ids=batch)

    return len(vector_ids)


def store_chunks(chunks: List[Any], embeddings: List[List[float]], batch_size: int = 50) -> int:
    """Upsert chunk embeddings and rich metadata into Pinecone."""
    index = get_pinecone_index()
    vectors = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc_id = str(chunk.metadata.get("document_id", ""))
        vector_id = f"{doc_id}-chunk-{i}"
        page_val = str(chunk.metadata.get("page", ""))

        metadata = {
            "text": chunk.page_content,
            "document_id": doc_id,
            "source": str(chunk.metadata.get("source", "")),
            "page": page_val,
            "chunk_index": i,
        }

        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })

    # Upload in batches
    for start in range(0, len(vectors), batch_size):
        batch = vectors[start:start + batch_size]
        index.upsert(vectors=batch)

    print(f"Successfully stored {len(vectors)} chunks in Pinecone.")
    return len(vectors)


def search_chunks(query_embedding: List[float], top_k: int = 4, metadata_filter: Optional[Dict[str, Any]] = None):
    index = get_pinecone_index()
    return index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=metadata_filter
    )
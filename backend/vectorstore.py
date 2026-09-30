import os
from typing import List

from dotenv import load_dotenv
from pinecone import Pinecone


load_dotenv()

CHUNK_ID_PREFIX_TEMPLATE = "{document_id}-chunk-"


def get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY")

    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    pc = Pinecone(api_key=api_key)

    index = pc.Index("academic-files-rag")

    return index


def _chunk_id_prefix(document_id: str) -> str:
    return CHUNK_ID_PREFIX_TEMPLATE.format(document_id=document_id)


def list_vector_ids_for_document(document_id: str) -> List[str]:
    """Return all Pinecone vector IDs for a SHA-256 document_id."""
    index = get_pinecone_index()
    prefix = _chunk_id_prefix(document_id)
    collected: List[str] = []

    for page in index.list(prefix=prefix):
        collected.extend(item.id for item in page.vectors)

    return collected


def document_exists(document_id: str) -> bool:
    """True if this document_id already has at least one vector in Pinecone."""
    index = get_pinecone_index()
    prefix = _chunk_id_prefix(document_id)

    for page in index.list(prefix=prefix, limit=1):
        if page.vectors:
            return True
    return False


def delete_vectors_by_document_id(document_id: str) -> int:
    """Purge every vector whose ID is tied to this document_id. Returns count deleted."""
    vector_ids = list_vector_ids_for_document(document_id)
    if not vector_ids:
        return 0

    index = get_pinecone_index()
    batch_size = 1000
    for start in range(0, len(vector_ids), batch_size):
        index.delete(ids=vector_ids[start:start + batch_size])

    return len(vector_ids)


def store_chunks(chunks, embeddings, batch_size=50):

    index = get_pinecone_index()

    vectors = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

        vector_id = f"{chunk.metadata['document_id']}-chunk-{i}"

        metadata = {
            "text": chunk.page_content,
            "document_id": chunk.metadata.get("document_id", ""),
            "source": chunk.metadata.get("source", ""),
            "page": str(chunk.metadata.get("page", "")),
        }

        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })

    # Upload in batches
    for start in range(0, len(vectors), batch_size):

        batch = vectors[start:start + batch_size]

        index.upsert(
            vectors=batch
        )

    print(f"{len(vectors)} chunks stored successfully in Pinecone!")


def search_chunks(query_embedding, top_k=3):

    index = get_pinecone_index()

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    return results
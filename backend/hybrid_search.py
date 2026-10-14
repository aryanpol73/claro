import re
from typing import Any, Dict, List, Optional
from backend.config import TOP_K_RESULTS
from backend.embeddings import get_embeddings
from backend.vectorstore import get_pinecone_index


def _compute_lexical_overlap(query: str, text: str) -> float:
    """Compute normalized token overlap between query and text for hybrid ranking."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    if not query_tokens:
        return 0.0
    text_tokens = set(re.findall(r"\w+", text.lower()))
    overlap = len(query_tokens & text_tokens)
    return overlap / len(query_tokens)


def retrieve_documents(
    query: str,
    top_k: int = TOP_K_RESULTS,
    metadata_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve and rank the most relevant document chunks from Pinecone.
    Performs vector similarity search combined with lexical boost for hybrid ranking.
    """
    if not query or not query.strip():
        return []

    clean_query = query.strip()
    if len(clean_query) > 2000:
        clean_query = clean_query[:2000]

    if top_k <= 0:
        top_k = TOP_K_RESULTS

    # Retrieve slightly more candidates for hybrid re-ranking
    candidate_k = min(top_k * 2, 20)

    try:
        index = get_pinecone_index()
        embedding_model = get_embeddings()

        query_vector = embedding_model.embed_query(clean_query)

        results = index.query(
            vector=query_vector,
            top_k=candidate_k,
            include_metadata=True,
            filter=metadata_filter,
        )

        matches = (
            results.get("matches", [])
            if isinstance(results, dict)
            else getattr(results, "matches", None) or []
        )

    except Exception as error:
        print(f"Retrieval error in hybrid search: {error}")
        return []

    candidate_docs: List[Dict[str, Any]] = []

    for match in matches:
        metadata = (
            match.get("metadata", {})
            if isinstance(match, dict)
            else (getattr(match, "metadata", None) or {})
        )
        if hasattr(metadata, "items") and not isinstance(metadata, dict):
            metadata = dict(metadata)

        text = metadata.get("text") or ""
        vector_score = float(match.get("score") if isinstance(match, dict) else (getattr(match, "score", 0.0) or 0.0))

        # Lexical boost: give up to +0.15 boost for exact term matches
        lexical_boost = _compute_lexical_overlap(clean_query, text) * 0.15
        combined_score = vector_score + lexical_boost

        candidate_docs.append({
            "text": text,
            "score": round(combined_score, 4),
            "vector_score": round(vector_score, 4),
            "chunk_id": str(match.get("id") if isinstance(match, dict) else getattr(match, "id", "")),
            "document_id": str(metadata.get("document_id") or ""),
            "source": str(metadata.get("source") or "Unknown Document"),
            "page": metadata.get("page") or "",
            "metadata": metadata,
        })

    # Sort candidates by combined score and take top_k
    candidate_docs.sort(key=lambda d: d["score"], reverse=True)
    return candidate_docs[:top_k]
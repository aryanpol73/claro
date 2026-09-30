from backend.vectorstore import get_pinecone_index
from backend.embeddings import get_embeddings
from backend.config import TOP_K_RESULTS

def retrieve_documents(
    query: str,
    top_k: int = TOP_K_RESULTS,
    metadata_filter: dict | None = None
):
    """
    Retrieve the most relevant document chunks from Pinecone.
    """

    # --- NEW CHANGE: Stop the process if the user typed nothing ---
    if not query or not query.strip():
        return []

    # --- NEW CHANGE: Cut the text down if the user pastes too much text ---
    if len(query) > 2000:
        query = query[:2000]

    # --- NEW CHANGE: Reset to default if the frontend sends a negative number ---
    if top_k <= 0:
        top_k = TOP_K_RESULTS

    # --- NEW CHANGE: Start try block to safely handle internet/database going offline ---
    index = get_pinecone_index()
    embedding_model = get_embeddings()
    try:
        # 1. Convert user's question into an embedding

        # --- NEW CHANGE: Print the exact question being searched ---
        print(f"STEP 1: Converting question to numbers: {query}")
        query_vector = embedding_model.embed_query(query)


# --- NEW CHANGE: Print right before asking Pinecone ---
        print("STEP 2: Searching Pinecone database...")
        # 2. Search Pinecone
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter
        )

        matches = (
            results.get("matches", [])
            if isinstance(results, dict)
            else getattr(results, "matches", None) or []
        )
        print(f"STEP 3: Pinecone found {len(matches)} matches.")

        
    # --- NEW CHANGE: Catch the error and return an empty list so the app does not crash ---
    except Exception as error:
        print(f"Network error: {error}")
        return []

    documents = []

    for match in matches:
        metadata = (
            match.get("metadata", {})
            if isinstance(match, dict)
            else (getattr(match, "metadata", None) or {})
        )
        if hasattr(metadata, "items") and not isinstance(metadata, dict):
            metadata = dict(metadata)

        documents.append({
            "text": metadata.get("text") or "No text found",
            "score": match.get("score") if isinstance(match, dict) else getattr(match, "score", None),
            "chunk_id": (
                str(match.get("id") or "")
                if isinstance(match, dict)
                else str(getattr(match, "id", "") or "")
            ),
            "document_id": metadata.get("document_id", ""),
            "source": metadata.get("source", ""),
            "page": metadata.get("page", ""),
            "metadata": metadata
        })

    return documents
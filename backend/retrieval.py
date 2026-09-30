from vectorstore import index
from embeddings import embedding_model
from config import TOP_K_RESULTS


def retrieve_documents(query: str, top_k: int = TOP_K_RESULTS, metadata_filter=None):
    
    # 1. Fix for Empty Search: Stop the process if the user typed nothing or just spaces
    if not query or not query.strip():
        print("Error: The search box is empty.")
        return []

    # 2. Fix for Too Much Text: Cut the text to a safe limit (e.g., 2000 characters) so the AI does not crash
    if len(query) > 2000:
        print("Warning: Search text is too long. Cutting it down to fit limits.")
        query = query[:2000]

    try:
        # Convert user's question into an embedding
        query_vector = embedding_model.embed_query(query)


        # Search Pinecone
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter
        )
        # 4. Fix for Zero Results: Check if the database found nothing and return safely
        if not results.get("matches"):
            print("Notice: No matching documents were found.")
            return []
        # Extract useful information from the results
        documents = []

        for match in results["matches"]:
            documents.append({
                "text": match["metadata"].get("text"),
                "score": match["score"],
                "metadata": match["metadata"]
            })

        return documents
    # Catch the connection errors here so the server does not shut down 
    except Exception as error:
        print(f"System Error: The database connection failed. Details: {error}")
        return []
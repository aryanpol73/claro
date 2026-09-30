import os

from dotenv import load_dotenv
from pinecone import Pinecone


load_dotenv()


def get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY")

    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    pc = Pinecone(api_key=api_key)

    index = pc.Index("academic-files-rag")

    return index


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
import os
from typing import List
from dotenv import load_dotenv

from backend.config import EMBEDDING_MODEL, get_google_api_key

load_dotenv()

_fastembed_instance = None


class FastEmbeddingsWrapper:
    """Lightweight, local ONNX embeddings matching Pinecone 768-dimension schema."""

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        from fastembed import TextEmbedding

        self.model_name = model_name
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return [list(map(float, vec)) for vec in self.model.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        results = list(self.model.query_embed(text))
        if not results:
            return [0.0] * 768
        return [float(x) for x in results[0]]


def get_embeddings():
    """
    Returns an embedding generator.
    Prioritizes GoogleGenerativeAIEmbeddings if GOOGLE_API_KEY is configured and model is gemini,
    otherwise uses local FastEmbed BAAI/bge-base-en-v1.5 (768 dimensions, zero rate limits).
    """
    google_key = get_google_api_key()
    if google_key and "gemini" in EMBEDDING_MODEL.lower():
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL,
                google_api_key=google_key,
                output_dimensionality=768,
            )
        except Exception as e:
            print(f"Notice: Google embeddings fallback to FastEmbed: {e}")

    global _fastembed_instance
    if _fastembed_instance is None:
        _fastembed_instance = FastEmbeddingsWrapper(model_name=EMBEDDING_MODEL if "bge" in EMBEDDING_MODEL else "BAAI/bge-base-en-v1.5")
    return _fastembed_instance
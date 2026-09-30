from backend.hybrid_search import retrieve_documents as hybrid_search
from backend.config import TOP_K_RESULTS,LLM_MODEL,TEMPERATURE
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

# Gemini LLM
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    temperature=TEMPERATURE
)
@traceable(name="ask_rag")
def ask_rag(
    question: str,
    top_k: int = TOP_K_RESULTS,
    metadata_filter: dict | None = None
):
    """
    Retrieve relevant documents and generate an answer
    using Gemini.
    """
    question = str(question).strip()
    if not question:
        return {"answer": "Please provide a valid question.", "sources": []}

    if metadata_filter is not None and not isinstance(metadata_filter, dict):
        metadata_filter = None

    try:
        # 1. Retrieve relevant chunks
        documents = hybrid_search(
            query=question,
            top_k=top_k,
            metadata_filter=metadata_filter
        )
        if documents is None:
            documents = []
    except Exception as e:
        print(f"RAG SEARCH CRASH: {e}")
        documents = []

    # 2. Create context from retrieved chunks
    context = "\n\n".join(
        document.get("text", "")
        for document in documents
        if document.get("text")
    )[:15000]

    # 3. Prompt Gemini
    prompt = f"""
Answer the question using only the provided context.

If the answer cannot be found in the context, say:
"I don't have enough information in the provided notes."

Context:
{context}

Question:
{question}

Answer:
"""

    # 4. Generate answer
    try:
        response = llm.invoke(prompt)
        final_answer = response.content
    except Exception as e:
        
        print(f"GEMINI ERROR: {e}") 
        final_answer = "The AI service is temporarily unavailable."

    # 5. Return answer + sources
    return {
        "answer": final_answer,
        "sources": [
            {
                "text": document.get("text", "No text found"),
                "score": document.get("score", 0.0),
                "metadata": document.get("metadata", {})
            }
            for document in documents
        ]
    }
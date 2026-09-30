import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from pydantic import BaseModel, Field

from backend.config import LLM_MODEL, TEMPERATURE, TOP_K_RESULTS
from backend.hybrid_search import retrieve_documents as hybrid_search

REFUSE_MESSAGE = (
    "The uploaded materials do not contain sufficient evidence to answer this question."
)
SNIPPET_MAX_CHARS = 400
CITATION_MARKER = re.compile(r"\[(\d+)\]")


class Citation(BaseModel):
    document_id: str
    source: str
    page: int | None = None
    chunk_id: str
    snippet: str


class RAGResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool


class GroundedAnswer(BaseModel):
    """LLM-facing schema: citations are attached server-side from retrieved chunks."""

    answer: str
    grounded: bool = Field(
        description="True only if every factual claim is supported by the numbered sources."
    )


llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    temperature=TEMPERATURE,
)
structured_llm = llm.with_structured_output(GroundedAnswer)


def _parse_page(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _snippet(text: str) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= SNIPPET_MAX_CHARS:
        return cleaned
    return cleaned[: SNIPPET_MAX_CHARS - 1].rstrip() + "…"


def _citation_from_document(document: dict, index: int) -> Citation:
    metadata = document.get("metadata") or {}
    document_id = str(
        document.get("document_id")
        or metadata.get("document_id")
        or ""
    )
    source = str(document.get("source") or metadata.get("source") or "unknown")
    page = _parse_page(document.get("page", metadata.get("page")))
    chunk_id = str(document.get("chunk_id") or metadata.get("chunk_id") or f"source-{index}")
    return Citation(
        document_id=document_id,
        source=source,
        page=page,
        chunk_id=chunk_id,
        snippet=_snippet(str(document.get("text") or "")),
    )


def _format_context(documents: list[dict]) -> str:
    blocks: list[str] = []
    for i, document in enumerate(documents, start=1):
        citation = _citation_from_document(document, i)
        page_label = citation.page if citation.page is not None else "unknown"
        header = f"[Source {i}: doc={citation.source}, page={page_label}]"
        blocks.append(f"{header}\n{document.get('text') or ''}")
    return "\n\n".join(blocks)


def _cited_indices(answer: str, source_count: int) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for match in CITATION_MARKER.finditer(answer or ""):
        index = int(match.group(1))
        if 1 <= index <= source_count and index not in seen:
            seen.add(index)
            ordered.append(index)
    return ordered


def _response_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return "".join(parts)
    return str(content or "")


def _ungrounded(answer: str = REFUSE_MESSAGE) -> RAGResponse:
    return RAGResponse(answer=answer, citations=[], grounded=False)


@traceable(name="ask_rag")
def ask_rag(
    question: str,
    top_k: int = TOP_K_RESULTS,
    metadata_filter: dict | None = None,
) -> RAGResponse:
    """Retrieve chunks and return a cite-or-refuse RAGResponse."""
    question = str(question).strip()
    if not question:
        return _ungrounded("Please provide a valid question.")

    if metadata_filter is not None and not isinstance(metadata_filter, dict):
        metadata_filter = None

    try:
        documents = hybrid_search(
            query=question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        if documents is None:
            documents = []
    except Exception as e:
        print(f"RAG SEARCH CRASH: {e}")
        documents = []

    if not documents:
        return _ungrounded()

    context = _format_context(documents)[:15000]
    prompt = f"""You are Claro, a cite-or-refuse academic research assistant.

Rules:
- Use ONLY the numbered sources in the context.
- Tag every factual claim with an inline marker such as [1] or [2] that matches a Source number.
- If the context does not contain sufficient facts to answer, set grounded=false and set answer to exactly:
{REFUSE_MESSAGE}
- Never use outside knowledge, speculation, or unsourced claims.
- Do not invent page numbers, titles, or facts that are not in the sources.

Context:
{context}

Question:
{question}
"""

    try:
        parsed = structured_llm.invoke(prompt)
        if isinstance(parsed, GroundedAnswer):
            answer = parsed.answer
            grounded = parsed.grounded
        else:
            response = llm.invoke(prompt)
            answer = _response_text(getattr(response, "content", response))
            grounded = REFUSE_MESSAGE not in answer
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return _ungrounded("The AI service is temporarily unavailable.")

    if not grounded or REFUSE_MESSAGE in (answer or ""):
        return _ungrounded(REFUSE_MESSAGE if REFUSE_MESSAGE in (answer or "") else answer or REFUSE_MESSAGE)

    used_indices = _cited_indices(answer, len(documents))
    if not used_indices:
        used_indices = list(range(1, len(documents) + 1))

    citations = [
        _citation_from_document(documents[i - 1], i)
        for i in used_indices
    ]
    return RAGResponse(answer=answer, citations=citations, grounded=True)

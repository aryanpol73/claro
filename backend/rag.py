import os
import re
from typing import Any, Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from backend.config import (
    LLM_MODEL,
    TEMPERATURE,
    TOP_K_RESULTS,
    get_google_api_key,
    get_groq_api_key,
    is_gemini_configured,
    is_groq_configured,
    is_llm_configured,
)
from backend.hybrid_search import retrieve_documents as hybrid_search

REFUSE_MESSAGE = (
    "The uploaded materials do not contain sufficient evidence to answer this question."
)
SNIPPET_MAX_CHARS = 450
CITATION_MARKER = re.compile(r"\[(\d+)\]")


class Citation(BaseModel):
    document_id: str
    source: str
    page: Optional[int] = None
    chunk_id: str
    snippet: str
    score: Optional[float] = None


class RAGResponse(BaseModel):
    answer: str
    citations: List[Citation]
    grounded: bool
    mode: Optional[str] = "qa"


class GroundedAnswer(BaseModel):
    """LLM-facing structured output schema."""
    answer: str = Field(
        description="The detailed academic answer, with inline numerical citation markers like [1], [2] for every claim."
    )
    grounded: bool = Field(
        description="True ONLY if all factual statements in the answer are directly backed by the numbered sources. False if evidence is missing or insufficient."
    )


def _get_llm(model_name: Optional[str] = None):
    groq_key = get_groq_api_key()
    if groq_key:
        from langchain_groq import ChatGroq

        model = model_name or LLM_MODEL or "openai/gpt-oss-20b"
        return ChatGroq(
            model_name=model,
            temperature=TEMPERATURE,
            groq_api_key=groq_key,
        )

    google_key = get_google_api_key()
    if google_key:
        return ChatGoogleGenerativeAI(
            model=model_name or LLM_MODEL or "gemini-2.5-flash",
            temperature=TEMPERATURE,
            google_api_key=google_key,
        )

    raise ValueError(
        "Neither GROQ_API_KEY nor GOOGLE_API_KEY is configured. Please set GROQ_API_KEY in your .env file."
    )


def _parse_page(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_snippet(text: str) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= SNIPPET_MAX_CHARS:
        return cleaned
    return cleaned[: SNIPPET_MAX_CHARS - 1].rstrip() + "…"


def _citation_from_document(document: Dict[str, Any], index: int) -> Citation:
    metadata = document.get("metadata") or {}
    document_id = str(
        document.get("document_id")
        or metadata.get("document_id")
        or ""
    )
    source = str(document.get("source") or metadata.get("source") or "Academic Source")
    page = _parse_page(document.get("page", metadata.get("page")))
    chunk_id = str(document.get("chunk_id") or metadata.get("chunk_id") or f"source-{index}")
    score = document.get("score")

    return Citation(
        document_id=document_id,
        source=source,
        page=page,
        chunk_id=chunk_id,
        snippet=_clean_snippet(str(document.get("text") or "")),
        score=float(score) if score is not None else None,
    )


def _format_context(documents: List[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for i, document in enumerate(documents, start=1):
        citation = _citation_from_document(document, i)
        page_label = f"Page {citation.page}" if citation.page is not None else "Page unknown"
        header = f"[Source {i}: {citation.source} | {page_label} | ID={citation.chunk_id}]"
        blocks.append(f"{header}\n{document.get('text') or ''}")
    return "\n\n".join(blocks)


def _cited_indices(answer: str, source_count: int) -> List[int]:
    seen: set[int] = set()
    ordered: List[int] = []
    for match in CITATION_MARKER.finditer(answer or ""):
        index = int(match.group(1))
        if 1 <= index <= source_count and index not in seen:
            seen.add(index)
            ordered.append(index)
    return ordered


def _extract_response_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return "".join(parts)
    return str(content or "")


def _ungrounded_response(answer: str = REFUSE_MESSAGE, mode: str = "qa") -> RAGResponse:
    return RAGResponse(answer=answer, citations=[], grounded=False, mode=mode)


def ask_rag(
    question: str,
    top_k: int = TOP_K_RESULTS,
    metadata_filter: Optional[Dict[str, Any]] = None,
) -> RAGResponse:
    """
    Retrieve evidence from Pinecone and produce a cite-or-refuse grounded answer.
    """
    clean_question = str(question or "").strip()
    if not clean_question:
        return _ungrounded_response("Please provide a research question.")

    if not (is_llm_configured() or is_gemini_configured()):
        return _ungrounded_response(
            "AI service configuration required: Neither GROQ_API_KEY nor GOOGLE_API_KEY is configured. "
            "Please add GROQ_API_KEY to your .env file to enable synthesis and question answering."
        )

    try:
        documents = hybrid_search(
            query=clean_question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
    except Exception as search_err:
        print(f"RAG search error: {search_err}")
        documents = []

    if not documents:
        return _ungrounded_response(
            "No relevant passages were found in the uploaded documents for this query. "
            "Try broadening your terms or verifying that relevant documents are indexed."
        )

    context = _format_context(documents)[:16000]

    system_instruction = f"""You are Claro, a rigorous academic research assistant.
Your core principle is CITE-OR-REFUSE:
1. Ground every claim strictly in the numbered sources below.
2. Tag EVERY factual claim with an inline bracketed citation, e.g. [1], [2], corresponding to the source numbers.
3. If the context does not contain sufficient factual evidence to answer the question, you MUST set grounded=false and answer:
{REFUSE_MESSAGE}
4. Do NOT use outside knowledge, speculation, or hallucinated facts.
5. If there is partial information, explain what is supported with citations and clearly note what is not covered.

Context:
{context}

Question:
{clean_question}
"""

    try:
        llm = _get_llm()
        structured_llm = llm.with_structured_output(GroundedAnswer)
        parsed = structured_llm.invoke(system_instruction)

        if isinstance(parsed, GroundedAnswer):
            answer_text = parsed.answer
            is_grounded = parsed.grounded
        elif isinstance(parsed, dict) and "answer" in parsed:
            answer_text = str(parsed["answer"])
            is_grounded = bool(parsed.get("grounded", True))
        else:
            raw_response = llm.invoke(system_instruction)
            answer_text = _extract_response_text(getattr(raw_response, "content", raw_response))
            is_grounded = REFUSE_MESSAGE.lower() not in answer_text.lower()

    except Exception as llm_err:
        print(f"LLM execution error: {llm_err}. Attempting fallback...")
        try:
            fallback_model = "qwen/qwen3.8-27b" if is_groq_configured() else "gemini-1.5-flash"
            fallback_llm = _get_llm(model_name=fallback_model)
            raw_response = fallback_llm.invoke(system_instruction)
            answer_text = _extract_response_text(getattr(raw_response, "content", raw_response))
            is_grounded = REFUSE_MESSAGE.lower() not in answer_text.lower()
        except Exception as fallback_err:
            print(f"LLM fallback failed: {fallback_err}")
            return _ungrounded_response(
                f"The AI service could not process the request ({str(llm_err)[:100]}). Please check your API key and network connection."
            )

    if not is_grounded or REFUSE_MESSAGE in (answer_text or ""):
        return _ungrounded_response(answer_text if answer_text else REFUSE_MESSAGE)

    used_indices = _cited_indices(answer_text, len(documents))
    if not used_indices:
        used_indices = list(range(1, len(documents) + 1))

    citations = [_citation_from_document(documents[i - 1], i) for i in used_indices]
    return RAGResponse(answer=answer_text, citations=citations, grounded=True, mode="qa")


def synthesize_cross_documents(
    topic: str,
    document_ids: Optional[List[str]] = None,
    top_k_per_query: int = 5,
) -> RAGResponse:
    """
    Synthesize findings across multiple academic papers.
    Differentiates source findings, highlights consensus, contrasts methodologies,
    and grounds all synthesis in citations.
    """
    if not topic or not topic.strip():
        return _ungrounded_response("Please specify a topic or question to synthesize across documents.")

    if not (is_llm_configured() or is_gemini_configured()):
        return _ungrounded_response("GROQ_API_KEY is required to generate multi-document synthesis.")

    # Retrieve relevant chunks across the library or scoped documents
    all_chunks: List[Dict[str, Any]] = []

    if document_ids:
        for doc_id in document_ids:
            chunks = hybrid_search(query=topic, top_k=top_k_per_query, metadata_filter={"document_id": doc_id})
            all_chunks.extend(chunks)
    else:
        all_chunks = hybrid_search(query=topic, top_k=top_k_per_query * 2)

    if not all_chunks:
        return _ungrounded_response(
            "No evidence found in the document library related to this synthesis topic."
        )

    # Deduplicate chunks
    seen_chunk_ids = set()
    unique_chunks = []
    for c in all_chunks:
        cid = c.get("chunk_id")
        if cid not in seen_chunk_ids:
            seen_chunk_ids.add(cid)
            unique_chunks.append(c)

    context = _format_context(unique_chunks)[:18000]

    prompt = f"""You are Claro, conducting an academic synthesis across multiple research papers.

Topic:
{topic}

Context Passages:
{context}

Synthesis Instructions:
1. Synthesize the findings across the provided sources into a structured academic overview.
2. Structure your response into:
   - **Executive Synthesis**: A unified overview of the topic across the sources.
   - **Cross-Source Comparison**: Compare methodologies, datasets, or theoretical stances. Contrast where Source A finds X while Source B reports Y.
   - **Key Consensus & Divergence**: Points of agreement and conflicting findings.
   - **Open Questions & Limitations**: What remains unsolved according to the sources.
3. Every factual statement MUST cite the corresponding source with inline markers like [1], [2].
4. If the sources do not provide sufficient cross-document evidence, state so clearly.
"""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        answer_text = _extract_response_text(getattr(response, "content", response))
    except Exception as e:
        print(f"Synthesis error: {e}")
        return _ungrounded_response(f"Synthesis generation failed: {e}")

    used_indices = _cited_indices(answer_text, len(unique_chunks))
    if not used_indices:
        used_indices = list(range(1, min(len(unique_chunks) + 1, 6)))

    citations = [_citation_from_document(unique_chunks[i - 1], i) for i in used_indices]
    return RAGResponse(answer=answer_text, citations=citations, grounded=True, mode="synthesis")


def summarize_document(
    document_id: str,
    original_filename: str,
    top_chunks: int = 8,
) -> Dict[str, Any]:
    """
    Produce a structured academic brief for a single document.
    """
    if not (is_llm_configured() or is_gemini_configured()):
        return {
            "error": "GROQ_API_KEY required for document summarization.",
            "document_id": document_id,
        }

    # Retrieve representative chunks from the document
    chunks = hybrid_search(
        query="abstract introduction methodology results conclusion findings contribution",
        top_k=top_chunks,
        metadata_filter={"document_id": document_id},
    )

    if not chunks:
        return {
            "error": "No indexed content found for this document.",
            "document_id": document_id,
        }

    context = "\n\n".join(
        f"[Page {c.get('page', '?')}]: {c.get('text', '')}" for c in chunks
    )[:14000]

    prompt = f"""You are Claro, an academic research assistant.
Produce a structured Academic Executive Brief for the document '{original_filename}'.

Excerpts:
{context}

Format your output in clean Markdown with these exact sections:
### 1. Research Objective & Problem
What fundamental question or challenge does this work address?

### 2. Core Methodology & Approach
What techniques, frameworks, datasets, or theoretical models were employed?

### 3. Key Findings & Contributions
What are the main results, discoveries, or performance improvements?

### 4. Limitations & Future Directions
What constraints or open problems are acknowledged?
"""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        summary_text = _extract_response_text(getattr(response, "content", response))
        return {
            "document_id": document_id,
            "filename": original_filename,
            "summary": summary_text,
            "status": "success",
        }
    except Exception as e:
        return {
            "document_id": document_id,
            "error": f"Summarization failed: {e}",
            "status": "failed",
        }

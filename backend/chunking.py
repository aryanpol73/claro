from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    Split documents into semantically coherent chunks while preserving page and source metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        strip_whitespace=True,
    )

    raw_chunks = splitter.split_documents(documents)

    # Filter out empty or near-empty chunks
    valid_chunks = []
    for chunk in raw_chunks:
        content = (chunk.page_content or "").strip()
        if len(content) >= 20:  # Minimum useful text threshold
            chunk.page_content = content
            valid_chunks.append(chunk)

    return valid_chunks


def attach_document_id(chunks: List[Document], document_id: str) -> List[Document]:
    """Ensure every chunk carries the SHA-256 document_id and chunk_index before embedding."""
    for idx, chunk in enumerate(chunks):
        chunk.metadata["document_id"] = document_id
        chunk.metadata["chunk_index"] = idx
    return chunks

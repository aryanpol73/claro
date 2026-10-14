import hashlib
import os
from typing import Any, BinaryIO, List, Union
from langchain_core.documents import Document


def generate_document_id(file_bytes: Union[bytes, bytearray, BinaryIO]) -> str:
    """Return a 64-character SHA-256 hex digest of the file contents as the document_id."""
    hasher = hashlib.sha256()

    if hasattr(file_bytes, "read"):
        stream: BinaryIO = file_bytes  # type: ignore[assignment]
        current_pos = None
        if hasattr(stream, "tell") and hasattr(stream, "seek"):
            current_pos = stream.tell()
            stream.seek(0)

        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            hasher.update(block)

        if current_pos is not None:
            stream.seek(current_pos)
    else:
        hasher.update(bytes(file_bytes))

    return hasher.hexdigest()


def add_metadata(
    documents: List[Document],
    document_id: str,
    source_name: str | None = None,
) -> List[Document]:
    """Attach SHA-256 document_id and cleaned source/page fields to each page."""
    for idx, document in enumerate(documents, start=1):
        source_path = document.metadata.get("source", "")
        resolved_source = source_name or os.path.basename(source_path) or f"document_{document_id[:8]}"

        raw_page = document.metadata.get("page")
        raw_page_label = document.metadata.get("page_label")

        page_val = raw_page_label if (raw_page_label is not None and str(raw_page_label).strip() != "") else raw_page
        if page_val is None or str(page_val).strip() == "":
            page_val = idx

        try:
            page_num = int(page_val)
        except (ValueError, TypeError):
            page_num = idx

        document.metadata["source"] = resolved_source
        document.metadata["page"] = page_num
        document.metadata["document_id"] = document_id

    return documents

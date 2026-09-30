import hashlib
import os
from typing import BinaryIO, Union


def generate_document_id(file_bytes: Union[bytes, bytearray, BinaryIO]) -> str:
    """Return a SHA-256 hex digest of the file contents as the document_id."""
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


def add_metadata(documents, document_id: str):
    """Attach SHA-256 document_id and cleaned source/page fields to each page."""
    for document in documents:
        source_path = document.metadata.get("source", "")
        page_number = document.metadata.get("page_label", "")
        source_name = os.path.basename(source_path)

        document.metadata["source"] = source_name
        document.metadata["page"] = page_number
        document.metadata["document_id"] = document_id

    return documents

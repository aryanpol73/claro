import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document

from backend.pdf_ingestion import load_pdf


def load_document(file_path: str) -> List[Document]:
    """Load and parse documents supporting .pdf and .docx formats."""
    file_path_obj = Path(file_path)
    file_extension = file_path_obj.suffix.lower()

    if file_extension == ".pdf":
        return load_pdf(str(file_path_obj))

    elif file_extension == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(str(file_path_obj))
        docs = loader.load()
        for idx, doc in enumerate(docs):
            if "page" not in doc.metadata:
                doc.metadata["page"] = idx + 1
            doc.metadata["source"] = file_path_obj.name
        return docs

    else:
        raise ValueError(f"Unsupported file type '{file_extension}'. Claro supports .pdf and .docx documents.")
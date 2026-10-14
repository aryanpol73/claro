import os
from pathlib import Path
from typing import List
import pymupdf
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

# Attempt to locate Tesseract if installed, but never fail if absent
default_tessdata = Path(r"C:\Program Files\Tesseract-OCR\tessdata")
if default_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(default_tessdata))

MIN_TEXT_CHARS = 40
OCR_DPI = 150


def load_pdf(file_path: str) -> List[Document]:
    """
    Extract text and metadata from PDF files page-by-page.
    Uses PyPDFLoader for baseline extraction, supplements with PyMuPDF text,
    and attempts OCR only if Tesseract is available and text is sparse.
    """
    documents: List[Document] = []

    # First attempt extraction using PyMuPDF (fast, accurate, preserves layout)
    try:
        pdf = pymupdf.open(file_path)
        for page_number in range(len(pdf)):
            page = pdf.load_page(page_number)
            text = page.get_text("text").strip()

            meaningful_chars = sum(c.isalnum() for c in text)
            ocr_used = False

            # If page text is minimal (e.g., scanned page), attempt OCR if tessdata is available
            if meaningful_chars < MIN_TEXT_CHARS:
                try:
                    text_page = page.get_textpage_ocr(
                        language="eng",
                        dpi=OCR_DPI,
                        full=True,
                    )
                    ocr_text = page.get_text("text", textpage=text_page).strip()
                    if len(ocr_text) > len(text):
                        text = ocr_text
                        ocr_used = True
                except Exception as ocr_err:
                    # OCR not installed or failed on this page; continue with extracted text
                    pass

            doc = Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(file_path),
                    "page": page_number + 1,  # 1-indexed for academic citations
                    "total_pages": len(pdf),
                    "ocr_used": ocr_used,
                }
            )
            documents.append(doc)

        pdf.close()
        return documents

    except Exception as mupdf_err:
        print(f"PyMuPDF load failed for {file_path}: {mupdf_err}. Falling back to PyPDFLoader.")
        # Fallback to PyPDFLoader
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        for idx, doc in enumerate(docs):
            if "page" not in doc.metadata:
                doc.metadata["page"] = idx + 1
            else:
                # Ensure 1-indexed page
                try:
                    doc.metadata["page"] = int(doc.metadata["page"]) + 1
                except Exception:
                    doc.metadata["page"] = idx + 1
        return docs
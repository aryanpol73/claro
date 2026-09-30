import os
import pymupdf
from langchain_community.document_loaders import PyPDFLoader

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# A page with fewer than this many meaningful characters is treated
# as potentially scanned/image-only and sent through OCR.
MIN_TEXT_CHARS = 50

# Higher DPI gives OCR better image quality but takes more time.
OCR_DPI = 150


def load_pdf(file_path: str):
    # First try the normal, fast PDF text extraction.
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    pdf = pymupdf.open(file_path)

    try:
        for page_number, document in enumerate(documents):
            text = (document.page_content or "").strip()

            # Count actual alphanumeric characters rather than whitespace.
            meaningful_chars = sum(
                character.isalnum()
                for character in text
            )

            # Normal PDF text exists → keep it.
            if meaningful_chars >= MIN_TEXT_CHARS:
                document.metadata["ocr_used"] = False
                continue

            # Little/no text → use OCR for this page only.
            page = pdf.load_page(page_number)

            text_page = page.get_textpage_ocr(
                language="eng",
                dpi=OCR_DPI,
                full=True,
            )

            ocr_text = page.get_text(
                "text",
                textpage=text_page
            ).strip()

            document.page_content = ocr_text
            document.metadata["ocr_used"] = True

    finally:
        pdf.close()

    return documents
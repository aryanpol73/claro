import os

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

from langchain_community.document_loaders import Docx2txtLoader

from backend.pdf_ingestion import load_pdf

def load_document(file_path):

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":

        return load_pdf(file_path)

    elif file_extension == ".docx":

        loader = Docx2txtLoader(file_path)

        return loader.load()

    else:

        raise ValueError(
            f"Unsupported file type: {file_extension}"
        )
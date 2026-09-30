from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    return chunks


def attach_document_id(chunks, document_id: str):
    """Ensure every chunk carries the SHA-256 document_id before embedding."""
    for chunk in chunks:
        chunk.metadata["document_id"] = document_id
    return chunks

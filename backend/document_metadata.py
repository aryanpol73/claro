import os
import hashlib


def add_metadata(documents):

    for document in documents:

        source_path = document.metadata.get("source", "")
        page_number = document.metadata.get("page_label", "")

        # Get only the file name
        source_name = os.path.basename(source_path)

        # Create a stable unique ID for this document
        document_id = hashlib.md5(
            source_name.encode()
        ).hexdigest()

        # Store cleaned metadata
        document.metadata["source"] = source_name
        document.metadata["page"] = page_number
        document.metadata["document_id"] = document_id

    return documents
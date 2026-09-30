import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import time
load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")

if not api_key:
    raise ValueError("PINECONE_API_KEY not found in .env")

pc = Pinecone(api_key=api_key)

index_name = "academic-files-rag"

existing_indexes = [index.name for index in pc.list_indexes()]

if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    
    # Add these two lines so Python waits patiently for Pinecone to finish building
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(2)
    print("Index Created Succesfully.")

else:
    print(f"Index '{index_name}' already exists!")
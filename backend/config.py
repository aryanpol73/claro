import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true" 
os.environ["LANGSMITH_PROJECT"] = "Academic-Files-Rag"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
VECTOR_DB_DIR = BASE_DIR / "chroma_db"


ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB = 50

EMBEDDING_MODEL = "gemini-embedding-001"

LLM_MODEL = "gemini-3.6-flash"
TEMPERATURE = 0.0

TOP_K_RESULTS = 3

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

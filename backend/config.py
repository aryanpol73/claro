import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

load_dotenv()

# LangSmith configuration: safely handle missing or empty keys without crashing
langsmith_key = os.getenv("LANGSMITH_API_KEY")
if langsmith_key:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "Academic-Files-Rag")
    os.environ["LANGSMITH_API_KEY"] = langsmith_key
else:
    os.environ["LANGSMITH_TRACING"] = "false"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = PROJECT_ROOT / "data"
METADATA_FILE = UPLOAD_DIR / "documents_metadata.json"

# Ensure essential directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".ppt"}
MAX_FILE_SIZE_MB = 50

# Embedding & LLM configuration with safe defaults
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))

TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "4"))

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "academic-files-rag")


def reload_env() -> None:
    """Reload .env file to immediately pick up user credential changes."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            load_dotenv(env_file, override=True)
        except Exception:
            pass


def get_groq_api_key() -> str | None:
    reload_env()
    val = os.getenv("GROQ_API_KEY")
    if val and val.strip():
        return val.strip()
    return None


def get_google_api_key() -> str | None:
    reload_env()
    val = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if val and val.strip():
        return val.strip()
    return None


def get_pinecone_api_key() -> str | None:
    reload_env()
    val = os.getenv("PINECONE_API_KEY")
    if val and val.strip():
        return val.strip()
    return None


def is_groq_configured() -> bool:
    key = get_groq_api_key()
    return bool(key and key.strip())


def is_gemini_configured() -> bool:
    key = get_google_api_key()
    return bool(key and key.strip())


def is_llm_configured() -> bool:
    return is_groq_configured() or is_gemini_configured()


def is_pinecone_configured() -> bool:
    key = get_pinecone_api_key()
    return bool(key and key.strip())


def update_api_keys(
    groq_api_key: str | None = None,
    google_api_key: str | None = None,
    pinecone_api_key: str | None = None,
    pinecone_index_name: str | None = None,
    llm_model: str | None = None,
) -> dict:
    """Safely update environment variables and persist to .env file."""
    env_file = PROJECT_ROOT / ".env"
    existing_lines = []
    if env_file.exists():
        try:
            existing_lines = env_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            existing_lines = []

    env_dict = {}
    for line in existing_lines:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env_dict[k.strip()] = v.strip()

    if groq_api_key is not None:
        cleaned_groq = groq_api_key.strip()
        if cleaned_groq:
            os.environ["GROQ_API_KEY"] = cleaned_groq
            env_dict["GROQ_API_KEY"] = cleaned_groq
        else:
            os.environ.pop("GROQ_API_KEY", None)
            env_dict["GROQ_API_KEY"] = ""

    if google_api_key is not None:
        cleaned_google = google_api_key.strip()
        if cleaned_google:
            os.environ["GOOGLE_API_KEY"] = cleaned_google
            env_dict["GOOGLE_API_KEY"] = cleaned_google
        else:
            os.environ.pop("GOOGLE_API_KEY", None)
            env_dict["GOOGLE_API_KEY"] = ""

    if pinecone_api_key is not None:
        cleaned_pinecone = pinecone_api_key.strip()
        if cleaned_pinecone:
            os.environ["PINECONE_API_KEY"] = cleaned_pinecone
            env_dict["PINECONE_API_KEY"] = cleaned_pinecone
        else:
            os.environ.pop("PINECONE_API_KEY", None)
            env_dict["PINECONE_API_KEY"] = ""

    if pinecone_index_name and pinecone_index_name.strip():
        cleaned_index = pinecone_index_name.strip()
        os.environ["PINECONE_INDEX_NAME"] = cleaned_index
        env_dict["PINECONE_INDEX_NAME"] = cleaned_index

    if llm_model and llm_model.strip():
        cleaned_model = llm_model.strip()
        os.environ["LLM_MODEL"] = cleaned_model
        env_dict["LLM_MODEL"] = cleaned_model

    # Write back to .env
    out_lines = [
        "# Claro Environment Configuration",
        f"GROQ_API_KEY={env_dict.get('GROQ_API_KEY', os.getenv('GROQ_API_KEY', ''))}",
        f"GOOGLE_API_KEY={env_dict.get('GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY', ''))}",
        f"PINECONE_API_KEY={env_dict.get('PINECONE_API_KEY', os.getenv('PINECONE_API_KEY', ''))}",
        f"PINECONE_INDEX_NAME={env_dict.get('PINECONE_INDEX_NAME', PINECONE_INDEX_NAME)}",
        f"LLM_MODEL={env_dict.get('LLM_MODEL', LLM_MODEL)}",
        f"EMBEDDING_MODEL={env_dict.get('EMBEDDING_MODEL', EMBEDDING_MODEL)}",
        f"TEMPERATURE={env_dict.get('TEMPERATURE', str(TEMPERATURE))}",
        f"TOP_K_RESULTS={env_dict.get('TOP_K_RESULTS', str(TOP_K_RESULTS))}",
    ]
    try:
        env_file.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"Warning: Failed to persist .env: {e}")

    return {
        "groq_configured": is_groq_configured(),
        "gemini_configured": is_gemini_configured(),
        "llm_configured": is_llm_configured(),
        "pinecone_configured": is_pinecone_configured(),
        "pinecone_index_name": os.getenv("PINECONE_INDEX_NAME", PINECONE_INDEX_NAME),
        "llm_model": os.getenv("LLM_MODEL", LLM_MODEL),
    }

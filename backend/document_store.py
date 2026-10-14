import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import METADATA_FILE, UPLOAD_DIR

_lock = threading.Lock()


def _read_metadata_unlocked() -> Dict[str, Dict[str, Any]]:
    if not METADATA_FILE.exists():
        return {}
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception as e:
        print(f"Warning: Failed to read {METADATA_FILE}: {e}")
        return {}


def _write_metadata_unlocked(data: Dict[str, Dict[str, Any]]) -> None:
    import time
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = METADATA_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # On Windows (especially OneDrive folders), os.replace may trigger WinError 5
        # if the file is momentarily locked by the OneDrive sync engine or anti-virus.
        # We retry with a brief backoff, then fallback to direct write.
        replaced = False
        for attempt in range(6):
            try:
                temp_file.replace(METADATA_FILE)
                replaced = True
                break
            except (PermissionError, OSError):
                time.sleep(0.05 * (attempt + 1))
        
        if not replaced:
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if temp_file.exists():
                try:
                    temp_file.unlink(missing_ok=True)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error writing document metadata: {e}")
        try:
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as final_err:
            print(f"Direct fallback write also failed: {final_err}")
        if temp_file.exists():
            try:
                temp_file.unlink(missing_ok=True)
            except Exception:
                pass


def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        data = _read_metadata_unlocked()
        return data.get(document_id)


def list_documents() -> List[Dict[str, Any]]:
    with _lock:
        data = _read_metadata_unlocked()
        # Also check disk for any files not yet in registry
        upload_path = Path(UPLOAD_DIR)
        modified = False

        if upload_path.exists():
            for entry in upload_path.iterdir():
                if entry.is_file() and entry.name != METADATA_FILE.name and not entry.name.endswith(".tmp"):
                    doc_id = entry.stem
                    if len(doc_id) == 64 and doc_id not in data:
                        stat = entry.stat()
                        data[doc_id] = {
                            "document_id": doc_id,
                            "original_filename": entry.name,
                            "stored_filename": entry.name,
                            "file_extension": entry.suffix.lower(),
                            "size_bytes": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "total_pages": None,
                            "total_chunks": None,
                            "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "status": "ready",
                        }
                        modified = True

        if modified:
            _write_metadata_unlocked(data)

        docs = list(data.values())
        docs.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
        return docs


def save_document(
    document_id: str,
    original_filename: str,
    stored_filename: str,
    size_bytes: int,
    file_extension: str,
    total_pages: Optional[int] = None,
    total_chunks: Optional[int] = None,
    status: str = "ready",
    summary: Optional[str] = None,
    key_topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    with _lock:
        data = _read_metadata_unlocked()
        doc_entry = data.get(document_id, {})
        doc_entry.update({
            "document_id": document_id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_extension": file_extension,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "uploaded_at": doc_entry.get("uploaded_at") or datetime.utcnow().isoformat() + "Z",
            "total_pages": total_pages if total_pages is not None else doc_entry.get("total_pages"),
            "total_chunks": total_chunks if total_chunks is not None else doc_entry.get("total_chunks"),
            "status": status,
        })
        if summary is not None:
            doc_entry["summary"] = summary
        if key_topics is not None:
            doc_entry["key_topics"] = key_topics

        data[document_id] = doc_entry
        _write_metadata_unlocked(data)
        return doc_entry


def update_document_summary(document_id: str, summary: str, key_topics: Optional[List[str]] = None) -> bool:
    with _lock:
        data = _read_metadata_unlocked()
        if document_id in data:
            data[document_id]["summary"] = summary
            if key_topics:
                data[document_id]["key_topics"] = key_topics
            _write_metadata_unlocked(data)
            return True
        return False


def delete_document(document_id: str) -> bool:
    with _lock:
        data = _read_metadata_unlocked()
        if document_id in data:
            del data[document_id]
            _write_metadata_unlocked(data)
            return True
        return False

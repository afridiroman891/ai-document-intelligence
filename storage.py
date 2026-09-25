import hashlib
import re
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"

ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".txt"
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_file(filename, size):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: {ext or 'none'}"
    if size > MAX_UPLOAD_BYTES:
        return False, "File is larger than the 10 MB upload limit."
    return True, ""

def calculate_sha256(data):
    return hashlib.sha256(data).hexdigest()

def safe_filename(original_filename):
    original = Path(original_filename)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", original.stem).strip("_") or "document"
    ext = original.suffix.lower()
    return f"{stem}_{uuid.uuid4().hex[:10]}{ext}"

def category_folder(document_type):
    value = document_type.lower()
    if "invoice" in value:
        return STORAGE_DIR / "invoices"
    if "resume" in value:
        return STORAGE_DIR / "resumes"
    return STORAGE_DIR / "other"

def save_file(data, original_filename, document_type):
    folder = category_folder(document_type)
    folder.mkdir(parents=True, exist_ok=True)
    filename = safe_filename(original_filename)
    path = folder / filename
    path.write_bytes(data)
    return path, filename

def delete_file(file_path):
    path = Path(file_path)
    if path.exists() and path.is_file():
        path.unlink()

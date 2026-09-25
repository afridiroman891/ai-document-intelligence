import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "database" / "documents.db"

@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            document_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            company TEXT,
            invoice_number TEXT,
            total_amount REAL,
            file_path TEXT NOT NULL,
            text_preview TEXT,
            file_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL
        )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")

def get_by_hash(file_hash):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE file_hash = ?", (file_hash,)
        ).fetchone()
        return dict(row) if row else None

def create_document(data):
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO documents (
                original_filename, stored_filename, document_type, upload_date,
                company, invoice_number, total_amount, file_path,
                text_preview, file_hash, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["original_filename"], data["stored_filename"],
            data["document_type"], data["upload_date"], data.get("company"),
            data.get("invoice_number"), data.get("total_amount"),
            data["file_path"], data.get("text_preview"),
            data["file_hash"], data["status"]
        ))
        return cur.lastrowid

def list_documents(search="", document_type="All", status="All",
                   date_from="", date_to="", sort_order="Newest"):
    clauses = []
    params = []

    if search.strip():
        like = f"%{search.strip()}%"
        clauses.append("""(
            original_filename LIKE ? OR company LIKE ? OR
            invoice_number LIKE ? OR document_type LIKE ? OR
            text_preview LIKE ?
        )""")
        params.extend([like] * 5)

    if document_type != "All":
        clauses.append("document_type = ?")
        params.append(document_type)

    if status != "All":
        clauses.append("status = ?")
        params.append(status)

    if date_from:
        clauses.append("date(upload_date) >= date(?)")
        params.append(date_from)

    if date_to:
        clauses.append("date(upload_date) <= date(?)")
        params.append(date_to)

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    order = "ASC" if sort_order == "Oldest" else "DESC"

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM documents{where} ORDER BY datetime(upload_date) {order}",
            params
        ).fetchall()
        return [dict(r) for r in rows]

def get_document(doc_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        return dict(row) if row else None

def update_status(doc_id, status):
    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET status = ? WHERE id = ?",
            (status, doc_id)
        )

def delete_document(doc_id):
    doc = get_document(doc_id)
    if not doc:
        return False
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    return True

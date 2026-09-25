import tempfile
from pathlib import Path

def test_sha256():
    from storage import calculate_sha256
    assert len(calculate_sha256(b"hello")) == 64

def test_safe_filename():
    from storage import safe_filename
    name = safe_filename("my invoice 2026!.pdf")
    assert name.endswith(".pdf")
    assert " " not in name

# AI Document Intelligence — Week 4

A Streamlit-based document repository that builds on the document-processing workflow and adds organized storage, SQLite metadata, duplicate detection, search, filters, sorting, document details, status management and safer error handling.

## Week 4 features

- Organized storage for invoices, resumes and other documents
- Safe generated filenames
- Original filename preserved in SQLite
- SQLite document repository
- SHA-256 duplicate detection
- Multi-field search
- Document-type and processing-status filters
- Upload-date filters
- Newest/oldest sorting
- Document detail view
- File download
- Processing status: Processed, Needs Review, Failed
- Upload validation and 10 MB size limit
- OCR support for images when Tesseract is installed
- PDF text extraction
- README and tests

## Project structure

```text
ai-document-intelligence/
├── app.py
├── database.py
├── processor.py
├── storage.py
├── requirements.txt
├── README.md
├── database/
│   └── documents.db
├── storage/
│   ├── invoices/
│   ├── resumes/
│   └── other/
└── tests/
    └── test_repository.py
```

## Installation

Create a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## SQLite

The database is automatically created at:

```text
database/documents.db
```

The application creates the `documents` table automatically on startup.

## Duplicate detection

Every uploaded file is converted to a SHA-256 hash. The hash is stored as a unique database field. If a later upload has the same hash, the application reports the existing document instead of storing a second copy.

## Supported files

- PDF
- PNG
- JPG/JPEG
- TXT

Maximum upload size: 10 MB.

## OCR

Image OCR uses Tesseract through `pytesseract`. If OCR is required, install the Tesseract OCR engine separately and ensure it is available on PATH.

## Testing

Run:

```bash
pytest
```

The Week 4 task should also be manually tested with at least 10 documents, including invoices, resumes, other files, duplicate files, a scanned document and a document with missing fields.

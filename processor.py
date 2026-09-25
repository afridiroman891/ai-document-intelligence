import io
import re
from pathlib import Path

def extract_text(data, filename):
    """Extract text from TXT/PDF/images with OCR fallback."""
    import io
    from pathlib import Path

    ext = Path(filename).suffix.lower()

    # TXT
    if ext == ".txt":
        return data.decode("utf-8", errors="ignore")

    # PDF
    if ext == ".pdf":
        try:
            import fitz

            pdf = fitz.open(stream=data, filetype="pdf")

            # First try normal PDF text extraction
            text_parts = []

            for page in pdf:
                text_parts.append(page.get_text())

            text = "\n".join(text_parts).strip()

            if text:
                return text

            # If PDF has no text, use OCR
            try:
                from PIL import Image
                import pytesseract

                ocr_parts = []

                for page in pdf:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    image = Image.open(
                        io.BytesIO(pix.tobytes("png"))
                    )

                    ocr_text = pytesseract.image_to_string(image)
                    ocr_parts.append(ocr_text)

                return "\n".join(ocr_parts)

            except Exception:
                return ""

        except Exception:
            return ""

    # Images
    if ext in {".png", ".jpg", ".jpeg"}:
        try:
            from PIL import Image
            import pytesseract

            image = Image.open(io.BytesIO(data))
            return pytesseract.image_to_string(image)

        except Exception:
            return ""

    return ""

def clean_text(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text

def classify_document(text, filename):
    combined = f"{filename} {text}".lower()
    invoice_words = ["invoice", "invoice number", "bill to", "amount due", "subtotal"]
    resume_words = ["resume", "curriculum vitae", "experience", "education", "skills"]

    invoice_score = sum(word in combined for word in invoice_words)
    resume_score = sum(word in combined for word in resume_words)

    if invoice_score > resume_score and invoice_score > 0:
        return "Invoice"
    if resume_score > invoice_score and resume_score > 0:
        return "Resume"
    return "Other"

def extract_invoice_fields(text):
    text = text or ""
    invoice_number = None
    total_amount = None
    company = None

    patterns = [
        r"(?:invoice\s*(?:number|no|#))\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
        r"(?:inv\s*(?:no|#))\s*[:\-]?\s*([A-Za-z0-9\-\/]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            invoice_number = match.group(1)
            break

    amount_patterns = [
        r"(?:total|amount\s*due|grand\s*total)\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d{1,2})?)"
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            try:
                total_amount = float(match.group(1).replace(",", ""))
            except ValueError:
                pass
            break

    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if lines:
        for line in lines[:8]:
            if any(word in line.lower() for word in ["invoice", "bill", "company"]):
                continue
            if 2 <= len(line.split()) <= 8:
                company = line[:120]
                break

    return {
        "company": company,
        "invoice_number": invoice_number,
        "total_amount": total_amount
    }

def process_document(data, filename):
    raw_text = extract_text(data, filename)
    cleaned = clean_text(raw_text)
    document_type = classify_document(cleaned, filename)

    fields = extract_invoice_fields(raw_text) if document_type == "Invoice" else {
        "company": None, "invoice_number": None, "total_amount": None
    }

    important_missing = (
        document_type == "Invoice" and
        (not fields["invoice_number"] or fields["total_amount"] is None)
    )

    if not cleaned:
        status = "Failed"
    elif important_missing:
        status = "Needs Review"
    else:
        status = "Processed"

    return {
        "text": cleaned,
        "document_type": document_type,
        "company": fields["company"],
        "invoice_number": fields["invoice_number"],
        "total_amount": fields["total_amount"],
        "status": status
    }

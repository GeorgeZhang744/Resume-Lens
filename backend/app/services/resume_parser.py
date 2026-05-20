"""
Extract plain text from uploaded resume files (PDF or DOCX).

Used by POST /api/resume/parse before the analyze workflow runs.
"""

import re
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document

# Only these extensions are accepted
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# 5 MB max upload size
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


class ResumeParseError(Exception):
    """Raised when validation or parsing fails (mapped to HTTP 400 in routes)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters."""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _validate_extension(filename: str) -> str:
    """Return lowercase extension or raise."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ResumeParseError(
            f"Unsupported file type '{ext or '(none)'}'. Upload a .pdf or .docx file."
        )
    return ext


def _validate_size(content: bytes) -> None:
    if not content:
        raise ResumeParseError("Uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ResumeParseError(
            f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )


def parse_pdf(content: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ResumeParseError(f"Failed to read PDF: {exc}") from exc

    try:
        pages = [page.get_text() for page in doc]
    finally:
        doc.close()

    return _clean_text("\n".join(pages))


def parse_docx(content: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    try:
        document = Document(BytesIO(content))
    except Exception as exc:
        raise ResumeParseError(f"Failed to read DOCX: {exc}") from exc

    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return _clean_text("\n".join(paragraphs))


def parse_resume_file(filename: str, content: bytes) -> str:
    """
    Validate and parse an uploaded resume file.

    Args:
        filename: Original name (used for extension check).
        content: Raw file bytes from UploadFile.read().
    """
    _validate_size(content)
    ext = _validate_extension(filename)

    if ext == ".pdf":
        text = parse_pdf(content)
    else:
        text = parse_docx(content)

    if not text:
        raise ResumeParseError(
            "No text could be extracted from the file. "
            "Try a different PDF/DOCX or paste your resume as text."
        )

    return text

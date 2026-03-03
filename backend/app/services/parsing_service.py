"""
Parsing Service — extracts raw text with section headings and page numbers
from PDF (PyMuPDF) and DOCX (python-docx) files.
"""
import re
from pathlib import Path
from typing import List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ParsedPage:
    def __init__(self, text: str, page_number: int, section_heading: str | None = None):
        self.text = text
        self.page_number = page_number
        self.section_heading = section_heading


def extract_from_pdf(file_path: str) -> List[ParsedPage]:
    """Extract text from a PDF, preserving page numbers."""
    pages: List[ParsedPage] = []
    current_heading: str | None = None

    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None

    try:
        if fitz is not None:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                blocks = page.get_text("dict")["blocks"]
                page_text_parts = []
                for block in blocks:
                    if block["type"] == 0:  # text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if not text:
                                    continue
                                # Detect headings by font size / boldness
                                if span["size"] >= 13 or "Bold" in span.get("font", ""):
                                    current_heading = text
                                page_text_parts.append(text)

                full_text = " ".join(page_text_parts)
                if full_text.strip():
                    pages.append(ParsedPage(
                        text=full_text,
                        page_number=page_num,
                        section_heading=current_heading,
                    ))
            doc.close()
            logger.info("PDF parsed (PyMuPDF)", file=file_path, pages=len(pages))
            return pages

        from pypdf import PdfReader

        reader = PdfReader(file_path)
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if lines:
                    heading_candidate = lines[0]
                    if len(heading_candidate) <= 120 and re.match(r"^[A-Z0-9\s\-:()]+$", heading_candidate):
                        current_heading = heading_candidate
                pages.append(ParsedPage(
                    text=" ".join(lines) if lines else text,
                    page_number=page_num,
                    section_heading=current_heading,
                ))

        logger.info("PDF parsed (pypdf fallback)", file=file_path, pages=len(pages))
    except Exception as exc:
        logger.error("PDF parse error", file=file_path, error=str(exc))
        raise
    return pages


def extract_from_docx(file_path: str) -> List[ParsedPage]:
    """Extract text from DOCX, treating each heading as a new section."""
    pages: List[ParsedPage] = []
    current_heading: str | None = None
    buffer: List[str] = []
    virtual_page = 1

    try:
        from docx import Document

        doc = Document(file_path)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style.name.startswith("Heading"):
                if buffer:
                    pages.append(ParsedPage(
                        text=" ".join(buffer),
                        page_number=virtual_page,
                        section_heading=current_heading,
                    ))
                    virtual_page += 1
                    buffer = []
                current_heading = text
            else:
                buffer.append(text)

        if buffer:
            pages.append(ParsedPage(
                text=" ".join(buffer),
                page_number=virtual_page,
                section_heading=current_heading,
            ))

        logger.info("DOCX parsed", file=file_path, sections=len(pages))
    except Exception as exc:
        logger.error("DOCX parse error", file=file_path, error=str(exc))
        raise
    return pages


def parse_document(file_path: str) -> List[ParsedPage]:
    """Route to appropriate parser based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

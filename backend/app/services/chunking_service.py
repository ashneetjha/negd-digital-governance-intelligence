"""
Chunking Service — splits parsed pages into semantically coherent chunks.

Upgrade (production-grade):
────────────────────────────
BEFORE: Character-based sliding-window (fixed CHUNK_SIZE chars, CHUNK_OVERLAP chars back)
        Problem: cuts sentences mid-way, ignores paragraph structure.

AFTER: Paragraph + section-aware splitter
   1. Split page text into natural paragraphs (double-newline or heading boundaries)
   2. Detect section headings from bold/caps markers or known SeMT keywords
   3. Accumulate paragraphs until ~CHUNK_SIZE chars (~400 token equivalents at 4 chars/token)
   4. Never break mid-sentence — split at ". " / "\\n" boundaries within a paragraph
   5. Each chunk tagged with section_type, practice_area, section heading, page_number

Aligns to SeMT Monthly Report format for NeGD Digital Governance portal.
"""

from typing import List, Optional
import re

from app.config import settings
from app.services.parsing_service import ParsedPage
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Heading Detection
# ─────────────────────────────────────────────────────────────────────────────

# SeMT report section keywords → map to canonical section_type
_SECTION_KEYWORD_MAP = [
    (re.compile(r"ongoing\s+digital\s+governance\s+project", re.IGNORECASE), "ongoing_projects"),
    (re.compile(r"key\s+documents?\s+prepared", re.IGNORECASE), "documents_submitted"),
    (re.compile(r"major\s+activities?\s+perform", re.IGNORECASE), "major_activities"),
    (re.compile(r"proposed\s+activities?", re.IGNORECASE), "proposed_activities"),
    (re.compile(r"documents?\s+submitted", re.IGNORECASE), "documents_submitted"),
]

# Practice area keywords used in Major Activities
_PRACTICE_AREA_PATTERNS = [
    "digital transformation & strategy",
    "digital transformation and strategy",
    "data analytics and business intelligence",
    "emerging technologies",
    "it infra and cyber security",
    "it infrastructure",
    "cyber security",
]

# Heading detection: line is a heading if it's short, all-caps or title-case with known keywords,
# OR if it came from PyMuPDF as bold/large font (stored in section_heading of ParsedPage)
_HEADING_RE = re.compile(
    r"^(?:"
    r"[A-Z][A-Z0-9\s\-:()&/]{3,80}"   # ALL CAPS line
    r"|(?:(?:[A-Z][a-z]+\s?){2,8})"     # Title Case short phrase
    r")$"
)


def _is_heading_line(line: str) -> bool:
    """Returns True if a text line looks like a section heading."""
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False
    if re.match(r"^\d+[\.\)]\s", stripped):  # numbered list → not a heading
        return False
    return bool(_HEADING_RE.match(stripped))


def detect_section_type(text: str) -> str:
    """Detect high-level section category from SeMT report format."""
    for pattern, section_type in _SECTION_KEYWORD_MAP:
        if pattern.search(text):
            return section_type
    return "major_activities"  # safe default


def detect_practice_area(text: str) -> Optional[str]:
    """Extract practice area from Major Activities section text."""
    text_lower = text.lower()
    for pattern in _PRACTICE_AREA_PATTERNS:
        if pattern in text_lower:
            # Normalize to canonical form
            if "cyber" in pattern:
                return "it infra and cyber security"
            if "analytics" in pattern:
                return "data analytics and business intelligence"
            if "emerging" in pattern:
                return "emerging technologies"
            return "digital transformation & strategy"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Data Structure
# ─────────────────────────────────────────────────────────────────────────────

class TextChunk:
    def __init__(
        self,
        text: str,
        section_heading: Optional[str],
        page_number: int,
        chunk_index: int,
        section_type: str,
        practice_area: Optional[str],
    ):
        self.text = text
        self.section_heading = section_heading
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.section_type = section_type
        self.practice_area = practice_area


# ─────────────────────────────────────────────────────────────────────────────
# Paragraph Splitter
# ─────────────────────────────────────────────────────────────────────────────

def _split_into_paragraphs(text: str) -> List[str]:
    """
    Split raw page text into paragraph-level units.
    Splits on double-newline, single newline before a heading-like line,
    or any line break after 80+ chars.
    Strips empty units.
    """
    # Normalize Windows line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Primary split: double newline (paragraph break)
    raw_blocks = re.split(r"\n{2,}", text)

    paragraphs = []
    for block in raw_blocks:
        # Secondary: if a block contains heading-like lines, split on them
        lines = block.split("\n")
        current_lines = []
        for line in lines:
            if _is_heading_line(line) and current_lines:
                joined = " ".join(l.strip() for l in current_lines if l.strip())
                if joined:
                    paragraphs.append(joined)
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_lines:
            joined = " ".join(l.strip() for l in current_lines if l.strip())
            if joined:
                paragraphs.append(joined)

    return [p for p in paragraphs if p.strip()]


def _split_at_sentence_boundary(text: str, max_chars: int) -> List[str]:
    """
    Split a long paragraph into sentence-respecting sub-chunks of at most max_chars.
    Splits on '. ' or '! ' or '? ' boundaries.
    Never breaks a sentence mid-word.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        candidate = (current + " " + sentence).strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                parts.append(current)
            # If a single sentence is still too long, hard-truncate at word boundary
            if len(sentence) > max_chars:
                words = sentence.split()
                sub = ""
                for word in words:
                    trial = (sub + " " + word).strip()
                    if len(trial) <= max_chars:
                        sub = trial
                    else:
                        if sub:
                            parts.append(sub)
                        sub = word
                if sub:
                    parts.append(sub)
                current = ""
            else:
                current = sentence

    if current:
        parts.append(current)

    return parts


def _fallback_page_chunks(page: ParsedPage, max_chunk_chars: int, chunk_index_start: int) -> List[TextChunk]:
    """Create fallback chunks directly from raw page text when semantic chunking yields none."""
    text = (page.text or "").strip()
    if not text:
        return []

    section_type = detect_section_type(text)
    practice_area = detect_practice_area(text)
    parts = _split_at_sentence_boundary(text, max_chunk_chars)
    if not parts:
        parts = [text[i:i + max_chunk_chars].strip() for i in range(0, len(text), max_chunk_chars)]

    fallback_chunks: List[TextChunk] = []
    next_index = chunk_index_start
    for part in parts:
        part = part.strip()
        if not part:
            continue
        fallback_chunks.append(
            TextChunk(
                text=part,
                section_heading=page.section_heading,
                page_number=page.page_number,
                chunk_index=next_index,
                section_type=section_type,
                practice_area=practice_area,
            )
        )
        next_index += 1

    return fallback_chunks


# ─────────────────────────────────────────────────────────────────────────────
# Main Chunking Logic
# ─────────────────────────────────────────────────────────────────────────────

def chunk_pages(pages: List[ParsedPage]) -> List[TextChunk]:
    """
    Takes ParsedPage objects and returns semantically coherent text chunks.

    Strategy:
    1. Split each page into paragraphs (natural language boundaries)
    2. Track running section heading from PyMuPDF or heading detection
    3. Accumulate paragraphs into chunks up to CHUNK_SIZE chars (~400 tokens)
    4. Never break mid-sentence — uses sentence-boundary splitter for overlong paragraphs
    5. Each chunk tagged with section_type, practice_area, section_heading, page_number

    Returns:
        List[TextChunk] — ready for embedding and storage.
    """
    max_chunk_chars = settings.CHUNK_SIZE  # 1600 chars ≈ 400 tokens
    min_chunk_chars = 80  # discard trivially small chunks (e.g., lone headers)

    chunks: List[TextChunk] = []
    chunk_index = 0

    for page in pages:
        text = page.text
        if not text or not text.strip():
            continue

        # Page-level section inference (may be overridden paragraph-by-paragraph)
        page_section_type = detect_section_type(text)
        page_practice_area = detect_practice_area(text)

        # Use the heading extracted at parse time (from PyMuPDF bold/font detection)
        current_heading = page.section_heading

        paragraphs = _split_into_paragraphs(text)
        if not paragraphs:
            paragraphs = [text]

        accumulator: List[str] = []
        accumulator_chars = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Update current heading if this paragraph looks like a heading
            if _is_heading_line(para):
                # Flush accumulator before starting new section
                if accumulator:
                    chunk_text = " ".join(accumulator).strip()
                    if len(chunk_text) >= min_chunk_chars:
                        chunks.append(TextChunk(
                            text=chunk_text,
                            section_heading=current_heading,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                            section_type=page_section_type,
                            practice_area=page_practice_area,
                        ))
                        chunk_index += 1
                    accumulator = []
                    accumulator_chars = 0
                current_heading = para
                # Update section type based on new heading
                detected = detect_section_type(para)
                if detected != "major_activities":
                    page_section_type = detected
                detected_area = detect_practice_area(para)
                if detected_area:
                    page_practice_area = detected_area
                continue  # heading itself not added as content

            # If this single paragraph exceeds max_chunk_chars, split at sentences
            if len(para) > max_chunk_chars:
                # First flush accumulator
                if accumulator:
                    chunk_text = " ".join(accumulator).strip()
                    if len(chunk_text) >= min_chunk_chars:
                        chunks.append(TextChunk(
                            text=chunk_text,
                            section_heading=current_heading,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                            section_type=page_section_type,
                            practice_area=page_practice_area,
                        ))
                        chunk_index += 1
                    accumulator = []
                    accumulator_chars = 0

                # Split overlong paragraph into sentence-bounded sub-chunks
                sub_chunks = _split_at_sentence_boundary(para, max_chunk_chars)
                for sub in sub_chunks:
                    sub = sub.strip()
                    if len(sub) >= min_chunk_chars:
                        chunks.append(TextChunk(
                            text=sub,
                            section_heading=current_heading,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                            section_type=page_section_type,
                            practice_area=page_practice_area,
                        ))
                        chunk_index += 1
                continue

            # Accumulate: check if adding this paragraph would exceed limit
            if accumulator_chars + len(para) + 1 > max_chunk_chars and accumulator:
                # Flush and start fresh
                chunk_text = " ".join(accumulator).strip()
                if len(chunk_text) >= min_chunk_chars:
                    chunks.append(TextChunk(
                        text=chunk_text,
                        section_heading=current_heading,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        section_type=page_section_type,
                        practice_area=page_practice_area,
                    ))
                    chunk_index += 1
                accumulator = [para]
                accumulator_chars = len(para)
            else:
                accumulator.append(para)
                accumulator_chars += len(para) + 1

        # Flush remaining accumulator for this page
        if accumulator:
            chunk_text = " ".join(accumulator).strip()
            if len(chunk_text) >= min_chunk_chars:
                chunks.append(TextChunk(
                    text=chunk_text,
                    section_heading=current_heading,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    section_type=page_section_type,
                    practice_area=page_practice_area,
                ))
                chunk_index += 1

    if not chunks:
        for page in pages:
            fallback_chunks = _fallback_page_chunks(page, max_chunk_chars, chunk_index)
            if fallback_chunks:
                chunks.extend(fallback_chunks)
                chunk_index = fallback_chunks[-1].chunk_index + 1

    if not chunks:
        raise ValueError("Chunking failed - no chunks generated")

    logger.info(
        "Chunks created",
        total_pages=len(pages),
        count=len(chunks),
        avg_chunk_chars=round(sum(len(c.text) for c in chunks) / max(1, len(chunks))),
    )

    return chunks

"""
Chunking Service — splits parsed pages into semantically coherent chunks
with configurable size, overlap, and structured metadata tagging
aligned to SeMT Monthly Report format.
"""

from typing import List, Optional
import re

from app.config import settings
from app.services.parsing_service import ParsedPage
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ----------------------------
# Section Detection Utilities
# ----------------------------

def detect_section_type(text: str) -> str:
    """
    Detects high-level section category from SeMT report format.
    """
    text_lower = text.lower()

    if "ongoing digital governance projects" in text_lower:
        return "ongoing_projects"

    if "key documents prepared" in text_lower:
        return "documents_submitted"

    if "major activities performed" in text_lower:
        return "major_activities"

    if "proposed activities" in text_lower:
        return "proposed_activities"

    # fallback
    return "major_activities"


def detect_practice_area(text: str) -> Optional[str]:
    """
    Extracts practice area inside Major Activities section.
    """
    patterns = [
        "digital transformation & strategy",
        "data analytics and business intelligence",
        "emerging technologies",
        "it infra and cyber security",
    ]

    text_lower = text.lower()

    for pattern in patterns:
        if pattern in text_lower:
            return pattern

    return None


# ----------------------------
# Data Structure
# ----------------------------

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


# ----------------------------
# Main Chunking Logic
# ----------------------------

def chunk_pages(pages: List[ParsedPage]) -> List[TextChunk]:
    """
    Takes ParsedPage objects and returns overlapping text chunks.
    Each chunk preserves structured metadata aligned to SeMT format.
    """
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP

    chunks: List[TextChunk] = []
    chunk_index = 0

    for page in pages:
        text = page.text
        if not text or not text.strip():
            continue

        section_type = detect_section_type(text)
        practice_area = detect_practice_area(text)

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Extend to sentence boundary if possible
            if end < len(text):
                boundary_match = re.search(
                    r"[.\n]", text[end - 50:end + 50]
                )
                if boundary_match:
                    boundary_pos = (end - 50) + boundary_match.start()
                    end = boundary_pos + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        section_heading=page.section_heading,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        section_type=section_type,
                        practice_area=practice_area,
                    )
                )
                chunk_index += 1

            start = end - overlap if end < len(text) else len(text)

    logger.info(
        "Chunking complete",
        total_chunks=len(chunks)
    )

    return chunks
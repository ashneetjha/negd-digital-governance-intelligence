"""
Hybrid Analysis Layer — Transform retrieval into actionable insights

Instead of:   retrieve → answer
Now:          retrieve → analyze → compare → explain

Extracts key facts, identifies patterns, and synthesizes governance insights.
"""

import re
from typing import List, Dict, Tuple, Any
from collections import Counter

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# FACT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_key_facts(chunks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract actionable facts from retrieved chunks."""
    facts = {
        "initiatives": [],
        "metrics": [],
        "completed": [],
        "pending": [],
        "risks": [],
    }

    # Patterns
    initiative_pattern = re.compile(
        r"(DigiLocker|UMANG|BharatNet|Aadhaar|e-District|DigiYatra|"
        r"PM Gati Shakti|CCTNS|CERT-In|GIGW|SeMT|STQC)",
        re.IGNORECASE,
    )
    metric_pattern = re.compile(r"\b(\d+(?:%|,\d+)*)\s*(user|transaction|state|district|service)", re.IGNORECASE)
    completed_pattern = re.compile(r"(implemented|deployed|completed|launched|operational)", re.IGNORECASE)
    pending_pattern = re.compile(r"(pending|delayed|in progress|planned|in development)", re.IGNORECASE)
    risk_pattern = re.compile(r"(delay|issue|challenge|gap|bottleneck|risk|low|decline)", re.IGNORECASE)

    text = " ".join(c.get("chunk_text", "") for c in chunks)
    text_lower = text.lower()

    # Extract initiatives
    for match in initiative_pattern.finditer(text):
        initiative = match.group(1)
        if initiative not in facts["initiatives"]:
            facts["initiatives"].append(initiative)

    # Extract metrics
    for match in metric_pattern.finditer(text):
        metric = f"{match.group(1)} {match.group(2)}"
        if metric not in facts["metrics"]:
            facts["metrics"].append(metric)

    # Classify completeness
    if completed_pattern.search(text_lower):
        facts["completed"].append("Completed initiatives detected")
    if pending_pattern.search(text_lower):
        facts["pending"].append("Pending/in-progress initiatives detected")

    # Identify risks
    risk_sentences = []
    for sentence in text.split("."):
        if risk_pattern.search(sentence.lower()) and len(sentence.split()) > 5:
            risk_sentences.append(sentence.strip()[:100])
    facts["risks"] = risk_sentences[:3]

    logger.info(
        "Key facts extracted",
        initiatives=len(facts["initiatives"]),
        metrics=len(facts["metrics"]),
        risks=len(facts["risks"]),
    )

    return facts


# ─────────────────────────────────────────────────────────────────────────────
# COMPARATIVE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def comparative_analysis(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare chunks across states/months to identify patterns."""
    states = Counter(c.get("state") for c in chunks if c.get("state"))
    months = Counter(c.get("reporting_month") for c in chunks if c.get("reporting_month"))
    sections = Counter(c.get("section_type") for c in chunks if c.get("section_type"))

    return {
        "state_coverage": len(states),
        "top_states": [s for s, _ in states.most_common(3)],
        "time_span": sorted([m for m in months.keys() if m], reverse=True)[:3],
        "section_diversity": len(sections),
        "top_sections": [s for s, _ in sections.most_common(3)],
    }


# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT SYNTHESIS
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_insights(
    facts: Dict[str, List[str]],
    analysis: Dict[str, Any],
    answer: str,
) -> str:
    """Convert extracted facts and analysis into synthesized insights."""
    insights = []

    if facts["initiatives"]:
        insights.append(f"Key initiatives identified: {', '.join(facts['initiatives'][:3])}.")

    if facts["completed"]:
        insights.append("Several initiatives are operational and deployed.")

    if facts["pending"]:
        insights.append("Some initiatives are still in development or pending completion.")

    if facts["risks"]:
        insights.append(f"Risk areas noted: {facts['risks'][0][:80]}...")

    if analysis.get("state_coverage", 0) > 1:
        insights.append(
            f"Data spans {analysis['state_coverage']} states, "
            f"showing cross-state variation in implementation."
        )

    if insights:
        insights_text = " ".join(insights)
        return f"{answer}\n\nKey Insights: {insights_text}"
    
    return answer


# ─────────────────────────────────────────────────────────────────────────────
# EXPLAIN CONFIDENCE
# ─────────────────────────────────────────────────────────────────────────────

def build_confidence_explanation(
    confidence: float,
    chunk_count: int,
    avg_similarity: float,
    facts_count: int,
) -> str:
    """Build human-readable confidence justification."""
    parts = []

    # Confidence level
    if confidence >= 0.7:
        parts.append("HIGH confidence")
    elif confidence >= 0.5:
        parts.append("MODERATE confidence")
    else:
        parts.append("LOW confidence")

    # Reasons
    reasons = []
    if chunk_count >= 3:
        reasons.append(f"strong evidence from {chunk_count} sources")
    elif chunk_count > 0:
        reasons.append(f"grounded in {chunk_count} source(s)")
    else:
        reasons.append("very limited evidence")

    if avg_similarity >= 0.6:
        reasons.append("highly relevant matches")
    elif avg_similarity >= 0.4:
        reasons.append("moderately relevant sources")

    if facts_count >= 5:
        reasons.append(f"{facts_count} extracted facts")

    if reasons:
        parts.append(f"based on {', '.join(reasons)}")

    return ". ".join(parts) + "."

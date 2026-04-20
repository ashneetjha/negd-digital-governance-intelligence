"""
Insight Service — Global Intelligence Aggregator

Scans ALL indexed states/reports and produces system-wide insights:
  - Top performing states (by initiative count + section coverage)
  - Low adoption states (fewer indexed data points)
  - Common gaps (rarely mentioned critical schemes)
  - Emerging trends (most-mentioned initiatives across states)

Uses existing DB + retrieval. No heavy computation. No LLM call.
"""

import math
from typing import Dict
from collections import Counter, defaultdict

from app.db.database import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Key schemes/initiatives tracked across all states
_TRACKED_INITIATIVES = [
    "DigiLocker", "UMANG", "BharatNet", "e-District", "DigiYatra",
    "CERT-In", "MyGov", "STQC", "GIGW", "SeMT", "Aadhaar",
    "PM Gati Shakti", "Rapid Assessment System", "CCTNS",
    "GIS", "blockchain", "AI", "cyber", "cloud",
]

# Minimum initiative mentions for "well-performing"
_HIGH_ADOPTION_THRESHOLD = 5
# Below this = low adoption
_LOW_ADOPTION_THRESHOLD = 2


def generate_global_insights() -> Dict:
    """
    Generate system-wide governance intelligence from all indexed data.
    Purely rule-based — no LLM call, no embedding call.
    """
    supabase = get_supabase()

    # ── Step 1: Fetch all distinct states and their report metadata ────────
    try:
        reports_resp = supabase.table("reports").select(
            "id, state, reporting_month, file_name"
        ).execute()
        reports = reports_resp.data or []
    except Exception as exc:
        logger.error("Failed to fetch reports for insights", error=str(exc))
        return _empty_result(str(exc))

    if not reports:
        return _empty_result("No reports indexed in the system.")

    # Group reports by state
    states = sorted({r["state"] for r in reports if r.get("state")})
    reports_by_state = defaultdict(list)
    for r in reports:
        if r.get("state"):
            reports_by_state[r["state"]].append(r)

    # ── Step 2: Fetch chunk text samples per state for initiative scanning ─
    state_signals: Dict[str, dict] = {}

    for st in states:
        try:
            report_ids = [str(r.get("id")) for r in reports_by_state[st] if r.get("id")]
            if report_ids:
                chunk_resp = supabase.table("report_chunks").select(
                    "report_id, chunk_text, section_type, practice_area"
                ).in_("report_id", report_ids).limit(200).execute()
                chunks = chunk_resp.data or []
            else:
                chunks = []
        except Exception:
            chunks = []

        all_text = " ".join(c.get("chunk_text", "") for c in chunks).lower()

        # Count initiative mentions
        initiative_hits = []
        for init in _TRACKED_INITIATIVES:
            if init.lower() in all_text:
                initiative_hits.append(init)

        # Section diversity
        sections = {c.get("section_type") for c in chunks if c.get("section_type")}

        state_signals[st] = {
            "state": st,
            "report_count": len(reports_by_state[st]),
            "chunk_count": len(chunks),
            "initiatives_found": sorted(initiative_hits),
            "initiative_count": len(initiative_hits),
            "section_types": sorted(sections),
            "section_diversity": len(sections),
        }

    # ── Step 3: Compute rankings ──────────────────────────────────────────

    # Score: initiative_count * 2 + section_diversity + log(chunk_count)
    for sig in state_signals.values():
        sig["score"] = round(
            sig["initiative_count"] * 2
            + sig["section_diversity"]
            + math.log(max(sig["chunk_count"], 1)),
            2,
        )

    sorted_states = sorted(
        state_signals.values(), key=lambda x: x["score"], reverse=True
    )

    top_performing = [
        {
            "state": s["state"],
            "score": s["score"],
            "initiatives": s["initiatives_found"],
            "report_count": s["report_count"],
        }
        for s in sorted_states
        if s["initiative_count"] >= _HIGH_ADOPTION_THRESHOLD
    ][:5]

    low_adoption = [
        {
            "state": s["state"],
            "score": s["score"],
            "initiatives": s["initiatives_found"],
            "report_count": s["report_count"],
        }
        for s in sorted_states
        if s["initiative_count"] <= _LOW_ADOPTION_THRESHOLD
    ]

    # ── Step 4: Common gaps ───────────────────────────────────────────────
    # Initiatives that are critical but mentioned by fewer than 30% of states
    initiative_presence = Counter()
    for sig in state_signals.values():
        for init in sig["initiatives_found"]:
            initiative_presence[init] += 1

    gaps_threshold = max(1, len(states) * 0.3)
    common_gaps = [
        {"initiative": init, "states_with": count, "total_states": len(states)}
        for init, count in sorted(initiative_presence.items(), key=lambda x: x[1])
        if count < gaps_threshold and init in [
            "DigiLocker", "UMANG", "e-District", "BharatNet",
            "CERT-In", "CCTNS", "cyber",
        ]
    ]

    # ── Step 5: Emerging trends ───────────────────────────────────────────
    emerging_trends = [
        {"initiative": init, "states_mentioning": count, "coverage_pct": round(count / len(states) * 100, 1)}
        for init, count in initiative_presence.most_common(8)
    ]

    # ── Build result ──────────────────────────────────────────────────────
    result = {
        "total_states": len(states),
        "total_reports": len(reports),
        "states_indexed": states,
        "top_performing_states": top_performing,
        "low_adoption_states": low_adoption,
        "common_gaps": common_gaps,
        "emerging_trends": emerging_trends,
        "status": "ok",
    }

    logger.info(
        "Global insights generated",
        total_states=len(states),
        total_reports=len(reports),
        top_count=len(top_performing),
        low_count=len(low_adoption),
    )

    return result


def _empty_result(reason: str) -> Dict:
    return {
        "total_states": 0,
        "total_reports": 0,
        "states_indexed": [],
        "top_performing_states": [],
        "low_adoption_states": [],
        "common_gaps": [],
        "emerging_trends": [],
        "status": "no_data",
        "message": reason,
    }

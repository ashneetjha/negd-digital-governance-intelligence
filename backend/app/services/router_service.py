"""LLM-powered routing intelligence for query orchestration."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Optional

from groq import Groq

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_ROUTES = {"chat", "rag", "comparison", "cross_state"}
KNOWN_SCHEMES = [
    "DigiLocker",
    "UMANG",
    "BharatNet",
    "Aadhaar",
    "e-District",
    "DigiYatra",
    "PM Gati Shakti",
]


@dataclass
class RouteDecision:
    route: str
    confidence: float
    entities: dict[str, Any]
    rationale: str
    latency_ms: float
    model_used: bool


def _parse_months(text: str) -> list[str]:
    return [m[0] for m in re.findall(r"\b((?:20\d{2})-(?:0[1-9]|1[0-2]))\b", text)]


def _parse_states(text: str) -> list[str]:
    known_states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    ]
    lower = text.lower()
    hits = [s for s in known_states if s.lower() in lower]
    # dedupe while preserving order
    deduped: list[str] = []
    for s in hits:
        if s not in deduped:
            deduped.append(s)
    return deduped


def _parse_scheme(text: str) -> Optional[str]:
    lower = text.lower()
    for scheme in KNOWN_SCHEMES:
        if scheme.lower() in lower:
            return scheme
    return None


def _fallback_route(prompt: str) -> RouteDecision:
    text = prompt.lower()
    states = _parse_states(prompt)
    months = _parse_months(prompt)
    scheme = _parse_scheme(prompt)

    if len(states) >= 2:
        route = "cross_state"
    elif any(w in text for w in ["compare", "comparison", "difference", "versus", "vs"]):
        route = "comparison"
    elif any(w in text for w in ["what is", "explain", "how does", "overview", "definition"]):
        route = "chat"
    else:
        route = "rag"

    return RouteDecision(
        route=route,
        confidence=0.51,
        entities={"states": states, "months": months, "scheme": scheme},
        rationale="Fallback heuristic routing used because LLM classifier unavailable.",
        latency_ms=0.0,
        model_used=False,
    )


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return {}
    return {}


def classify_route(
    prompt: str,
    explicit_state: Optional[str] = None,
    explicit_month: Optional[str] = None,
) -> RouteDecision:
    """Classify route with LLM; falls back safely when uncertain."""
    if not settings.GROQ_API_KEY:
        decision = _fallback_route(prompt)
        if explicit_state and explicit_state not in decision.entities.get("states", []):
            decision.entities.setdefault("states", []).append(explicit_state)
        if explicit_month and explicit_month not in decision.entities.get("months", []):
            decision.entities.setdefault("months", []).append(explicit_month)
        logger.warning("Router fallback used because GROQ_API_KEY is missing")
        return decision

    client = Groq(api_key=settings.GROQ_API_KEY)
    started = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0.0,
            max_tokens=220,
            timeout=8.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify governance assistant query route. "
                        "Return ONLY valid JSON with keys: route, confidence, rationale, entities. "
                        "route must be one of: chat, rag, comparison, cross_state. "
                        "entities must include states (array), months (array YYYY-MM if present), scheme (string or null). "
                        "Use comparison when same-state month comparison intent is present. "
                        "Use cross_state only when two states are present. "
                        "Use rag for report-grounded analysis and factual queries requiring source evidence. "
                        "Use chat for general explanations not requiring report grounding."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Query: {prompt}\n"
                        f"Explicit state: {explicit_state or 'null'}\n"
                        f"Explicit month: {explicit_month or 'null'}"
                    ),
                },
            ],
        )
        payload = _extract_json(response.choices[0].message.content)
        route = payload.get("route", "rag")
        confidence = float(payload.get("confidence", 0.5))
        entities = payload.get("entities") or {}
        rationale = str(payload.get("rationale", "LLM classifier response"))

        if route not in ALLOWED_ROUTES:
            route = "rag"
            confidence = min(confidence, 0.5)
            rationale = "Classifier returned invalid route; forced to rag fallback."

        entities.setdefault("states", _parse_states(prompt))
        entities.setdefault("months", _parse_months(prompt))
        entities.setdefault("scheme", _parse_scheme(prompt))

        if explicit_state and explicit_state not in entities["states"]:
            entities["states"].append(explicit_state)
        if explicit_month and explicit_month not in entities["months"]:
            entities["months"].append(explicit_month)

        # Safety downgrade when uncertain
        if confidence < 0.45:
            route = "rag"
            rationale = "Low classifier confidence; routed to rag fallback."

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        decision = RouteDecision(
            route=route,
            confidence=round(max(0.0, min(confidence, 1.0)), 4),
            entities=entities,
            rationale=rationale,
            latency_ms=latency_ms,
            model_used=True,
        )

        logger.info(
            "Route classified",
            route=decision.route,
            confidence=decision.confidence,
            entities=decision.entities,
            latency_ms=decision.latency_ms,
            rationale=decision.rationale,
        )
        return decision

    except Exception as exc:
        logger.warning("Router classification failed; using fallback", error=str(exc))
        decision = _fallback_route(prompt)
        if explicit_state and explicit_state not in decision.entities.get("states", []):
            decision.entities.setdefault("states", []).append(explicit_state)
        if explicit_month and explicit_month not in decision.entities.get("months", []):
            decision.entities.setdefault("months", []).append(explicit_month)
        decision.rationale = f"Fallback used due to classifier error: {exc}"
        return decision

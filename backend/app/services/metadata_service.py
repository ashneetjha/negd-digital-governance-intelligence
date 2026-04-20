import re
import json
from groq import Groq
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

KNOWN_SCHEMES = [
    "DigiLocker", "UMANG", "BharatNet", "Aadhaar", "e-District",
    "DigiYatra", "PM Gati Shakti", "CCTNS", "CERT-In",
]

def extract_json(text: str) -> dict:
    s = (text or "").strip()
    try:
        return json.loads(s)
    except Exception:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except Exception:
                return {}
    return {}

def extract_query_metadata(prompt: str, client: Groq) -> dict:
    """Extract state/month/scheme metadata from query for filtered retrieval."""
    fallback = {
        "state": None,
        "month": None,
        "scheme": next((s for s in KNOWN_SCHEMES if s.lower() in prompt.lower()), None),
    }

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0.0,
            max_tokens=120,
            timeout=5.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract query metadata as JSON only with keys state, month, scheme. "
                        "month format must be YYYY-MM when present else null."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        data = extract_json(response.choices[0].message.content)
        if data:
            return {
                "state": data.get("state") or fallback["state"],
                "month": data.get("month") or fallback["month"],
                "scheme": data.get("scheme") or fallback["scheme"],
            }
    except Exception as exc:
        logger.warning("Metadata extraction failed; using fallback", error=str(exc))

    # Regex fallback month extraction
    month_match = re.search(r"\b(20\d{2}-(?:0[1-9]|1[0-2]))\b", prompt)
    if month_match:
        fallback["month"] = month_match.group(1)
    return fallback

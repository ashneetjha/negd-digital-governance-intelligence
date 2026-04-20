import hashlib
import time
from typing import Dict, Any, Optional

_CACHE: Dict[str, Any] = {}
_CACHE_TTL = 300

def get_cache_key(prompt: str, state: Optional[str], month: Optional[str], section: Optional[str]) -> str:
    raw = f"{prompt}|{state}|{month}|{section}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_from_cache(key: str) -> Optional[Any]:
    item = _CACHE.get(key)
    if not item:
        return None
    if time.time() - item["timestamp"] > _CACHE_TTL:
        return None
    return item["value"]

def set_in_cache(key: str, value: Any) -> None:
    _CACHE[key] = {"value": value, "timestamp": time.time()}

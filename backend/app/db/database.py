"""
Supabase client initialisation.
Provides a singleton client instance used across all services.
"""
from supabase import create_client, Client
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    """Return the singleton Supabase client, initialising it on first call."""
    global _client

    if _client is not None:
        return _client

    url = (settings.SUPABASE_URL or "").strip()
    key = (settings.SUPABASE_KEY or "").strip()

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set correctly in environment variables."
        )

    try:
        _client = create_client(url, key)
        logger.info(
            "Supabase client initialised",
            url_preview=url[:40] + "…",
            key_type="service_role" if "service_role" in key else "anon/public",
        )
        return _client

    except Exception as exc:
        logger.error("Failed to initialise Supabase client", error=str(exc))
        raise
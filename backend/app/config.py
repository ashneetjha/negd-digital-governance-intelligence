"""
Centralised application configuration using Pydantic Settings.
Loads values from environment variables and optionally a .env file.

Embedding model: sentence-transformers/paraphrase-MiniLM-L3-v2 via HF Inference API (384-dim).
STRICT_REAL_AI=true enforces no pseudo-embedding fallback.
"""

from functools import lru_cache
from pathlib import Path
from typing import ClassVar, List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root = negd-digital-governance-intelligence/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Add production frontend URL here when deploying
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Groq (Open model inference)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Strict mode for production-grade behavior
    STRICT_REAL_AI: bool = True

    # ── Embeddings ────────────────────────────────────────────────────────────
    # Model label used in logs/status. No local model is loaded in production.
    EMBEDDING_MODEL: ClassVar[str] = "sentence-transformers/paraphrase-MiniLM-L3-v2"
    HF_API_BASE: str = "https://api-inference.huggingface.co/models"
    EMBEDDING_DIMENSION: int = 384  # paraphrase-MiniLM-L3-v2 produces 384-dim vectors

    # HuggingFace Inference API token — REQUIRED in production (STRICT_REAL_AI=true).
    # No local model fallback; no pseudo-embedding fallback.
    HF_API_TOKEN: str = ""

    # ── RAG ───────────────────────────────────────────────────────────────────
    RAG_TOP_K: int = 12   # Hard cap — retrieval never exceeds 12 chunks
    CHUNK_SIZE: int = 1600  # ~400 token equivalents (4 chars/token estimate)
    CHUNK_OVERLAP: int = 0   # Paragraph chunker uses natural boundaries, no overlap needed

    # ── Uploads ───────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = str(BASE_DIR / "tmp_uploads")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        """
        Be tolerant of common env values such as "release"/"prod"
        to avoid startup failures from global process env collisions.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            truthy = {"1", "true", "yes", "y", "on", "dev", "development"}
            falsy = {"0", "false", "no", "n", "off", "release", "prod", "production"}
            if normalized in truthy:
                return True
            if normalized in falsy:
                return False
        return bool(value)

    @model_validator(mode="after")
    def validate_required_envs(self) -> 'Settings':
        missing = []
        if not self.SUPABASE_URL: missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY: missing.append("SUPABASE_KEY")
        if not self.GROQ_API_KEY: missing.append("GROQ_API_KEY")
        if not self.HF_API_TOKEN: missing.append("HF_API_TOKEN")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return self

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

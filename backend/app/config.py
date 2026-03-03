"""
Centralised application configuration using Pydantic Settings.
Loads values from environment variables and optionally a .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root = negd-digital-governance-intelligence/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
    ]

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Groq (Open model inference)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Strict mode for production-grade behavior
    STRICT_REAL_AI: bool = True

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ── RAG ───────────────────────────────────────────────────────────────────
    RAG_TOP_K: int = 8
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

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

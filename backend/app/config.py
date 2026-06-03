"""GuardianHealth v2 — Pydantic application settings.

All configuration is loaded from environment variables (12-factor style).
The SECRET_KEY MUST be provided at runtime; the application will refuse
to start without a key of at least 32 characters.
"""

import os
import secrets
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with strict validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # App identity
    # ------------------------------------------------------------------
    app_name: str = "GuardianHealth v2"
    app_version: str = "2.0.0"
    debug: bool = False
    guardian_env: str = "production"  # "development", "staging", "production"

    # ------------------------------------------------------------------
    # Security — SECRET_KEY is REQUIRED (no default)
    # ------------------------------------------------------------------
    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ------------------------------------------------------------------
    # AWS / DynamoDB
    # ------------------------------------------------------------------
    aws_region: str = "us-east-1"
    dynamodb_table_prefix: str = "guardian"
    dynamodb_endpoint_url: Optional[str] = None  # e.g. http://localhost:8000 for local

    # ------------------------------------------------------------------
    # Together AI (LLM)
    # ------------------------------------------------------------------
    together_api_key: Optional[str] = None
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    together_base_url: str = "https://api.together.xyz/v1"

    # ------------------------------------------------------------------
    # NCBI / PubMed
    # ------------------------------------------------------------------
    ncbi_email: Optional[str] = None
    ncbi_api_key: Optional[str] = None

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    allowed_origins: List[str] = ["http://localhost:5173"]

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------
    mock_mode: bool = False  # If True, skip external LLM calls (testing)

    # ------------------------------------------------------------------
    # Rate limits (requests per minute)
    # ------------------------------------------------------------------
    rate_limit_health: str = "100/minute"
    rate_limit_register: str = "5/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_refresh: str = "20/minute"
    rate_limit_chat: str = "60/minute"
    rate_limit_triage: str = "10/minute"

    # ------------------------------------------------------------------
    # Redis / Celery (optional — disabled by default for zero-cost mode)
    # ------------------------------------------------------------------
    redis_url: Optional[str] = None
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # ------------------------------------------------------------------
    # ML model path (optional sklearn model)
    # ------------------------------------------------------------------
    ml_model_path: Optional[str] = None

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                f"Got length={len(v) if v else 0}. "
                f'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return v.strip()

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------

    @property
    def table_users(self) -> str:
        return f"{self.dynamodb_table_prefix}_users"

    @property
    def table_chats(self) -> str:
        return f"{self.dynamodb_table_prefix}_chats"

    @property
    def table_interactions(self) -> str:
        return f"{self.dynamodb_table_prefix}_interactions"

    @property
    def is_development(self) -> bool:
        return self.guardian_env == "development"


# ------------------------------------------------------------------------------
# Singleton factory
# ------------------------------------------------------------------------------

@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()


# ------------------------------------------------------------------------------
# Startup validation
# ------------------------------------------------------------------------------

def validate_startup() -> None:
    """Eagerly validate critical configuration at application startup.

    Raises:
        SystemExit: If SECRET_KEY is missing or too short.
    """
    settings = get_settings()

    # Pydantic already validated length, but double-check explicitly
    # so the error message is crystal-clear in startup logs.
    if not settings.secret_key or len(settings.secret_key) < 32:
        print(
            "\n[GUARDIAN FATAL] SECRET_KEY is missing or shorter than 32 characters.\n"
            "The application cannot start with an insecure signing key.\n\n"
            "Generate a secure key:\n"
            '  export SECRET_KEY="' + secrets.token_hex(32) + '"\n\n'
            "Or add it to your .env file:\n"
            "  SECRET_KEY=<your-64-char-hex-key>\n",
            flush=True,
        )
        raise SystemExit(1)

    # Warn if running mock mode in production-like environments
    if settings.mock_mode and not settings.is_development:
        print(
            "\n[GUARDIAN WARNING] MOCK_MODE is enabled in a non-development environment.\n"
            "External LLM calls will be skipped. This is NOT suitable for production.\n",
            flush=True,
        )

    # Validate Together AI credentials unless in mock mode
    if not settings.mock_mode and not settings.together_api_key:
        print(
            "\n[GUARDIAN WARNING] TOGETHER_API_KEY is not set. "
            "LLM-based triage will fail at runtime.\n",
            flush=True,
        )

"""GuardianHealth — Pydantic application settings."""

import secrets
from functools import lru_cache
from typing import List, Optional

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.paths import resolve_env_file

_ENV_FILE = resolve_env_file()


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "GuardianHealth"
    app_version: str = "2.0.0"
    debug: bool = False
    guardian_env: str = "production"

    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "guardian"

    upstash_redis_rest_url: Optional[str] = None
    upstash_redis_rest_token: Optional[str] = None
    upstash_redis_url: Optional[str] = None
    cache_ttl_seconds: int = 3600

    together_api_key: Optional[str] = None
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    together_base_url: str = "https://api.together.xyz/v1"

    allowed_origins: Annotated[List[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://kartik-soni18.github.io",
    ]
    api_gateway_stage: str = "prod"
    mock_mode: bool = False

    rate_limit_health: str = "100/minute"
    rate_limit_register: str = "5/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_refresh: str = "20/minute"
    rate_limit_triage: str = "10/minute"

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                f"Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v.strip()

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, v):
        if v is None or v == "":
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "https://kartik-soni18.github.io",
            ]
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_development(self) -> bool:
        return self.guardian_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_startup() -> None:
    settings = get_settings()
    if not settings.secret_key or len(settings.secret_key) < 32:
        print(
            "\n[GUARDIAN FATAL] SECRET_KEY is missing or shorter than 32 characters.\n"
            f'  export SECRET_KEY="{secrets.token_hex(32)}"\n',
            flush=True,
        )
        raise SystemExit(1)

    if settings.mock_mode and not settings.is_development:
        print(
            "\n[GUARDIAN WARNING] MOCK_MODE is enabled in a non-development environment.\n",
            flush=True,
        )

    if not settings.mock_mode and not settings.together_api_key:
        print(
            "\n[GUARDIAN WARNING] TOGETHER_API_KEY is not set. "
            "LLM triage will fail at runtime unless MOCK_MODE=true.\n",
            flush=True,
        )

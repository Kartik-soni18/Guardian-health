"""Pydantic BaseSettings for centralized, validated configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """GuardianHealth application settings loaded from environment variables."""

    # Application
    guardian_env: str = Field(default="production", alias="GUARDIAN_ENV")
    secret_key: str = Field(default="guardian-health-super-secret-key-donot-share", alias="SECRET_KEY")

    # MongoDB
    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_db: str = Field(default="guardian_health", alias="MONGODB_DB")

    # LLM (Together.ai)
    together_api_key: str | None = Field(default=None, alias="TOGETHER_API_KEY")
    together_model: str = Field(
        default="meta-llama/Llama-3.3-70B-Instruct-Turbo", alias="TOGETHER_MODEL"
    )

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://localhost:8080",
        alias="ALLOWED_ORIGINS",
    )

    # PubMed / NCBI
    ncbi_email: str = Field(default="guardian-health@example.com", alias="NCBI_EMAIL")

    # LM Studio (local summarisation fallback)
    lm_studio_url: str = Field(default="http://localhost:1234", alias="LM_STUDIO_URL")
    lm_studio_model: str = Field(
        default="QuantFactory/Bio-Medical-Llama-3-8B-GGUF", alias="LM_STUDIO_MODEL"
    )

    # ChromaDB
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8000, alias="CHROMA_PORT")

    # Mock mode (test only)
    mock_mode: bool = Field(default=False, alias="MOCK_MODE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_development(self) -> bool:
        return self.guardian_env.lower() in ("development", "dev", "test", "testing")

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        # Ensure frontend origin is always present
        if "https://kartik-soni18.github.io" not in origins:
            origins.append("https://kartik-soni18.github.io")
        return origins


# Global singleton — imported by services, deps, and legacy modules
settings = Settings()

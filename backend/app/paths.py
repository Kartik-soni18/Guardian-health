"""Repository path helpers."""

from pathlib import Path

# backend/app/paths.py -> repo root is two levels up from backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
ROOT_ENV_FILE = PROJECT_ROOT / ".env"


def resolve_env_file() -> str | None:
    """Return the central repo-root .env path when it exists."""
    if ROOT_ENV_FILE.is_file():
        return str(ROOT_ENV_FILE)
    return None

"""Re-export settings from app.config for backward compatibility."""

from app.config import Settings, get_settings, validate_startup

settings = get_settings()

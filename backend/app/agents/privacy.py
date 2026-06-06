"""Privacy agent — re-exports core PII scrubbing."""

from app.core.privacy import scrub_pii

__all__ = ["scrub_pii"]

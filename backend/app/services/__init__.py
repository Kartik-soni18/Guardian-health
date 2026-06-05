"""Business logic services."""

__all__ = ["AuthService", "TriageService"]


def __getattr__(name: str):
    if name == "AuthService":
        from app.services.auth_service import AuthService
        return AuthService
    if name == "TriageService":
        from app.services.triage_service import TriageService
        return TriageService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

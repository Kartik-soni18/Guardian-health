"""GuardianHealth custom exception hierarchy.

All exceptions map to an appropriate HTTP status code and carry a
machine-readable error_code + human-readable detail for consistent
API error responses.
"""


from http import HTTPStatus
from typing import Any, Dict, Optional


class GuardianException(Exception):
    """Base exception for all GuardianHealth domain errors.

    Attributes:
        status_code: HTTP status code to return.
        error_code: Machine-readable snake_case identifier.
        detail: Human-readable explanation.
        headers: Optional HTTP headers (e.g., WWW-Authenticate for 401).
        extra: Arbitrary key-value pairs for structured logging.
    """

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"

    def __init__(
        self,
        detail: str = "An unexpected error occurred.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.detail = detail
        self.headers = headers or {}
        self.extra = extra or {}
        super().__init__(self.detail)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-friendly dict for API responses."""
        payload: Dict[str, Any] = {
            "error_code": self.error_code,
            "detail": self.detail,
        }
        if self.extra:
            payload["extra"] = self.extra
        return payload


# ------------------------------------------------------------------------------
# Client / 4xx errors
# ------------------------------------------------------------------------------

class AuthenticationError(GuardianException):
    """Missing, expired, or invalid authentication credentials."""

    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "authentication_error"

    def __init__(
        self,
        detail: str = "Authentication required.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        default_headers = {"WWW-Authenticate": "Bearer"}
        if headers:
            default_headers.update(headers)
        super().__init__(detail, headers=default_headers, extra=extra)


class AuthorizationError(GuardianException):
    """Authenticated user lacks permission for the requested resource."""

    status_code = HTTPStatus.FORBIDDEN
    error_code = "authorization_error"

    def __init__(
        self,
        detail: str = "Insufficient permissions.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)


class ValidationError(GuardianException):
    """Request payload failed business-rule or schema validation."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "validation_error"

    def __init__(
        self,
        detail: str = "Request validation failed.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)


class RateLimitError(GuardianException):
    """Client has exceeded the allowed request rate."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "rate_limit_exceeded"

    def __init__(
        self,
        detail: str = "Rate limit exceeded. Please slow down.",
        *,
        retry_after: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        hdrs = headers or {}
        if retry_after is not None:
            hdrs["Retry-After"] = str(retry_after)
        super().__init__(detail, headers=hdrs, extra=extra)


class NotFoundError(GuardianException):
    """Requested resource does not exist."""

    status_code = HTTPStatus.NOT_FOUND
    error_code = "not_found"

    def __init__(
        self,
        detail: str = "Resource not found.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)


class ConflictError(GuardianException):
    """Request conflicts with current state (e.g., duplicate username)."""

    status_code = HTTPStatus.CONFLICT
    error_code = "conflict"

    def __init__(
        self,
        detail: str = "Resource conflict.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)


# ------------------------------------------------------------------------------
# Server / 5xx errors
# ------------------------------------------------------------------------------

class LLMError(GuardianException):
    """External LLM provider (Together AI) returned an error or timed out."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "llm_unavailable"

    def __init__(
        self,
        detail: str = "The triage engine is temporarily unavailable.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)


class DatabaseError(GuardianException):
    """DynamoDB operation failed unexpectedly."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "database_error"

    def __init__(
        self,
        detail: str = "Database operation failed.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)


class ComplianceError(GuardianException):
    """Operation blocked by safety, privacy, or regulatory guardrails.

    This is returned as 500 because it indicates a server-side
    guardrail violation that should not normally be triggered by
    benign client input.
    """

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "compliance_violation"

    def __init__(
        self,
        detail: str = "Operation blocked by compliance guardrails.",
        *,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail, headers=headers, extra=extra)
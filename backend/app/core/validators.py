"""Input validation utilities for GuardianHealth.

All functions are pure, side-effect free, and raise ValidationError on failure.
They are used both in Pydantic validators (model layer) and in manual checks
(service layer).
"""


import re

from app.core.exceptions import ValidationError

# ------------------------------------------------------------------------------
# Regex patterns (compiled once)
# ------------------------------------------------------------------------------

_RE_USERNAME = re.compile(r"^[a-zA-Z0-9_]+$")
_RE_EMAIL = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)
_RE_PASSWORD_UPPER = re.compile(r"[A-Z]")
_RE_PASSWORD_LOWER = re.compile(r"[a-z]")
_RE_PASSWORD_DIGIT = re.compile(r"[0-9]")
_RE_PASSWORD_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~ ]")


# ------------------------------------------------------------------------------
# Username
# ------------------------------------------------------------------------------

def validate_username(username: str) -> str:
    """Validate username format.

    Rules:
        - 3 to 50 characters
        - Alphanumeric and underscore only
        - Must not start or end with underscore

    Raises:
        ValidationError: If any rule is violated.
    """
    if not username:
        raise ValidationError("Username is required.", extra={"field": "username"})

    if len(username) < 3 or len(username) > 50:
        raise ValidationError(
            "Username must be between 3 and 50 characters.",
            extra={"field": "username", "received_length": len(username)},
        )

    if username.startswith("_") or username.endswith("_"):
        raise ValidationError(
            "Username must not start or end with an underscore.",
            extra={"field": "username"},
        )

    if not _RE_USERNAME.match(username):
        raise ValidationError(
            "Username may only contain letters, numbers, and underscores.",
            extra={"field": "username"},
        )

    return username


# ------------------------------------------------------------------------------
# Email
# ------------------------------------------------------------------------------

def validate_email(email: str) -> str:
    """Validate email address format.

    Uses a practical RFC 5322 subset regex. Does NOT verify deliverability.

    Raises:
        ValidationError: If format is invalid.
    """
    if not email:
        raise ValidationError("Email is required.", extra={"field": "email"})

    if len(email) > 254:
        raise ValidationError(
            "Email address is too long (max 254 characters).",
            extra={"field": "email"},
        )

    if not _RE_EMAIL.match(email):
        raise ValidationError(
            "Invalid email address format.",
            extra={"field": "email"},
        )

    return email.lower()


# ------------------------------------------------------------------------------
# Password
# ------------------------------------------------------------------------------

def validate_password(password: str) -> str:
    """Validate password strength.

    Rules:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character (!@#$%^&* etc.)

    Raises:
        ValidationError: If any rule is violated.
    """
    if not password:
        raise ValidationError("Password is required.", extra={"field": "password"})

    if len(password) < 8:
        raise ValidationError(
            "Password must be at least 8 characters long.",
            extra={"field": "password", "received_length": len(password)},
        )

    errors: list[str] = []

    if not _RE_PASSWORD_UPPER.search(password):
        errors.append("At least one uppercase letter (A-Z) is required.")

    if not _RE_PASSWORD_LOWER.search(password):
        errors.append("At least one lowercase letter (a-z) is required.")

    if not _RE_PASSWORD_DIGIT.search(password):
        errors.append("At least one digit (0-9) is required.")

    if not _RE_PASSWORD_SPECIAL.search(password):
        errors.append(
            "At least one special character is required (!@#$%^&* etc.)."
        )

    if errors:
        raise ValidationError(
            "Password does not meet complexity requirements.",
            extra={"field": "password", "errors": errors},
        )

    return password


# ------------------------------------------------------------------------------
# Query / free-text
# ------------------------------------------------------------------------------

def validate_query_text(text: str, *, min_length: int = 3, max_length: int = 2000) -> str:
    """Validate a free-text query (symptom description, etc.).

    Raises:
        ValidationError: If text is too short or too long.
    """
    if not text or len(text.strip()) < min_length:
        raise ValidationError(
            f"Query must be at least {min_length} characters long.",
            extra={"field": "query", "received_length": len(text.strip()) if text else 0},
        )

    if len(text) > max_length:
        raise ValidationError(
            f"Query must not exceed {max_length} characters.",
            extra={"field": "query", "received_length": len(text)},
        )

    return text.strip()
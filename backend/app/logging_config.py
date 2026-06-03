"""Structured JSON logging for GuardianHealth.

Every log record includes a request_id correlated via an async-safe ContextVar.
Third-party libraries have their log levels reduced to keep output readable.
"""


import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

# ------------------------------------------------------------------------------
# Request ID context
# ------------------------------------------------------------------------------

_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_request_id(request_id: str | None) -> None:
    """Set the current request ID in the async context."""
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get the current request ID from the async context."""
    return _request_id_var.get()


def generate_request_id() -> str:
    """Generate a new short request ID."""
    return uuid.uuid4().hex[:16]


# ------------------------------------------------------------------------------
# JSON formatter
# ------------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "lvl": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Inject request_id if present
        req_id = get_request_id()
        if req_id:
            payload["request_id"] = req_id

        # Add exception info
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_type"] = record.exc_info[0].__name__
            payload["exc_msg"] = str(record.exc_info[1])

        # Add any extra fields set on the record
        for key in ("error_code", "user", "chat_id", "triage_level", "extra"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        return json.dumps(payload, default=str, ensure_ascii=False)


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

_LOG_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": _JsonFormatter,
        },
        "simple": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json",
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "json",
            "level": "WARNING",
        },
    },
    "loggers": {
        # Guardian app loggers
        "app": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        "app.api": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        "app.core": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        "app.dynamodb": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        # Third-party noise reduction
        "boto3": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "botocore": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "aiobotocore": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "urllib3": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "httpx": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "httpcore": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "slowapi": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
        "passlib": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
    },
    "root": {
        "handlers": ["stdout"],
        "level": "INFO",
    },
}


def configure_logging(debug: bool = False) -> None:
    """Apply the logging configuration globally.

    Args:
        debug: If True, switch to simple text format and lower levels.
    """
    config = _LOG_CONFIG.copy()
    if debug:
        config["handlers"]["stdout"]["formatter"] = "simple"
        config["handlers"]["stderr"]["formatter"] = "simple"
        config["loggers"]["app"]["level"] = "DEBUG"
        config["loggers"]["app.api"]["level"] = "DEBUG"
        config["loggers"]["app.core"]["level"] = "DEBUG"

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a GuardianHealth logger with the given dotted name.

    Usage:
        logger = get_logger("app.api.triage")
        logger.info("Triage complete", extra={"triage_level": "urgent"})
    """
    return logging.getLogger(name)
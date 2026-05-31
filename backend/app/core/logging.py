"""Structured JSON logging with request ID correlation."""

import json
import logging
import sys
import uuid
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for CloudWatch / ELK ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Pull in extra fields commonly attached by middleware
        for key in ("request_id", "user_id", "chat_id", "path", "method", "latency_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str | int = logging.INFO) -> None:
    """Attach the JSON formatter to the root logger."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplication on reload
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance. Prefer this over logging.getLogger() directly."""
    return logging.getLogger(name)

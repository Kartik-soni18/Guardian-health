"""
GuardianHealth v2 - OpenTelemetry Instrumentation

Provides distributed tracing with optional OpenTelemetry support.
If the opentelemetry packages are not installed, tracing falls back
gracefully to no-op spans to avoid import-time failures.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from app.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Graceful import handling
# ---------------------------------------------------------------------------

_OTEL_AVAILABLE = False
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    _OTEL_AVAILABLE = True
except ImportError:
    trace = None  # type: ignore[assignment]
    TracerProvider = None  # type: ignore[assignment,misc]
    BatchSpanProcessor = None  # type: ignore[assignment,misc]
    ConsoleSpanExporter = None  # type: ignore[assignment,misc]
    Resource = None  # type: ignore[assignment,misc]
    SERVICE_NAME = "service.name"  # type: ignore[assignment]


def setup_telemetry(service_name: str = "guardian-health") -> None:
    """
    Configure OpenTelemetry tracing if available.

    In production, set OTEL_EXPORTER_OTLP_ENDPOINT to send spans to
    a collector (Jaeger, Tempo, etc.). In development, spans are printed
    to stdout if OTEL_DEBUG=1 is set.

    Args:
        service_name: The service name tag attached to all traces.
    """
    if not _OTEL_AVAILABLE:
        logger.info(
            "OpenTelemetry not installed; tracing is disabled. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx"
        )
        return

    if TracerProvider is None:
        return

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    # Console exporter for development
    if os.getenv("OTEL_DEBUG") == "1":
        if ConsoleSpanExporter is not None:
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            logger.info("OpenTelemetry console exporter enabled")

    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry tracer configured for service=%s", service_name)


def get_tracer(name: str = "guardian-health"):
    """
    Return a tracer instance for creating custom spans.

    Falls back to a no-op tracer if OpenTelemetry is not available.
    """
    if not _OTEL_AVAILABLE or trace is None:
        # Return a dummy tracer that does nothing
        class _NoOpTracer:
            def start_as_current_span(self, *args, **kwargs):
                class _NoOpSpan:
                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        return False

                    def set_attribute(self, *args, **kwargs):
                        pass

                    def record_exception(self, *args, **kwargs):
                        pass

                return _NoOpSpan()

        return _NoOpTracer()

    return trace.get_tracer(name)


# ---------------------------------------------------------------------------
# FastAPI instrumentation
# ---------------------------------------------------------------------------


def instrument_fastapi(app) -> None:
    """
    Instrument a FastAPI application with OpenTelemetry.

    Args:
        app: The FastAPI application instance.
    """
    if not _OTEL_AVAILABLE:
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OpenTelemetry instrumentation enabled")
    except ImportError:
        logger.debug(
            "opentelemetry-instrumentation-fastapi not installed; skipping"
        )


# ---------------------------------------------------------------------------
# HTTPX instrumentation
# ---------------------------------------------------------------------------


def instrument_httpx() -> None:
    """Instrument httpx AsyncClient with OpenTelemetry."""
    if not _OTEL_AVAILABLE:
        return

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX OpenTelemetry instrumentation enabled")
    except ImportError:
        logger.debug(
            "opentelemetry-instrumentation-httpx not installed; skipping"
        )

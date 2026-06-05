"""Context variable for SSE emit callbacks during graph streaming."""

from __future__ import annotations

import contextvars
from collections.abc import Awaitable, Callable
from typing import Any

StreamEmit = Callable[[dict[str, Any]], Awaitable[None] | None]

_stream_emit: contextvars.ContextVar[StreamEmit | None] = contextvars.ContextVar(
    "stream_emit",
    default=None,
)


def get_stream_emit() -> StreamEmit | None:
    return _stream_emit.get()


def set_stream_emit(emit: StreamEmit | None) -> contextvars.Token[StreamEmit | None]:
    return _stream_emit.set(emit)


def reset_stream_emit(token: contextvars.Token[StreamEmit | None]) -> None:
    _stream_emit.reset(token)

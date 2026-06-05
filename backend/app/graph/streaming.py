"""SSE helpers and graph node status messages for triage streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from app.graph.stream_context import StreamEmit

NODE_STATUS_MESSAGES: dict[str, str] = {
    "input_gate": "Validating your message...",
    "firewall": "Checking medical relevance...",
    "privacy": "Protecting your privacy...",
    "extractor": "Analyzing symptoms...",
    "dataset_lookup": "Searching medical reference data...",
    "reasoner": "Running clinical reasoning...",
    "consultation": "Generating assessment...",
    "triage": "Classifying triage level...",
    "disease_info": "Retrieving health information...",
    "emergency": "Preparing emergency guidance...",
    "compliance": "Reviewing safety compliance...",
    "assembler": "Assembling your response...",
    "persist": "Finalizing...",
}

CHUNK_SIZE = 40
CHUNK_DELAY_SECONDS = 0.02


def format_sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


async def emit_text_chunks(emit: StreamEmit, text: str) -> None:
    """Send user-visible text in small chunks for a typing effect."""
    if not text:
        return
    for index in range(0, len(text), CHUNK_SIZE):
        chunk = text[index : index + CHUNK_SIZE]
        result = emit({"type": "token", "chunk": chunk})
        if asyncio.iscoroutine(result):
            await result
        await asyncio.sleep(CHUNK_DELAY_SECONDS)


async def chunk_text(text: str) -> AsyncIterator[str]:
    """Yield text in fixed-size chunks with a short delay."""
    for index in range(0, len(text), CHUNK_SIZE):
        yield text[index : index + CHUNK_SIZE]
        await asyncio.sleep(CHUNK_DELAY_SECONDS)

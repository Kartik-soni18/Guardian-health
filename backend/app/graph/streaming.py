"""SSE helpers and graph node status messages for triage streaming."""

from __future__ import annotations

import json
from typing import Any

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


def format_sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"

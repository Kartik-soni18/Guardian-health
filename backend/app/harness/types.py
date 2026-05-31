"""Shared types for the agent harness and LangGraph state."""

from typing import TypedDict, Any


class AgentInput(TypedDict, total=False):
    """Standardized input every agent receives."""
    user_query: str
    scrubbed_query: str
    conversation_history: list[dict]
    context: dict[str, Any]


class AgentOutput(TypedDict, total=False):
    """Standardized output every agent produces."""
    success: bool
    data: dict[str, Any]
    error: str | None
    latency_ms: int


class AgentState(TypedDict, total=False):
    """Base state dict used by the harness.

    The LangGraph TriageState in app/graph/state.py extends this
    with triage-specific fields.
    """
    user_input: str
    scrubbed_input: str | None
    symptoms: list[str]
    duration: str | None
    severity: str | None
    search_terms: list[str]
    ml_prediction: dict | None
    ml_confidence: float
    emergency_detected: bool
    consultation_needed: bool
    force_phrase_used: bool
    triage_result: dict | None
    final_response: str | None
    compliance_passed: bool
    rejection_reason: str | None
    chat_history: list[dict]
    pii_detected: bool
    privacy_block: dict | None
    supervisor_notes: dict | None
    conversation_history: list[dict]
    status: str

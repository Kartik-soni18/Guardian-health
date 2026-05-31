"""TriageState definition for the LangGraph state machine."""

from typing import TypedDict


class TriageState(TypedDict, total=False):
    """Shared state that flows through the triage graph.

    Every node receives the full state and returns a partial dict of updates.
    """

    # ── Input metadata ───────────────────────────────────────────────────────
    user_input: str
    user: dict | None
    chat_id: str | None
    conversation_history: list[dict]

    # ── Pre-processing ───────────────────────────────────────────────────────
    force_phrase_used: bool
    scrubbed_input: str | None
    pii_detected: bool
    privacy_block: dict | None

    # ── Firewall ─────────────────────────────────────────────────────────────
    rejection_reason: str | None

    # ── Extraction ───────────────────────────────────────────────────────────
    symptoms: list[str]
    duration: str | None
    severity: str | None
    search_terms: list[str]

    # ── ML prediction ────────────────────────────────────────────────────────
    ml_prediction: dict | None
    ml_confidence: float

    # ── Supervisor reasoning ─────────────────────────────────────────────────
    scratchpad: str | None
    ml_reasoning: str | None
    discrepancy_note: str | None
    emergency_detected: bool
    final_routing: str | None  # "diagnosed" | "consultation" | "emergency"

    # ── Consultation ─────────────────────────────────────────────────────────
    consultation_needed: bool
    consultation_result: dict | None

    # ── Triage / Disease info ────────────────────────────────────────────────
    triage_result: dict | None
    disease_info: dict | None

    # ── Compliance ───────────────────────────────────────────────────────────
    compliance_passed: bool
    compliance_note: str | None

    # ── Final output ─────────────────────────────────────────────────────────
    response_data: dict | None
    status: str | None
    error: str | None

    # ── Internal tracing ─────────────────────────────────────────────────────
    _last_agent: str | None
    _last_latency_ms: int | None
    _error: str | None

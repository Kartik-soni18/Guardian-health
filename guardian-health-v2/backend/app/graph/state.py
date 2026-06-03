"""
TriageState — TypedDict defining the complete state schema for the triage graph.

Uses total=False so nodes can partially update state without requiring all fields.
"""


from typing import Any, NotRequired, TypedDict


class TriageState(TypedDict, total=False):
    """Complete state for the GuardianHealth triage pipeline."""

    # ------------------------------------------------------------------
    # Input fields (set at graph entry)
    # ------------------------------------------------------------------
    user_input: str
    user_id: str | None
    chat_id: str | None
    conversation_history: list[dict[str, Any]]
    force_phrase_used: bool

    # ------------------------------------------------------------------
    # Pre-processing fields
    # ------------------------------------------------------------------
    scrubbed_input: str | None
    pii_detected: bool
    pii_entities: list[dict[str, Any]] | None

    # ------------------------------------------------------------------
    # Firewall fields
    # ------------------------------------------------------------------
    is_medical: bool | None
    is_emergency: bool
    rejection_reason: str | None
    rejection_category: str | None

    # ------------------------------------------------------------------
    # Extraction fields
    # ------------------------------------------------------------------
    symptoms: list[str]
    duration: str | None
    severity: str | None
    search_terms: list[str]
    demographics: dict[str, Any] | None
    medications: list[str] | None
    extra_context: str | None

    # ------------------------------------------------------------------
    # ML prediction fields
    # ------------------------------------------------------------------
    ml_prediction: dict[str, Any] | None
    ml_confidence: float
    top_predictions: list[dict[str, Any]]

    # ------------------------------------------------------------------
    # Reasoning fields
    # ------------------------------------------------------------------
    scratchpad: dict[str, Any] | None
    ml_reasoning: str | None
    discrepancy_note: str | None
    reasoning_confidence: float

    # ------------------------------------------------------------------
    # PubMed / literature fields
    # ------------------------------------------------------------------
    pubmed_results: dict[str, Any] | None

    # ------------------------------------------------------------------
    # Routing & processing results
    # ------------------------------------------------------------------
    emergency_detected: bool
    final_routing: str | None  # "consultation" | "triage" | "disease_info" | "emergency"

    # ------------------------------------------------------------------
    # Node outputs
    # ------------------------------------------------------------------
    consultation_result: dict[str, Any] | None
    triage_result: dict[str, Any] | None
    disease_info: dict[str, Any] | None

    # ------------------------------------------------------------------
    # Compliance fields
    # ------------------------------------------------------------------
    compliance_passed: bool
    compliance_note: str | None
    compliance_violations: list[str] | None

    # ------------------------------------------------------------------
    # Response & persistence
    # ------------------------------------------------------------------
    response_data: dict[str, Any] | None
    audit_hash: str | None

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
    error: str | None

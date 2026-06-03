"""Pydantic models for the AI triage engine.

These DTOs define the contract between the API layer, the LLM service,
and the evidence-retrieval (PubMed) layer.
"""


from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import RoutingDecision, TriageLevel


# ------------------------------------------------------------------------------
# Request
# ------------------------------------------------------------------------------


class TriageRequest(BaseModel):
    """Patient-submitted symptom query for AI triage.

    conversation_history allows multi-turn context to be passed so the
    LLM can reference prior exchanges.
    """

    query: str = Field(..., min_length=3, max_length=2000)
    chat_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    include_evidence: bool = True  # Whether to fetch PubMed abstracts

    @field_validator("query")
    @classmethod
    def _normalize_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query must be at least 3 characters after trimming.")
        return v


# ------------------------------------------------------------------------------
# Internal clinical extraction
# ------------------------------------------------------------------------------


class ClinicalEntities(BaseModel):
    """Structured entities extracted from the patient's natural language query.

    This is produced by the NER / entity extraction step before the LLM
    performs differential diagnosis.
    """

    symptoms: List[str] = Field(default_factory=list)
    duration: Optional[str] = None  # e.g., "3 days", "since yesterday"
    severity: Optional[str] = None  # e.g., "mild", "severe", "7/10"
    search_terms: List[str] = Field(default_factory=list)


class MLPrediction(BaseModel):
    """Machine-learning disease prediction from the Together AI model.

    top_3 provides fallback candidates when confidence is low.
    unknown_symptoms flags terms the model could not map to known entities.
    """

    disease: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_pct: str = ""  # Human-readable e.g. "87%"
    top_3: List[Dict[str, Any]] = Field(default_factory=list)
    unknown_symptoms: List[str] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# Triage response (API output)
# ------------------------------------------------------------------------------


class EvidenceItem(BaseModel):
    """A single PubMed evidence citation supporting the triage decision."""

    title: str
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    pmid: str
    url: str
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)


class OTCProduct(BaseModel):
    """Over-the-counter product suggestion with dosage guidance."""

    name: str
    active_ingredient: str
    dosage: str
    warnings: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(default_factory=list)


class TriageAudit(BaseModel):
    """Tamper-evident audit metadata for the triage interaction."""

    version: str = "2.0.0"
    model: str = ""
    hash_chain: Optional[str] = None
    processing_time_ms: Optional[float] = None
    evidence_sources: List[str] = Field(default_factory=list)


class TriageResponse(BaseModel):
    """Complete AI triage response returned to the client.

    All clinical fields include explicit disclaimers.  The care_advice
    field is always present and emphasizes that this is NOT a diagnosis.
    """

    status: str = "success"
    triage_level: TriageLevel = TriageLevel.UNKNOWN
    routing: RoutingDecision = RoutingDecision.NONE
    reasoning: str = ""
    red_flags: List[str] = Field(default_factory=list)
    remedies: List[str] = Field(default_factory=list)
    disease_name: Optional[str] = None
    confidence: Optional[float] = None
    symptoms: List[str] = Field(default_factory=list)
    care_advice: str = ""
    otc_products: List[OTCProduct] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    disclaimer: str = (
        "This information is for educational purposes only and does not "
        "constitute medical advice, diagnosis, or treatment. Always seek "
        "the advice of a qualified healthcare provider for personal medical "
        "concerns. If you believe you are experiencing a medical emergency, "
        "call 911 (or your local emergency number) immediately."
    )
    privacy_info: str = (
        "Your conversation is processed by an AI system. Personal identifiers "
        "are not stored with clinical data. Review our Privacy Policy for details."
    )
    audit: TriageAudit = Field(default_factory=TriageAudit)
    chat_id: Optional[str] = None

    # Compatibility fields for test expectations and simpler clients
    triage: Optional[Dict[str, Any]] = None
    response: str = ""
    sources: List[str] = Field(default_factory=list)

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return max(0.0, min(1.0, v))
        return v


# ------------------------------------------------------------------------------
# Service-internal DTOs
# ------------------------------------------------------------------------------


class TriageContext(BaseModel):
    """Internal context object passed between triage pipeline stages.

    Not exposed directly via the API — used to accumulate state across
    entity extraction, LLM prediction, evidence retrieval, and response
    formatting steps.
    """

    request: TriageRequest
    entities: Optional[ClinicalEntities] = None
    prediction: Optional[MLPrediction] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)
    chat: Optional[Dict[str, Any]] = None  # Serialized chat dict
    processing_time_ms: float = 0.0
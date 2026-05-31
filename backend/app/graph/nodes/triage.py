"""Triage and disease-info nodes."""

import logging

from app.graph.state import TriageState
from app.triage_agent import analyze as triage_analyze, get_disease_info
from app import healthcare_tools

logger = logging.getLogger(__name__)


def triage_node(state: TriageState) -> dict:
    """Run triage analysis."""
    scrubbed = state.get("scrubbed_input", "")
    ml_prediction = state.get("ml_prediction")
    ml_confidence = state.get("ml_confidence", 0.0)
    clinical_entities = {
        "symptoms": state.get("symptoms", []),
        "duration": state.get("duration"),
        "severity": state.get("severity"),
    }
    consultation_result = state.get("consultation_result")
    conversation_history = state.get("conversation_history", [])

    # Determine ML for triage (30% threshold if forcing)
    force_used = state.get("force_phrase_used", False)
    threshold = 0.30 if force_used else 0.30  # consultation path already uses 30%
    ml_for_triage = ml_prediction if ml_prediction and ml_confidence >= threshold else None

    gathered_context = consultation_result.get("gathered_context") if consultation_result else None

    triage_result = triage_analyze(
        scrubbed,
        history=conversation_history,
        clinical_entities=clinical_entities,
        gathered_context=gathered_context,
        ml_prediction=ml_for_triage,
    )

    logger.info("[Graph] triage level=%s", triage_result.get("level"))
    return {"triage_result": triage_result}


def diagnosed_info_node(state: TriageState) -> dict:
    """Get disease info for the diagnosed path (high-confidence ML)."""
    ml_prediction = state.get("ml_prediction")
    confidence = state.get("ml_confidence", 0.0)
    symptoms = state.get("symptoms", [])

    trusted_disease = ml_prediction.get("disease") if ml_prediction and confidence >= 0.30 else None
    mcp_info = healthcare_tools.find_disease_info(trusted_disease) if trusted_disease else None

    disease_info = get_disease_info(
        trusted_disease,
        top_predictions=ml_prediction.get("top_3", []) if ml_prediction else [],
        symptoms=symptoms,
        mcp_info=mcp_info,
    )

    logger.info("[Graph] diagnosed_info disease=%s", trusted_disease)
    return {"disease_info": disease_info}

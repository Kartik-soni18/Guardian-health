"""Consultation node: decides if enough info exists for triage."""

import logging

from app.graph.state import TriageState
from app.triage_agent import consult as triage_consult

logger = logging.getLogger(__name__)


def consultation_node(state: TriageState) -> dict:
    """Run consultation agent."""
    scrubbed = state.get("scrubbed_input", "")
    ml_prediction = state.get("ml_prediction")
    ml_confidence = state.get("ml_confidence", 0.0)
    conversation_history = state.get("conversation_history", [])

    consultation = triage_consult(
        scrubbed,
        conversation_history=conversation_history,
        top_predictions=ml_prediction.get("top_3", []) if ml_prediction else None,
        ml_confidence=ml_confidence,
    )

    logger.info("[Graph] consultation ready=%s", consultation.get("ready_for_triage"))
    return {"consultation_result": consultation}

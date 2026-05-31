"""Extraction nodes: clinical entity extraction and ML prediction."""

import logging

from app.graph.state import TriageState
from app.symptom_extractor import extract_clinical_entities
from app.ml_mcp_server import GuardianMLClient

logger = logging.getLogger(__name__)

_ml_client = GuardianMLClient()


def extractor_node(state: TriageState) -> dict:
    """Extract clinical entities from scrubbed text."""
    accumulated = state.get("_accumulated_text", state.get("scrubbed_input", ""))
    clinical = extract_clinical_entities(accumulated)
    logger.info("[Graph] extractor symptoms=%s", clinical.get("symptoms"))
    return {
        "symptoms": clinical.get("symptoms", []),
        "duration": clinical.get("duration"),
        "severity": clinical.get("severity"),
        "search_terms": clinical.get("search_terms", []),
    }


async def ml_predictor_node(state: TriageState) -> dict:
    """Run the Guardian-ML Random Forest model."""
    symptoms = state.get("symptoms", [])
    if not symptoms:
        logger.info("[Graph] ml_predictor skipped (no symptoms)")
        return {"ml_prediction": None, "ml_confidence": 0.0}

    prediction = await _ml_client.predict(symptoms)
    confidence = prediction.get("confidence", 0.0)
    logger.info("[Graph] ml_predictor disease=%s confidence=%.2f",
                prediction.get("disease"), confidence)
    return {
        "ml_prediction": prediction,
        "ml_confidence": confidence,
    }

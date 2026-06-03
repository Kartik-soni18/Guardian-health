"""
Extraction nodes: extractor, ml_predictor.

- extractor_node: Extracts clinical entities from scrubbed input.
- ml_predictor_node: Runs ML model for symptom prediction.
"""


import logging

from app.agents.llm_client import AsyncLLMClient
from app.agents.symptom_extractor import extract_clinical_entities
from app.graph.state import TriageState
from app.services.ml_service import MLPrediction, predict

logger = logging.getLogger("guardian.nodes.extraction")

_llm: AsyncLLMClient | None = None


def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


async def extractor_node(state: TriageState) -> dict:
    """
    Extract clinical entities (symptoms, duration, severity) from scrubbed input.
    """
    if state.get("error"):
        return {}

    scrubbed = state.get("scrubbed_input", state["user_input"])
    llm = _get_llm()

    try:
        entities = await extract_clinical_entities(scrubbed, llm)
        return {
            "symptoms": entities.symptoms,
            "duration": entities.duration,
            "severity": entities.severity,
            "search_terms": entities.search_terms,
            "demographics": entities.demographics,
            "medications": entities.medications,
            "extra_context": entities.extra_context,
        }
    except Exception as exc:
        logger.error("Extractor node error: %s", exc)
        # Return minimal fallback so pipeline continues
        return {
            "symptoms": ["unspecified"],
            "duration": None,
            "severity": None,
            "search_terms": ["general symptoms"],
            "demographics": {},
            "medications": [],
            "extra_context": f"Extraction failed: {type(exc).__name__}",
        }


async def ml_predictor_node(state: TriageState) -> dict:
    """
    Run ML prediction on extracted symptoms.
    """
    if state.get("error"):
        return {}

    symptoms = state.get("symptoms", [])
    if not symptoms:
        logger.warning("ML predictor: no symptoms, returning empty prediction")
        return {
            "ml_prediction": None,
            "ml_confidence": 0.0,
            "top_predictions": [],
        }

    try:
        prediction: MLPrediction = predict(symptoms)
        return {
            "ml_prediction": {
                "top_predictions": [
                    {"condition": p.condition, "confidence": p.confidence}
                    for p in prediction.top_predictions
                ],
                "primary_condition": prediction.primary_condition,
                "confidence": prediction.confidence,
            },
            "ml_confidence": prediction.confidence,
            "top_predictions": [
                {"condition": p.condition, "confidence": p.confidence}
                for p in prediction.top_predictions
            ],
        }
    except Exception as exc:
        logger.error("ML predictor node error: %s", exc)
        return {
            "ml_prediction": None,
            "ml_confidence": 0.0,
            "top_predictions": [],
        }

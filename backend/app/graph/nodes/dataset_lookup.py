"""Dataset lookup node — maps symptoms to Indian healthcare reference data."""

import logging

from app.graph.state import TriageState
from app.services.symptom_dataset import lookup_symptoms

logger = logging.getLogger("guardian.nodes.dataset_lookup")


async def dataset_lookup_node(state: TriageState) -> dict:
    if state.get("error"):
        return {}

    symptoms = state.get("symptoms", [])
    if not symptoms:
        return {}

    try:
        prediction = await lookup_symptoms(symptoms)
        return {
            "ml_prediction": prediction,
            "top_predictions": prediction.get("top_predictions", []),
            "ml_confidence": float(prediction.get("confidence", 0.0)),
            "dataset_matches": prediction.get("matches", []),
        }
    except Exception as exc:
        logger.error("Dataset lookup failed: %s", exc)
        return {
            "ml_prediction": None,
            "top_predictions": [],
            "ml_confidence": 0.0,
        }

"""Clinical entity extraction node."""

import logging

from app.agents.llm_client import AsyncLLMClient
from app.agents.symptom_extractor import extract_clinical_entities
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.extraction")

_llm: AsyncLLMClient | None = None


def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


async def extractor_node(state: TriageState) -> dict:
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
        return {
            "symptoms": ["unspecified"],
            "duration": None,
            "severity": None,
            "search_terms": ["general symptoms"],
            "demographics": {},
            "medications": [],
            "extra_context": f"Extraction failed: {type(exc).__name__}",
        }

"""
Triage nodes: triage_node, diagnosed_info_node, emergency_node.
"""

import logging
from pathlib import Path

from app.agents.llm_client import AsyncLLMClient
from app.agents.triage_agent import analyze
from app.graph.response_builder import build_from_triage
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.triage")

_llm: AsyncLLMClient | None = None


def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


DISEASE_INFO_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "agents" / "prompts" / "disease_info.txt"
)


async def triage_node(state: TriageState) -> dict:
    if state.get("error"):
        return {}

    scrubbed = state.get("scrubbed_input", state["user_input"])
    history = state.get("conversation_history", [])
    clinical_entities = {
        "symptoms": state.get("symptoms", []),
        "duration": state.get("duration"),
        "severity": state.get("severity"),
        "search_terms": state.get("search_terms", []),
        "extra_context": state.get("extra_context", ""),
    }
    ml_prediction = state.get("ml_prediction")

    llm = _get_llm()

    try:
        result = await analyze(
            scrubbed=scrubbed,
            history=history,
            clinical_entities=clinical_entities,
            ml_prediction=ml_prediction,
            llm=llm,
            scratchpad=state.get("scratchpad"),
        )
        structured = build_from_triage(result, state)

        return {
            "triage_result": result,
            "response_text": structured["response"],
            "structured_response": structured,
            "final_routing": "triage",
        }
    except Exception as exc:
        logger.error("Triage node error: %s", exc)
        symptoms = state.get("symptoms", [])
        high_risk = {"chest_pain", "shortness_of_breath", "syncope", "seizure"}
        symptom_set = set(s.lower().replace(" ", "_") for s in symptoms)
        is_emergency = bool(symptom_set & high_risk)

        if is_emergency:
            fallback = {
                "level": "emergent",
                "care_setting": "ER",
                "assessment": "Your symptoms require immediate evaluation.",
                "explanation": "High-risk symptoms detected.",
                "what_to_do": ["Call emergency services or go to the nearest ER immediately."],
                "what_not_to_do": ["Do not delay care or drive yourself if severely unwell."],
                "timeframe": "Immediately",
                "heuristic": True,
            }
            structured = build_from_triage(fallback, state)
            return {
                "triage_result": fallback,
                "response_text": structured["response"],
                "structured_response": structured,
                "final_routing": "emergency",
            }

        fallback = {
            "level": "routine",
            "care_setting": "primary_care",
            "assessment": "Please consult a healthcare provider for evaluation.",
            "what_to_do": ["Schedule an appointment with your doctor within a few days."],
            "what_not_to_do": ["Do not ignore worsening symptoms."],
            "timeframe": "Within 3-5 days",
            "heuristic": True,
        }
        structured = build_from_triage(fallback, state)
        return {
            "triage_result": fallback,
            "response_text": structured["response"],
            "structured_response": structured,
            "final_routing": "triage",
            "error": f"Triage node: {type(exc).__name__}",
        }


async def diagnosed_info_node(state: TriageState) -> dict:
    if state.get("error"):
        return {}

    symptoms = state.get("symptoms", [])
    user_input = state.get("user_input", "")
    search_terms = state.get("search_terms", symptoms)

    condition = search_terms[0] if search_terms else "general health information"
    if symptoms and len(symptoms) == 1:
        condition = symptoms[0]

    try:
        prompt_text = DISEASE_INFO_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Disease info prompt not found")
        return {
            "disease_info": {"condition": condition, "description": "Information temporarily unavailable."},
            "response_text": f"I'm unable to provide detailed information about '{condition}' at this time.",
            "final_routing": "disease_info",
        }

    llm = _get_llm()

    try:
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=f"Provide information about: {condition}\n\nUser query: {user_input}",
            node_type="disease_info",
            max_tokens=1024,
        )

        structured = {
            "response": result.get("description") or f"Information about {condition}.",
            "triage_level": None,
            "assessment": result.get("description", ""),
            "what_to_do": result.get("prevention", []) or [],
            "what_not_to_do": [],
            "likely_conditions": [result.get("condition", condition)],
            "red_flags": [],
            "reasoning": result.get("when_to_seek", ""),
            "confidence": 0.6,
            "dataset_used": False,
        }

        return {
            "disease_info": result,
            "response_text": structured["response"],
            "structured_response": structured,
            "final_routing": "disease_info",
        }
    except Exception as exc:
        logger.error("Disease info node error: %s", exc)
        return {
            "disease_info": {"condition": condition, "error": str(exc)},
            "response_text": (
                f"I'm unable to retrieve detailed information about '{condition}' at this time. "
                "Please consult a healthcare provider or reputable medical source."
            ),
            "final_routing": "disease_info",
            "error": f"Disease info node: {type(exc).__name__}",
        }


async def emergency_node(state: TriageState) -> dict:
    symptoms = state.get("symptoms", [])
    user_input = state.get("user_input", "")

    emergency_type = "general emergency"
    if any(s in user_input.lower() for s in ["chest pain", "heart", "heart attack"]):
        emergency_type = "cardiac emergency"
    elif any(s in user_input.lower() for s in ["can't breathe", "breathing", "choke", "suffocat"]):
        emergency_type = "respiratory emergency"
    elif any(s in user_input.lower() for s in ["suicid", "kill myself", "want to die"]):
        emergency_type = "mental health crisis"
    elif any(s in user_input.lower() for s in ["seizure", "convulsion", "fitting"]):
        emergency_type = "neurological emergency"
    elif any(s in user_input.lower() for s in ["bleed", "blood", "hemorrhage"]):
        emergency_type = "hemorrhage"

    structured = {
        "response": f"Your symptoms suggest a {emergency_type}. Seek emergency care immediately.",
        "triage_level": "emergent",
        "assessment": f"{emergency_type.title()} — immediate emergency care required.",
        "what_to_do": [
            "Go to the nearest hospital emergency department immediately.",
            "Contact local emergency services (e.g. 102/108 in India) if you need urgent transport.",
        ],
        "what_not_to_do": [
            "Do not drive yourself if you have severe symptoms.",
            "Do not wait to see if symptoms pass.",
        ],
        "likely_conditions": [emergency_type],
        "red_flags": symptoms,
        "reasoning": "Emergency fast-path triggered.",
        "confidence": 0.95,
        "dataset_used": False,
    }

    logger.critical(
        "Emergency node triggered: user=%s type=%s",
        state.get("user_id"),
        emergency_type,
    )

    return {
        "triage_result": {
            "level": "emergent",
            "care_setting": "ER",
            "emergency_type": emergency_type,
            "heuristic": True,
        },
        "response_text": structured["response"],
        "structured_response": structured,
        "final_routing": "emergency",
        "is_emergency": True,
        "emergency_detected": True,
    }

"""
Triage nodes: triage_node, diagnosed_info_node, emergency_node.

- triage_node: Assigns triage level and care setting.
- diagnosed_info_node: Provides disease information.
- emergency_node: Fast-path emergency response.
"""


import json
import logging
from pathlib import Path

from app.agents.llm_client import AsyncLLMClient
from app.agents.triage_agent import analyze
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
    """
    Assign triage level based on clinical analysis.
    """
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
        )

        # Build response text
        response_parts = [
            f"Triage Level: {result.get('level', 'unknown').upper()}",
            f"Recommended Care: {result.get('care_setting', 'unknown').replace('_', ' ').title()}",
            "",
            f"{result.get('explanation', '')}",
            "",
            f"Action: {result.get('action', 'Consult a healthcare provider.')}",
            f"Timeframe: {result.get('timeframe', 'Schedule as needed')}",
        ]

        if result.get("red_flags"):
            response_parts.extend([
                "",
                "Warning signs — seek immediate care if you experience:",
                *[f"  • {flag}" for flag in result["red_flags"]],
            ])

        if result.get("safety_net"):
            response_parts.extend(["", f"Safety guidance: {result['safety_net']}"])

        response_text = "\n".join(response_parts)

        return {
            "triage_result": result,
            "response_text": response_text,
            "final_routing": "triage",
        }
    except Exception as exc:
        logger.error("Triage node error: %s", exc)
        # Emergency fallback for high-risk symptoms
        symptoms = state.get("symptoms", [])
        high_risk = {"chest_pain", "shortness_of_breath", "syncope", "seizure"}
        symptom_set = set(s.lower().replace(" ", "_") for s in symptoms)
        is_emergency = bool(symptom_set & high_risk)

        if is_emergency:
            return {
                "triage_result": {
                    "level": "emergent",
                    "care_setting": "ER",
                    "explanation": "Your symptoms require immediate evaluation.",
                    "action": "Seek emergency care immediately.",
                    "timeframe": "Immediately",
                    "heuristic": True,
                },
                "response_text": (
                    "EMERGENCY TRIAGE: Your symptoms require immediate emergency evaluation. "
                    "Please call emergency services or go to the nearest emergency department now."
                ),
                "final_routing": "emergency",
            }

        return {
            "triage_result": {
                "level": "routine",
                "care_setting": "primary_care",
                "explanation": "Please consult a healthcare provider for evaluation.",
                "action": "Schedule an appointment with your doctor.",
                "timeframe": "Within 3-5 days",
                "heuristic": True,
            },
            "response_text": (
                "I'm unable to complete the triage analysis at this time. "
                "Please consult your healthcare provider for proper evaluation."
            ),
            "final_routing": "triage",
            "error": f"Triage node: {type(exc).__name__}",
        }


async def diagnosed_info_node(state: TriageState) -> dict:
    """
    Provide disease information for informational queries.
    """
    if state.get("error"):
        return {}

    # Determine the condition to look up
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

        # Build response text
        response_parts = [f"# {result.get('condition', condition)}", ""]
        if result.get("description"):
            response_parts.append(result["description"])
            response_parts.append("")
        if result.get("symptoms"):
            response_parts.append("**Common Symptoms:**")
            response_parts.extend([f"  • {s}" for s in result["symptoms"]])
            response_parts.append("")
        if result.get("common_tests"):
            response_parts.append("**Common Tests:**")
            response_parts.extend([f"  • {t}" for t in result["common_tests"]])
            response_parts.append("")
        if result.get("treatment_overview"):
            response_parts.append(f"**Treatment Overview:** {result['treatment_overview']}")
            response_parts.append("")
        if result.get("when_to_seek"):
            response_parts.append(f"**When to Seek Care:** {result['when_to_seek']}")
            response_parts.append("")
        if result.get("prevention"):
            response_parts.append("**Prevention:**")
            response_parts.extend([f"  • {p}" for p in result["prevention"]])
            response_parts.append("")
        if result.get("references"):
            response_parts.append(f"**References:** {', '.join(result['references'])}")
            response_parts.append("")
        if result.get("disclaimer"):
            response_parts.append(f"\n*{result['disclaimer']}*")

        response_text = "\n".join(response_parts)

        return {
            "disease_info": result,
            "response_text": response_text,
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
    """
    Fast-path emergency response for high-acuity situations.
    """
    symptoms = state.get("symptoms", [])
    user_input = state.get("user_input", "")

    # Determine emergency type from symptoms
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

    response_text = (
        f"🚨 EMERGENCY — {emergency_type.upper()}\n\n"
        "Your symptoms or statement suggest a potentially life-threatening situation.\n\n"
        "**CALL EMERGENCY SERVICES (911 in US/Canada, 112 in EU, 999 in UK) OR "
        "GO TO THE NEAREST EMERGENCY DEPARTMENT IMMEDIATELY.**\n\n"
        "Do NOT drive yourself if you are experiencing severe symptoms.\n\n"
        "If this is a mental health crisis:\n"
        "  • 988 Suicide & Crisis Lifeline (US)\n"
        "  • Crisis Text Line: Text HOME to 741741\n\n"
        "Disclaimer: This is an emergency alert, not a diagnosis. "
        "Immediate professional medical evaluation is required."
    )

    logger.critical(
        "Emergency node triggered: user=%s type=%s",
        state.get("user_id"),
        emergency_type,
    )

    return {
        "triage_result": {
            "level": "emergent",
            "care_setting": "ER",
            "explanation": f"{emergency_type} detected — immediate emergency care required.",
            "action": "Call emergency services or go to ER immediately.",
            "timeframe": "Immediately",
            "emergency_type": emergency_type,
            "heuristic": True,
        },
        "response_text": response_text,
        "final_routing": "emergency",
        "is_emergency": True,
        "emergency_detected": True,
    }

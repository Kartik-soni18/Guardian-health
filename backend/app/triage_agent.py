import logging
import json
import random
import re as _re

from app import llm_client as gemini_client
from app.prompt_hub import get_prompt

_CONSULTATION_SYSTEM_PROMPT = get_prompt("consultation")
_SYSTEM_PROMPT = get_prompt("triage")
_DISEASE_INFO_WITH_DIAGNOSIS = get_prompt("disease-info-with-diagnosis")
_DISEASE_INFO_NO_DIAGNOSIS = get_prompt("disease-info-no-diagnosis")

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "⚠️ This is an AI-assisted triage suggestion only. "
    "It is NOT a medical diagnosis. Always consult a licensed healthcare "
    "professional before making any medical decisions."
)


def consult(
    scrubbed_query: str,
    conversation_history: list = None,
    top_predictions: list = None,
    ml_confidence: float = None,
) -> dict:
    history_text = ""
    if conversation_history:
        lines = []
        for entry in conversation_history:
            role = entry.get("role", "user").capitalize()
            lines.append(f"{role}: {entry['content']}")
        history_text = "\n".join(lines) + "\n"

    # Check if patient has already provided the key clinical fields across all text
    all_text = scrubbed_query.lower()
    if conversation_history:
        for entry in conversation_history:
            all_text += " " + entry.get("content", "").lower()
    has_duration = any(w in all_text for w in ["day", "week", "month", "hour", "yesterday", "ago", "since"])
    has_severity = any(w in all_text for w in ["mild", "moderate", "severe", "extreme", "little", "bit", "very", "extremely"])
    info_complete = has_duration and has_severity

    top_context = ""
    if top_predictions:
        pred_str = ", ".join([f"{d} ({c*100:.1f}%)" for d, c in top_predictions[:3]])
        top_context = f"\n\n[System: Currently considering: {pred_str}."
        if ml_confidence is not None and ml_confidence < 0.5 and not info_complete:
            top_context += " ML confidence is LOW — ask targeted questions before marking ready_for_triage true.]"
        else:
            top_context += " Ask targeted questions to narrow the diagnosis.]"
    elif ml_confidence is not None and ml_confidence < 0.5 and not info_complete:
        top_context = "\n\n[System: ML confidence is LOW — gather duration, severity, symptom location, and associated symptoms before marking ready_for_triage true.]"

    user_content = f"{history_text}Patient: {scrubbed_query}{top_context}"

    try:
        raw = gemini_client.call(
            system_prompt=_CONSULTATION_SYSTEM_PROMPT,
            user_content=user_content,
            temperature=0.3,
            max_tokens=400,
            timeout=20.0,
        )
        raw = raw.strip("```json").strip("```").strip()
        result = json.loads(raw)
        logger.info("[Consult] ready_for_triage=%s", result.get("ready_for_triage"))
        return {
            "ready_for_triage": bool(result.get("ready_for_triage", False)),
            "follow_up_message": result.get("follow_up_message", ""),
            "gathered_context": result.get("gathered_context", ""),
            "current_state": result.get("current_state", "consulting"),
            "top_candidates": [d for d, _ in top_predictions[:3]] if top_predictions else [],
        }

    except Exception as exc:
        logger.warning("[Consult] Failed: %s — heuristic fallback", exc)
        has_duration = any(w in scrubbed_query.lower() for w in ["day", "week", "month", "hour", "yesterday", "ago", "since"])
        has_severity = any(w in scrubbed_query.lower() for w in ["mild", "moderate", "severe", "extreme", "little", "bit", "very", "extremely"])
        is_forcing = any(k in scrubbed_query.lower() for k in ["that's it", "thats it", "i don't know", "i dont know", "proceed anyway"])
        low_ml = ml_confidence is not None and ml_confidence < 0.5
        needs_more = (not has_duration or not has_severity) and not is_forcing

        if needs_more and low_ml and len(scrubbed_query.split()) < 20 and not conversation_history and not is_forcing:
            return {
                "ready_for_triage": False,
                "follow_up_message": (
                    "Thank you for reaching out. To help me assess your situation properly, I need a bit more:\n\n"
                    "1. When did this start?\n2. How severe is it (mild, moderate, severe)?\n3. Any other symptoms?"
                ),
                "gathered_context": scrubbed_query,
            }
        return {"ready_for_triage": True, "follow_up_message": "", "gathered_context": scrubbed_query}


def analyze(
    scrubbed_query: str,
    history: list = None,
    clinical_entities: dict = None,
    research_result: dict = None,
    gathered_context: str = None,
    ml_prediction: dict = None,
) -> dict:
    result = _call_llm(scrubbed_query, history, clinical_entities, research_result, gathered_context, ml_prediction)
    result["disclaimer"] = _DISCLAIMER
    return result


def _call_llm(
    query: str,
    history: list = None,
    clinical_entities: dict = None,
    research_result: dict = None,
    gathered_context: str = None,
    ml_prediction: dict = None,
) -> dict:
    context_parts = []

    if gathered_context:
        context_parts.append(f"=== Consultation Summary ===\n{gathered_context}")

    if ml_prediction and ml_prediction.get("model_status") == "loaded":
        confidence = ml_prediction.get("confidence", 0.0)
        disease = ml_prediction.get("disease")
        top_3 = ml_prediction.get("top_3", [])
        unknown_symptoms = ml_prediction.get("unknown_symptoms", [])

        if confidence >= 0.3:
            ml_context = f"=== ML Prediction (Random Forest) ===\nPredicted: {disease}\nConfidence: {ml_prediction.get('confidence_pct', '0%')}"
            if top_3:
                ml_context += f"\nTop 3: {', '.join([f'{d} ({c*100:.1f}%)' for d, c in top_3])}"
            if confidence >= 0.7:
                ml_context += "\n⚠ HIGH confidence — strongly consider in reasoning."
            elif confidence >= 0.5:
                ml_context += "\n• MODERATE confidence — supporting evidence."
            else:
                ml_context += "\n• LOW confidence — supplementary only."
            if unknown_symptoms:
                ml_context += f"\nUnknown symptoms: {', '.join(unknown_symptoms)}"
            context_parts.append(ml_context)
        elif top_3:
            context_parts.append(
                f"=== ML Suggestions (Very Low Confidence) ===\nPossible: {', '.join([f'{d} ({c*100:.1f}%)' for d, c in top_3])}\nWeak signals only."
            )

    if research_result and research_result.get("articles"):
        articles = research_result["articles"]
        context_parts.append("=== PubMed Research Context ===")
        if research_result.get("summary"):
            context_parts.append(f"Summary: {research_result['summary']}")
        for i, art in enumerate(articles[:3], 1):
            context_parts.append(f"[{i}] {art['title']} ({art['year']}, {art['journal']})\n    {art['abstract'][:400]}")

    if clinical_entities:
        symptoms = clinical_entities.get("symptoms") or []
        if symptoms:
            context_parts.append(f"Extracted symptoms: {', '.join(symptoms)}")
        if clinical_entities.get("duration"):
            context_parts.append(f"Duration: {clinical_entities['duration']}")
        if clinical_entities.get("severity"):
            context_parts.append(f"Severity: {clinical_entities['severity']}")

    context_block = "\n\n".join(context_parts)
    user_content = f"Patient query: {query}\n\n{context_block}" if context_block else f"Patient query: {query}"

    try:
        raw = gemini_client.call(
            system_prompt=_SYSTEM_PROMPT,
            user_content=user_content,
            temperature=0.2,
            max_tokens=500,
            timeout=30.0,
        )
        raw = raw.strip("```json").strip("```").strip()
        result = json.loads(raw)
        if "level" not in result or result["level"] not in ("Self-Care", "Urgent Care", "Emergency Room"):
            raise ValueError(f"Invalid level: {result.get('level')}")
        logger.info("[Triage] level=%s", result.get("level"))
        return result

    except Exception as exc:
        logger.warning("[Triage] LLM failed: %s — fallback", exc)
        return _fallback(research_result, clinical_entities, ml_prediction)


_FALLBACK_REASONING_TEMPLATES = [
    "Based on your symptoms ({symptoms}), our analysis suggests possible {disease}. Please consult a licensed healthcare professional.",
    "Given what you've described ({symptoms}), {disease} is one possibility to consider. Please consult a licensed healthcare professional.",
    "Your reported symptoms ({symptoms}) may be associated with {disease}. A clinician can provide a definitive assessment. Please consult a licensed healthcare professional.",
]

_FALLBACK_RED_FLAGS = [
    ["Fever not responding to medication", "Signs of dehydration", "Shortness of breath or chest pain", "Confusion or altered mental status"],
    ["Worsening pain despite rest", "Difficulty breathing", "Persistent high fever", "Unusual drowsiness or confusion"],
    ["Chest tightness or pressure", "Inability to keep fluids down", "Severe headache with neck stiffness", "Sudden confusion or disorientation"],
]

_FALLBACK_REMEDIES = [
    ["Stay hydrated", "Get plenty of rest"],
    ["Drink clear fluids", "Rest in a comfortable position"],
    ["Keep warm and rest", "Sip water or oral rehydration solution"],
]


def _fallback(research_result=None, clinical_entities=None, ml_prediction=None) -> dict:
    symptoms = []
    severity = None
    if clinical_entities:
        symptoms = clinical_entities.get("symptoms") or []
        severity = clinical_entities.get("severity")

    symptom_str = ", ".join(symptoms) if symptoms else "the described symptoms"
    level = "Self-Care"

    if severity == "severe":
        level = "Urgent Care"
    elif ml_prediction and ml_prediction.get("model_status") == "loaded":
        disease = ml_prediction.get("disease", "").lower()
        confidence = ml_prediction.get("confidence", 0.0)
        critical = any(c in disease for c in ["heart attack", "stroke", "sepsis", "meningitis", "emergency", "acute"])
        if critical or confidence >= 0.6:
            level = "Urgent Care"
    elif severity == "moderate" or len(symptoms) > 1:
        level = "Urgent Care"

    if ml_prediction and ml_prediction.get("model_status") == "loaded":
        disease = ml_prediction.get("disease")
        confidence = ml_prediction.get("confidence", 0.0)
        template = random.choice(_FALLBACK_REASONING_TEMPLATES)
        reasoning = template.format(symptoms=symptom_str, disease=disease)
        source = "ML Model (Random Forest) + Clinical Protocol"
    elif research_result and research_result.get("summary"):
        reasoning = (
            f"Based on available research for {symptom_str}: {research_result['summary']} "
            f"Please consult a licensed healthcare professional."
        )
        source = "PubMed / NCBI Research"
    else:
        reasoning = (
            f"Your symptoms ({symptom_str}) require professional evaluation. "
            f"Please consult a licensed healthcare professional."
        )
        source = "GuardianHealth Clinical Protocol"

    return {
        "level": level,
        "reasoning": reasoning,
        "red_flags": random.choice(_FALLBACK_RED_FLAGS),
        "guideline_source": source,
        "remedies": random.choice(_FALLBACK_REMEDIES),
    }


def get_disease_info(
    disease_name: str,
    top_predictions: list = None,
    symptoms: list = None,
    mcp_info: str = None,
) -> dict:
    effective_disease = disease_name or "symptoms described below (no high-confidence diagnosis)"
    context = f"Disease/Condition: {effective_disease}\n"
    if symptoms:
        context += f"Symptoms: {', '.join(symptoms)}\n"
    if top_predictions:
        context += f"ML top possibilities: {', '.join([f'{d} ({c*100:.1f}%)' for d, c in top_predictions[:3]])}\n"
    if mcp_info:
        context += f"\n=== Healthcare Research ===\n{mcp_info}\n"

    system_prompt = _DISEASE_INFO_WITH_DIAGNOSIS if disease_name else _DISEASE_INFO_NO_DIAGNOSIS

    try:
        raw = gemini_client.call(
            system_prompt=system_prompt,
            user_content=f"Provide medical information for:\n\n{context}",
            temperature=0.3,
            max_tokens=600,
            timeout=20.0,
        )
        raw = _re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = _re.sub(r"\s*```$", "", raw.strip())
        result = json.loads(raw)
        logger.info("[DiseaseInfo] Retrieved for %s", disease_name)
        return {
            "cures": result.get("cures", []),
            "prevention": result.get("prevention", []),
            "self_care": result.get("self_care", []),
            "emergency_signs": result.get("emergency_signs", []),
            "otc_products": result.get("otc_products", []),
        }

    except Exception as exc:
        logger.warning("[DiseaseInfo] Failed for %s: %s", disease_name, exc)
        return {"cures": [], "prevention": [], "self_care": [], "emergency_signs": []}

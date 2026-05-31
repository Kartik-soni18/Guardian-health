import re
import logging

logger = logging.getLogger(__name__)

_DIAGNOSIS_PATTERNS = [
    r"\byou are diagnosed with\b",
    r"\bthe diagnosis is\b",
    r"\byou're suffering from\b",
    r"\byou have contracted\b",
]

_RX_KEYWORDS = [
    "specific dosage", "milligrams", "mg/kg",
    "prescription only", "prescribe you", "dose of",
]

_SAFE_DISCLAIMER = (
    "⚠️ This is an AI-assisted triage suggestion only. "
    "It is NOT a medical diagnosis. Always consult a licensed healthcare "
    "professional before making any medical decisions."
)


def review(triage_result: dict) -> dict:
    reasoning = triage_result.get("reasoning", "").lower()
    red_flags_text = " ".join(triage_result.get("red_flags", [])).lower()
    full_text = reasoning + " " + red_flags_text

    for pattern in _DIAGNOSIS_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            logger.warning("Compliance BLOCK — diagnosis language: %s", pattern)
            return _blocked_response(triage_result, f"Prohibited diagnosis language detected.")

    for kw in _RX_KEYWORDS:
        if kw in full_text:
            logger.warning("Compliance BLOCK — medication keyword: %s", kw)
            return _blocked_response(triage_result, f"Medication-specific language detected.")

    if not triage_result.get("disclaimer"):
        triage_result["disclaimer"] = _SAFE_DISCLAIMER

    logger.info("Compliance APPROVED — level=%s", triage_result.get("level"))
    return {"approved": True, "final_response": triage_result, "blocked_reason": None}


def _blocked_response(original: dict, reason: str) -> dict:
    return {
        "approved": False,
        "final_response": {
            "level": original.get("level", "Urgent Care"),
            "reasoning": (
                "Our compliance system detected content that may constitute a medical diagnosis "
                "or specific treatment recommendation. Please consult a licensed healthcare professional."
            ),
            "red_flags": ["Professional evaluation required"],
            "guideline_source": "GuardianHealth Compliance Policy",
            "disclaimer": _SAFE_DISCLAIMER,
            "compliance_overridden": True,
        },
        "blocked_reason": reason,
    }

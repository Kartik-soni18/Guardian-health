"""
Symptom Extractor — Extracts clinical entities from user text.

Uses LLM extraction with a comprehensive keyword fallback system.
Includes regex-based duration and severity parsing.
"""


import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.agents.llm_client import AsyncLLMClient

logger = logging.getLogger("guardian.extractor")

# ---------------------------------------------------------------------------
# Symptom keyword database (60+ patterns)
# ---------------------------------------------------------------------------
SYMPTOM_PATTERNS: dict[str, list[str]] = {
    "chest_pain": ["chest pain", "chest tightness", "chest pressure", "chest discomfort"],
    "shortness_of_breath": ["shortness of breath", "can't breathe", "cannot breathe", "difficulty breathing", "dyspnea", "breathless", "breathlessness"],
    "fever": ["fever", "febrile", "high temperature", "running a temperature", "hot and cold"],
    "cough": ["cough", "coughing", "hacking", "dry cough", "wet cough", "productive cough"],
    "fatigue": ["fatigue", "tired", "exhausted", "no energy", "lethargic", "weakness", "malaise"],
    "headache": ["headache", "migraine", "head pain", "throbbing head", "pounding head"],
    "nausea": ["nausea", "nauseous", "feel like throwing up", "queasy", "sick to stomach"],
    "vomiting": ["vomiting", "throwing up", "puking", "emesis", "threw up"],
    "diarrhea": ["diarrhea", "loose stool", "watery stool", "frequent bowel movements"],
    "constipation": ["constipation", "can't poop", "difficulty passing stool", "hard stool"],
    "abdominal_pain": ["stomach pain", "abdominal pain", "belly pain", "tummy ache", "stomach ache", "gut pain", "cramping"],
    "back_pain": ["back pain", "lower back pain", "upper back pain", "backache", "lumbar pain"],
    "joint_pain": ["joint pain", "arthralgia", "aching joints", "joint swelling", "stiff joints"],
    "muscle_pain": ["muscle pain", "myalgia", "muscle ache", "sore muscles", "body ache"],
    "sore_throat": ["sore throat", "throat pain", "painful swallowing", "scratchy throat", "pharyngitis"],
    "runny_nose": ["runny nose", "rhinorrhea", "nasal discharge", "drippy nose"],
    "congestion": ["congestion", "stuffy nose", "nasal congestion", "blocked nose", "sinus pressure"],
    "dizziness": ["dizzy", "dizziness", "lightheaded", "vertigo", "spinning", "feeling faint"],
    "rash": ["rash", "skin rash", "hives", "urticaria", "dermatitis", "skin eruption", "spots on skin"],
    "itching": ["itching", "itchy", "pruritus", "scratching", "skin irritation"],
    "swelling": ["swelling", "edema", "puffy", "bloated", "swollen"],
    "bleeding": ["bleeding", "blood", "hemorrhage", "bloody", "hematoma"],
    "weight_loss": ["weight loss", "losing weight", "unintentional weight loss", "dropping weight"],
    "weight_gain": ["weight gain", "gaining weight", "swelling weight", "bloating weight"],
    "loss_of_appetite": ["loss of appetite", "not hungry", "anorexia", "decreased appetite", "no appetite"],
    "night_sweats": ["night sweats", "sweating at night", "drenching sweats"],
    "chills": ["chills", "rigors", "shivering", "goosebumps", "feeling cold"],
    "confusion": ["confusion", "confused", "disoriented", "altered mental status", "not thinking clearly"],
    "memory_loss": ["memory loss", "forgetful", "can't remember", "amnesia", "short term memory"],
    "numbness": ["numbness", "tingling", "pins and needles", "paresthesia", "loss of sensation"],
    "seizure": ["seizure", "convulsion", "fitting", "episode", "tonic clonic"],
    "palpitations": ["palpitations", "racing heart", "heart racing", "pounding heart", "skipped beat", "irregular heartbeat"],
    "syncope": ["fainted", "passed out", "syncope", "blackout", "loss of consciousness"],
    "insomnia": ["insomnia", "can't sleep", "difficulty sleeping", "trouble falling asleep"],
    "anxiety": ["anxiety", "anxious", "worried", "nervous", "panic", "restless"],
    "depression": ["depression", "depressed", "hopeless", "sadness", "no interest", "anhedonia"],
    "suicidal_ideation": ["suicidal", "want to die", "kill myself", "end it all", "no reason to live"],
    "urinary_frequency": ["urinary frequency", "frequent urination", "peeing a lot", "urinating often"],
    "dysuria": ["painful urination", "burning urination", "dysuria", "hurts to pee"],
    "hematuria": ["blood in urine", "bloody urine", "red urine", "hematuria"],
    "jaundice": ["yellow skin", "yellow eyes", "jaundice", "icterus"],
    "vision_changes": ["blurry vision", "vision changes", "double vision", "diplopia", "seeing spots", "vision loss"],
    "hearing_loss": ["hearing loss", "can't hear", "deafness", "ringing in ears", "tinnitus", "ear pressure"],
    "dysphagia": ["difficulty swallowing", "can't swallow", "dysphagia", "painful swallowing"],
    "hoarseness": ["hoarseness", "hoarse", "lost voice", "voice changes", "raspy voice"],
    "wheezing": ["wheezing", "wheeze", "noisy breathing", "whistling breathing"],
    "cyanosis": ["blue lips", "blue fingers", "cyanosis", "turning blue", "pale skin"],
    "petechiae": ["petechiae", "small red spots", "pinpoint spots", "purpura", "bruising easily"],
    "lymphedema": ["swollen lymph nodes", "lymphadenopathy", "lump in neck", "lump in armpit", "lump in groin"],
}

# ---------------------------------------------------------------------------
# Duration patterns
# ---------------------------------------------------------------------------
DURATION_PATTERN = re.compile(
    r"(?:for\s+)?(\d+|a|an|several|few|couple)\s+(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)",
    re.IGNORECASE,
)

SEVERITY_KEYWORDS: dict[str, list[str]] = {
    "mild": ["mild", "slight", "minor", "little", "a bit", "somewhat", "not too bad"],
    "moderate": ["moderate", "fairly", "pretty", "uncomfortable", " bothersome", "significant"],
    "severe": ["severe", "intense", "extreme", "unbearable", "excruciating", "worst", "terrible", "agonizing"],
}


class ClinicalEntities(BaseModel):
    """Structured clinical entity extraction result."""

    symptoms: list[str] = Field(default_factory=list)
    duration: str | None = None
    severity: str | None = None
    search_terms: list[str] = Field(default_factory=list)
    demographics: dict[str, Any] = Field(default_factory=dict)
    medications: list[str] = Field(default_factory=list)
    extra_context: str = ""


def _keyword_extraction(text: str) -> dict[str, Any]:
    """Fallback keyword-based symptom extraction."""
    found_symptoms: list[str] = []
    lowered = text.lower()

    for canonical, keywords in SYMPTOM_PATTERNS.items():
        for kw in keywords:
            if kw in lowered:
                found_symptoms.append(canonical)
                break

    # Duration extraction
    duration = None
    duration_match = DURATION_PATTERN.search(text)
    if duration_match:
        duration = duration_match.group(0)

    # Severity extraction
    severity = None
    for sev_level, keywords in SEVERITY_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                severity = sev_level
                break
        if severity:
            break

    # Search terms = canonical symptoms + lay terms from text
    search_terms = found_symptoms.copy()
    if duration_match:
        search_terms.append(duration_match.group(2).lower())

    return {
        "symptoms": found_symptoms,
        "duration": duration,
        "severity": severity,
        "search_terms": search_terms,
        "demographics": {},
        "medications": [],
        "extra_context": f"Keyword extraction found {len(found_symptoms)} symptoms.",
    }


EXTRACTION_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent / "prompts" / "extraction.txt"
)


async def extract_clinical_entities(text: str, llm: AsyncLLMClient) -> ClinicalEntities:
    """
    Extract clinical entities using LLM + keyword fallback.

    Args:
        text: Raw (but scrubbed) user input.
        llm: AsyncLLMClient instance.

    Returns:
        ClinicalEntities with symptoms, duration, severity, etc.
    """
    try:
        prompt_text = EXTRACTION_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Extraction prompt not found, using keyword fallback only")
        return ClinicalEntities(**_keyword_extraction(text))

    try:
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=f'Patient message: """{text}"""\n\nExtract clinical entities.',
            node_type="extraction",
            max_tokens=512,
        )

        # Validate required fields
        symptoms = result.get("symptoms", [])
        if not symptoms:
            # LLM failed to find symptoms — use keyword fallback
            logger.warning("LLM extraction returned empty symptoms, using keyword fallback")
            fallback = _keyword_extraction(text)
            symptoms = fallback["symptoms"] or ["unspecified_symptom"]
        else:
            fallback = None

        return ClinicalEntities(
            symptoms=symptoms,
            duration=result.get("duration") or (fallback["duration"] if fallback else None),
            severity=result.get("severity") or (fallback["severity"] if fallback else None),
            search_terms=result.get("search_terms", symptoms),
            demographics=result.get("demographics", {}),
            medications=result.get("medications", []),
            extra_context=result.get("extra_context", ""),
        )

    except Exception as exc:
        logger.error("LLM extraction failed: %s, using keyword fallback", exc)
        fallback = _keyword_extraction(text)
        if not fallback["symptoms"]:
            fallback["symptoms"] = ["unspecified_symptom"]
            fallback["search_terms"] = ["general symptoms"]
        return ClinicalEntities(**fallback)

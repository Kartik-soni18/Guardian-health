import logging
import json

from app import llm_client as gemini_client
from app.prompt_hub import get_prompt

_EXTRACTION_SYSTEM_PROMPT = get_prompt("extraction")

logger = logging.getLogger(__name__)


def extract_clinical_entities(scrubbed_query: str) -> dict:
    try:
        raw = gemini_client.call(
            system_prompt=_EXTRACTION_SYSTEM_PROMPT,
            user_content=scrubbed_query,
            temperature=0.1,
            max_tokens=200,
            timeout=10.0,
        )
        raw = raw.strip("```json").strip("```").strip()
        entities = json.loads(raw)
        result = {
            "symptoms":     entities.get("symptoms", []),
            "duration":     entities.get("duration"),
            "severity":     entities.get("severity"),
            "search_terms": entities.get("search_terms", []),
        }
        logger.info("[Extractor] entities=%s", result)
        return result

    except Exception as exc:
        logger.warning("[Extractor] Failed: %s — keyword fallback", exc)
        return _keyword_fallback(scrubbed_query)


_COMMON_SYMPTOMS = [
    "itching", "skin_rash", "nodal_skin_eruptions", "continuous_sneezing", "shivering", "chills",
    "joint_pain", "stomach_pain", "acidity", "ulcers_on_tongue", "muscle_wasting", "vomiting",
    "burning_micturition", "spotting_ urination", "fatigue", "weight_gain", "anxiety",
    "cold_hands_and_feets", "mood_swings", "weight_loss", "restlessness", "lethargy",
    "patches_in_throat", "irregular_sugar_level", "cough", "high_fever", "sunken_eyes",
    "breathlessness", "sweating", "dehydration", "indigestion", "headache", "yellowish_skin",
    "dark_urine", "nausea", "loss_of_appetite", "pain_behind_the_eyes", "back_pain",
    "constipation", "abdominal_pain", "diarrhoea", "mild_fever", "yellow_urine",
    "yellowing_of_eyes", "acute_liver_failure", "fluid_overload", "swelling_of_stomach",
    "swelled_lymph_nodes", "malaise", "blurred_and_distorted_vision", "phlegm", "throat_irritation",
    "redness_of_eyes", "sinus_pressure", "runny_nose", "congestion", "chest_pain", "weakness_in_limbs",
    "fast_heart_rate", "pain_during_bowel_movements", "pain_in_anal_region", "bloody_stool",
    "irritation_in_anus", "neck_pain", "dizziness", "cramps", "bruising", "obesity",
    "swollen_legs", "swollen_blood_vessels", "puffy_face_and_eyes", "enlarged_thyroid",
    "brittle_nails", "swollen_extremeties", "excessive_hunger", "extra_marital_contacts",
    "drying_and_tingling_lips", "slurred_speech", "knee_pain", "hip_joint_pain",
    "muscle_weakness", "stiff_neck", "swelling_joints", "movement_stiffness",
    "spinning_movements", "loss_of_balance", "unsteadiness", "weakness_of_one_body_side",
    "loss_of_smell", "bladder_discomfort", "foul_smell_of urine", "continuous_feel_of_urine",
    "passage_of_gases", "internal_itching", "toxic_look_(typhos)", "depression", "irritability",
    "muscle_pain", "altered_sensorium", "red_spots_over_body", "belly_pain", "abnormal_menstruation",
    "dischromic _patches", "watering_from_eyes", "increased_appetite", "polyuria", "family_history",
    "mucoid_sputum", "rusty_sputum", "lack_of_concentration", "visual_disturbances",
    "receiving_blood_transfusion", "receiving_unsterile_injections", "coma", "stomach_bleeding",
    "distention_of_abdomen", "history_of_alcohol_consumption", "fluid_overload.1",
    "blood_in_sputum", "prominent_veins_on_calf", "palpitations", "painful_walking",
    "pus_filled_pimples", "blackheads", "scurring", "skin_peeling", "silver_like_dusting",
    "small_dents_in_nails", "inflammatory_nails", "blister", "red_sore_around_nose",
    "yellow_crust_ooze",
    "headache", "fever", "high fever", "chest pain", "cough", "diarrhea",
    "rash", "itching", "red spots", "abdominal pain", "stomach pain", "back pain",
    "fatigue", "weakness", "muscle pain", "joint pain", "nausea", "vomiting",
    "shortness of breath", "breathing difficulty", "anxiety", "depression",
]

_NATURAL_LANGUAGE_MAPPING = {
    "chest hurt": "chest_pain",
    "chest ache": "chest_pain",
    "chest tightness": "chest_pain",
    "breathing pain": "chest_pain",
    "hurts when breathe": "chest_pain",
    "difficult breath": "breathlessness",
    "hard to breathe": "breathlessness",
    "high temp": "high_fever",
    "temperature": "high_fever",
    "skin problem": "skin_rash",
    "red mark": "red_spots_over_body",
    "body ache": "muscle_pain",
    "feeling weak": "weakness_in_limbs",
    "lose consciousness": "coma",
    "pass out": "coma",
    "feel dizzy": "dizziness",
    "trouble walking": "painful_walking",
    "can't focus": "lack_of_concentration",
    "can't remember": "lack_of_concentration",
    "bleeding": "blood_in_sputum",
    "bleeding finger": "blood_in_sputum",
    "blood": "blood_in_sputum",
    "wound": "blood_in_sputum",
    "cut": "blood_in_sputum",
}

_BODY_PART_SYMPTOMS = {
    "left chest":  "chest_pain",
    "right chest": "chest_pain",
    "chest":       "chest_pain",
    "stomach":     "stomach_pain",
    "abdomen":     "abdominal_pain",
    "belly":       "belly_pain",
    "head":        "headache",
    "back":        "back_pain",
    "neck":        "neck_pain",
    "shoulder":    "joint_pain",
    "knee":        "knee_pain",
    "ankle":       "joint_pain",
    "foot":        "joint_pain",
    "feet":        "joint_pain",
    "finger":      "joint_pain",
    "fingertip":   "joint_pain",
    "fingers":     "joint_pain",
    "arm":         "joint_pain",
    "leg":         "joint_pain",
    "throat":      "throat_irritation",
    "ear":         "joint_pain",
    "eye":         "pain_behind_the_eyes",
    "hip":         "hip_joint_pain",
    "wrist":       "joint_pain",
    "jaw":         "joint_pain",
}

_SEVERITY_WORDS = {
    "mild":     ["mild", "slight", "minor", "little"],
    "moderate": ["moderate", "noticeable", "uncomfortable"],
    "severe":   ["severe", "intense", "excruciating", "unbearable", "extreme", "worst"],
}

_DURATION_PATTERNS = [
    ("hour",  "hours"),
    ("day",   "days"),
    ("week",  "weeks"),
    ("month", "months"),
]


def _keyword_fallback(query: str) -> dict:
    ql = query.lower()

    symptoms = [s for s in _COMMON_SYMPTOMS if s in ql]

    for pattern, symptom_name in _NATURAL_LANGUAGE_MAPPING.items():
        if pattern in ql and symptom_name not in symptoms:
            symptoms.append(symptom_name)

    for body_part, symptom_name in _BODY_PART_SYMPTOMS.items():
        if body_part in ql and symptom_name not in symptoms:
            if any(w in ql for w in ["pain", "ache", "hurt", "hurts", "sore", "sting", "throb", "bleeding", "bleed", "blood"]):
                symptoms.append(symptom_name)

    severity = None
    for level, words in _SEVERITY_WORDS.items():
        if any(w in ql for w in words):
            severity = level
            break

    duration = None
    for singular, plural in _DURATION_PATTERNS:
        for unit in (singular, plural):
            if unit in ql:
                words = ql.split()
                for i, w in enumerate(words):
                    if w == unit and i > 0 and words[i - 1].isdigit():
                        duration = f"{words[i-1]} {unit}"
                        break
                if not duration and unit in ql:
                    duration = f"a few {plural}"
                break
        if duration:
            break

    return {
        "symptoms":     symptoms,
        "duration":     duration,
        "severity":     severity,
        "search_terms": symptoms[:3] if symptoms else [query[:60]],
    }

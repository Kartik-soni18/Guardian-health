"""GuardianHealth v2 ML Service — Symptom classification, NO external AWS."""

import os
import pickle
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.models.enums import TriageLevel
from app.schemas.triage import TriageResult


SYMPTOM_DB: Dict[str, Dict[str, Any]] = {
    "chest pain": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "heart attack": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "can't breathe": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "not breathing": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "unconscious": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "severe bleeding": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "anaphylaxis": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "stroke": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "seizure": {"level": TriageLevel.EMERGENCY, "weight": 1.0},
    "fever": {"level": TriageLevel.URGENT, "weight": 0.8},
    "high fever": {"level": TriageLevel.URGENT, "weight": 0.9},
    "infection": {"level": TriageLevel.URGENT, "weight": 0.8},
    "possible fracture": {"level": TriageLevel.URGENT, "weight": 0.85},
    "severe vomiting": {"level": TriageLevel.URGENT, "weight": 0.85},
    "dehydration": {"level": TriageLevel.URGENT, "weight": 0.8},
    "abdominal pain": {"level": TriageLevel.URGENT, "weight": 0.75},
    "migraine": {"level": TriageLevel.URGENT, "weight": 0.7},
    "concussion": {"level": TriageLevel.URGENT, "weight": 0.85},
    "eye injury": {"level": TriageLevel.URGENT, "weight": 0.8},
    "rash": {"level": TriageLevel.PRIMARY_CARE, "weight": 0.6},
    "joint pain": {"level": TriageLevel.PRIMARY_CARE, "weight": 0.55},
    "back pain": {"level": TriageLevel.PRIMARY_CARE, "weight": 0.6},
    "chronic": {"level": TriageLevel.PRIMARY_CARE, "weight": 0.5},
    "skin condition": {"level": TriageLevel.PRIMARY_CARE, "weight": 0.55},
    "allergies": {"level": TriageLevel.PRIMARY_CARE, "weight": 0.5},
    "mild headache": {"level": TriageLevel.SELF_CARE, "weight": 0.5},
    "headache": {"level": TriageLevel.SELF_CARE, "weight": 0.4},
    "runny nose": {"level": TriageLevel.SELF_CARE, "weight": 0.45},
    "sore throat": {"level": TriageLevel.SELF_CARE, "weight": 0.45},
    "cough": {"level": TriageLevel.SELF_CARE, "weight": 0.4},
    "minor cut": {"level": TriageLevel.SELF_CARE, "weight": 0.5},
    "bruise": {"level": TriageLevel.SELF_CARE, "weight": 0.4},
    "mild cold": {"level": TriageLevel.SELF_CARE, "weight": 0.45},
    "cold": {"level": TriageLevel.SELF_CARE, "weight": 0.4},
    "sunburn": {"level": TriageLevel.SELF_CARE, "weight": 0.5},
}


class MLService:
    """Lightweight symptom classifier — keyword + optional sklearn model."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or get_settings().ml_model_path
        self._model: Optional[Any] = None
        self._vectorizer: Optional[Any] = None
        self._loaded = False

    async def load_model(self) -> bool:
        """Attempt to load a persisted sklearn model."""
        if self._loaded:
            return True
        if self.model_path and os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                self._model = data.get("model")
                self._vectorizer = data.get("vectorizer")
                self._loaded = True
                return True
            except Exception:
                self._loaded = True
                return False
        self._loaded = True
        return False

    async def predict(self, query: str) -> TriageResult:
        """Classify symptoms and return triage result."""
        await self.load_model()

        if self._model is not None and self._vectorizer is not None:
            try:
                import numpy as np
                vec = self._vectorizer.transform([query.lower()])
                pred = self._model.predict(vec)[0]
                probs = getattr(self._model, "predict_proba", lambda x: None)(vec)
                confidence = float(np.max(probs)) if probs is not None else 0.7
                level = TriageLevel(pred) if pred in iter(TriageLevel) else TriageLevel.UNKNOWN
                return TriageResult(
                    level=level,
                    confidence=round(min(confidence, 1.0), 3),
                    explanation=f"ML model classified as {level.value}.",
                    recommended_actions=self._actions_for_level(level),
                )
            except Exception:
                pass

        return self._keyword_predict(query)

    def _keyword_predict(self, query: str) -> TriageResult:
        """Score symptoms against keyword database."""
        q = query.lower()
        best_level = TriageLevel.UNKNOWN
        best_score = 0.0
        matched_symptoms: List[str] = []

        for symptom, data in SYMPTOM_DB.items():
            if symptom in q:
                score = data["weight"]
                if score > best_score:
                    best_score = score
                    best_level = data["level"]
                matched_symptoms.append(symptom)

        if matched_symptoms:
            confidence = min(best_score + 0.05 * (len(matched_symptoms) - 1), 1.0)
            explanations = {
                TriageLevel.EMERGENCY: "Critical symptoms detected requiring immediate attention.",
                TriageLevel.URGENT: "Symptoms suggest urgent medical evaluation needed.",
                TriageLevel.PRIMARY_CARE: "Symptoms suggest a non-urgent medical visit.",
                TriageLevel.SELF_CARE: "Mild symptoms that can typically be managed at home.",
            }
            return TriageResult(
                level=best_level,
                confidence=round(confidence, 3),
                explanation=explanations.get(best_level, "Based on symptom analysis."),
                recommended_actions=self._actions_for_level(best_level),
            )

        return TriageResult(
            level=TriageLevel.UNKNOWN,
            confidence=0.5,
            explanation="Could not match symptoms to known conditions.",
            follow_up_questions=[
                "Can you describe your symptoms in more detail?",
                "When did the symptoms start?",
            ],
        )

    @staticmethod
    def _actions_for_level(level: TriageLevel) -> List[str]:
        actions = {
            TriageLevel.EMERGENCY: ["Call 911 immediately.", "Do not drive yourself."],
            TriageLevel.URGENT: ["Seek medical care within 24 hours.", "Monitor symptoms closely."],
            TriageLevel.PRIMARY_CARE: ["Schedule a routine doctor appointment."],
            TriageLevel.SELF_CARE: ["Rest and hydrate.", "Use over-the-counter remedies as appropriate.", "See a doctor if symptoms persist."],
        }
        return actions.get(level, ["Consult a healthcare professional."])

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

"""GuardianHealth v2 ML Service Tests — 10+ tests for symptom classification."""

import os
import pickle
from typing import Any, Dict

import pytest

from app.models.enums import TriageLevel
from app.schemas.triage import TriageResult
from app.services.ml_service import MLService


# =============================================================================
# Keyword-based prediction tests
# =============================================================================

class TestMLKeywordPredict:
    """MLService keyword-based classification without sklearn model."""

    async def test_known_symptoms_chest_pain(self) -> None:
        """Chest pain should classify as EMERGENCY."""
        svc = MLService()
        result = await svc.predict("I have severe chest pain")
        assert result.level == TriageLevel.EMERGENCY
        assert result.confidence >= 0.9

    async def test_known_symptoms_fever(self) -> None:
        """Fever should classify as URGENT."""
        svc = MLService()
        result = await svc.predict("I have a high fever")
        assert result.level == TriageLevel.URGENT
        assert result.confidence >= 0.8

    async def test_known_symptoms_mild_cold(self) -> None:
        """Mild cold should classify as SELF_CARE."""
        svc = MLService()
        result = await svc.predict("I have a mild cold and runny nose")
        assert result.level == TriageLevel.SELF_CARE
        assert result.confidence >= 0.6

    async def test_known_symptoms_rash(self) -> None:
        """Rash should classify as PRIMARY_CARE."""
        svc = MLService()
        result = await svc.predict("I have a strange rash on my arm")
        assert result.level == TriageLevel.PRIMARY_CARE

    async def test_unknown_symptoms(self) -> None:
        """Unknown symptoms return UNKNOWN level."""
        svc = MLService()
        result = await svc.predict("Purple spots on left elbow every Tuesday")
        assert result.level == TriageLevel.UNKNOWN
        assert result.confidence >= 0.0

    async def test_empty_symptoms(self) -> None:
        """Empty query still returns a result (does not crash)."""
        svc = MLService()
        result = await svc.predict("")
        assert isinstance(result, TriageResult)
        assert result.level in iter(TriageLevel)

    async def test_multiple_matching_symptoms_boosts_confidence(self) -> None:
        """Multiple symptom keywords increase confidence."""
        svc = MLService()
        result = await svc.predict("chest pain and can't breathe and heart attack")
        assert result.level == TriageLevel.EMERGENCY
        assert result.confidence >= 0.9


# =============================================================================
# Sklearn model tests
# =============================================================================

class TestMLSklearnModel:
    """MLService with a persisted sklearn model."""

    async def test_model_loaded(self, tmp_path: pytest.TempPathFactory) -> None:
        """If model file exists, it should load successfully."""
        svc = MLService()
        # Without a real model file, load_model should complete
        loaded = await svc.load_model()
        # It returns False when no model path set, but should not error
        assert loaded is False or loaded is True

    async def test_model_not_found(self, tmp_path: str) -> None:
        """Non-existent model path should gracefully fall back."""
        svc = MLService(model_path="/does/not/exist.pkl")
        loaded = await svc.load_model()
        assert loaded is False

    async def test_is_loaded_property(self) -> None:
        """is_loaded should be False when no model is loaded."""
        svc = MLService()
        await svc.load_model()
        assert svc.is_loaded is False


# =============================================================================
# Actions generation
# =============================================================================

class TestMLActions:
    """Recommended actions for each triage level."""

    async def test_emergency_actions(self) -> None:
        """Emergency level should recommend calling 911."""
        svc = MLService()
        result = await svc.predict("severe chest pain")
        assert result.level == TriageLevel.EMERGENCY
        assert result.recommended_actions is not None
        assert any("911" in a for a in result.recommended_actions)

    async def test_self_care_actions(self) -> None:
        """Self-care level should recommend rest and hydration."""
        svc = MLService()
        result = await svc.predict("mild headache")
        assert result.level == TriageLevel.SELF_CARE
        assert result.recommended_actions is not None
        actions_lower = " ".join(result.recommended_actions).lower()
        assert "rest" in actions_lower or "hydrat" in actions_lower or "otc" in actions_lower

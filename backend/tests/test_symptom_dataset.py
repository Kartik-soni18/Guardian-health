"""Tests for Indian healthcare symptom dataset lookup."""

import pytest

from app.services.symptom_dataset import get_symptom_dataset, lookup_symptoms


@pytest.mark.asyncio
async def test_lookup_fever():
    result = await lookup_symptoms(["fever"])
    assert result["matches"]
    assert result["top_predictions"]
    assert result["confidence"] > 0
    assert result["source"] == "indian_healthcare_dataset"


@pytest.mark.asyncio
async def test_lookup_multiple_symptoms():
    result = await lookup_symptoms(["fever", "joint pain"])
    diseases = {p["condition"] for p in result["top_predictions"]}
    assert diseases


def test_dataset_loads_records():
    dataset = get_symptom_dataset()
    assert len(dataset._records) > 100

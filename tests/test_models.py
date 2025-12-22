"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from app.models import (
    IntakeOutput,
    Patient,
    Symptom,
    TriageOutput,
    CareType,
)


class TestIntakeModels:
    """Test intake model validation."""
    
    def test_confidence_must_be_between_0_and_1(self):
        """Confidence score must be in valid range."""
        with pytest.raises(ValidationError):
            IntakeOutput(
                patient=Patient(),
                symptoms=[],
                confidence=1.5  # Invalid: > 1.0
            )
    
    def test_patient_age_must_be_reasonable(self):
        """Patient age must be within valid range."""
        with pytest.raises(ValidationError):
            Patient(age=200)  # Invalid: > 150
    
    def test_valid_intake_output(self):
        """Valid intake output should pass validation."""
        output = IntakeOutput(
            patient=Patient(name="John Doe", age=45),
            symptoms=[Symptom(description="chest pain", duration="2 days")],
            medical_history=["hypertension"],
            confidence=0.85
        )
        assert output.confidence == 0.85
        assert output.patient.name == "John Doe"


class TestTriageModels:
    """Test triage model validation."""
    
    def test_urgency_level_must_be_1_to_5(self):
        """Urgency level must be within valid range."""
        with pytest.raises(ValidationError):
            TriageOutput(
                urgency_level=6,  # Invalid: > 5
                urgency_reasoning="test",
                recommended_specialty="cardiology",
                recommended_care_type=CareType.URGENT_CARE,
                confidence=0.9
            )
    
    def test_valid_triage_output(self):
        """Valid triage output should pass validation."""
        output = TriageOutput(
            urgency_level=2,
            urgency_reasoning="Chest pain with cardiac history",
            recommended_specialty="cardiology",
            recommended_care_type=CareType.URGENT_CARE,
            red_flags=["chest pain"],
            confidence=0.9
        )
        assert output.urgency_level == 2
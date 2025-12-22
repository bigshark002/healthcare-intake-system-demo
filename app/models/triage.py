"""Triage agent models - Classify urgency and determine specialty."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class UrgencyLevel(int, Enum):
    """Urgency classification levels."""
    
    EMERGENCY = 1       # Immediate attention required
    URGENT = 2          # Same-day attention needed
    SEMI_URGENT = 3     # Within 24-48 hours
    ROUTINE = 4         # Within a week
    PREVENTIVE = 5      # Scheduled preventive care


class CareType(str, Enum):
    """Type of care recommended."""
    
    EMERGENCY = "emergency"
    URGENT_CARE = "urgent_care"
    IN_PERSON = "in_person"
    TELEHEALTH = "telehealth"
    ROUTINE = "routine"


class TriageInput(BaseModel):
    """Input to triage agent - output from intake."""
    
    patient: "Patient"  # Forward reference
    symptoms: list["Symptom"]
    medical_history: list[str]
    current_medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class TriageOutput(BaseModel):
    """Triage classification result."""
    
    urgency_level: int = Field(..., ge=1, le=5, description="1=Emergency, 5=Routine")
    urgency_reasoning: str = Field(..., description="Explanation for urgency classification")
    recommended_specialty: str = Field(..., description="Medical specialty needed")
    recommended_care_type: CareType
    red_flags: list[str] = Field(default_factory=list, description="Critical symptoms identified")
    confidence: float = Field(..., ge=0.0, le=1.0)
    fallback_used: bool = Field(default=False, description="True if rule-based fallback was used")


# Update forward references
from app.models.intake import Patient, Symptom
TriageInput.model_rebuild()
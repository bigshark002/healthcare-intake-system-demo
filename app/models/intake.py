"""Intake agent models - Extract patient information from raw input."""

from pydantic import BaseModel, Field
from typing import Optional


class Symptom(BaseModel):
    """Individual symptom reported by patient."""
    
    description: str = Field(..., description="Symptom description")
    duration: Optional[str] = Field(None, description="How long symptom has persisted")
    severity: Optional[str] = Field(None, description="Severity level if mentioned")
    modifiers: list[str] = Field(default_factory=list, description="Additional details")


class Patient(BaseModel):
    """Patient demographic information."""
    
    name: Optional[str] = Field(None, description="Patient full name")
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")


class IntakeInput(BaseModel):
    """Input to the intake agent."""
    
    raw_input: str = Field(..., description="Raw patient input text")


class IntakeOutput(BaseModel):
    """Structured output from intake agent."""
    
    patient: Patient
    symptoms: list[Symptom] = Field(default_factory=list)
    medical_history: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list, description="Information that would be useful but wasn't provided")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in extraction accuracy")
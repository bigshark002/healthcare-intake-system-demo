"""Routing agent models - Match patient to appropriate provider."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TimeSlot(BaseModel):
    """Available appointment slot."""
    
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format")
    slot_type: str = Field(..., description="in_person or telehealth")


class Provider(BaseModel):
    """Healthcare provider information."""
    
    id: str
    name: str
    specialty: str
    location: str
    languages: list[str] = Field(default_factory=list)
    accepting_new_patients: bool = True


class RoutingInput(BaseModel):
    """Input to routing agent."""
    
    patient: "Patient"
    triage: "TriageOutput"
    available_providers: list[Provider]


class RoutingOutput(BaseModel):
    """Provider matching result."""
    
    recommended_provider: Provider
    available_slots: list[TimeSlot]
    routing_reasoning: str = Field(..., description="Why this provider was selected")
    alternative_providers: list[Provider] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


# Update forward references
from app.models.intake import Patient
from app.models.triage import TriageOutput
RoutingInput.model_rebuild()
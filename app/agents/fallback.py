"""Rule-based fallback logic when LLM is unavailable."""

from app.models import TriageOutput, CareType


# Keywords that indicate emergency
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "difficulty breathing",
    "unconscious", "severe bleeding", "stroke", "paralysis",
    "suicidal", "overdose", "poisoning"
]

# Keywords that indicate urgent care
URGENT_KEYWORDS = [
    "high fever", "severe pain", "vomiting blood", "broken bone",
    "deep cut", "head injury", "allergic reaction"
]

# Specialty mapping by symptom keywords
SPECIALTY_MAP = {
    "chest": "cardiology",
    "heart": "cardiology",
    "breathing": "pulmonology",
    "lung": "pulmonology",
    "stomach": "gastroenterology",
    "digestive": "gastroenterology",
    "skin": "dermatology",
    "rash": "dermatology",
    "bone": "orthopedics",
    "joint": "orthopedics",
    "head": "neurology",
    "headache": "neurology",
    "mental": "psychiatry",
    "anxiety": "psychiatry",
    "depression": "psychiatry",
}


def rule_based_triage(symptoms: list[str], medical_history: list[str]) -> TriageOutput:
    """
    Fallback triage using simple keyword matching.
    
    Used when Bedrock/LLM is unavailable. Always marks requires_human_review=True.
    """
    symptoms_text = " ".join(symptoms).lower()
    history_text = " ".join(medical_history).lower()
    combined_text = f"{symptoms_text} {history_text}"
    
    # Check for emergency keywords
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in combined_text:
            return TriageOutput(
                urgency_level=1,
                urgency_reasoning=f"Rule-based fallback: Emergency keyword detected '{keyword}'",
                recommended_specialty="emergency_medicine",
                recommended_care_type=CareType.EMERGENCY,
                red_flags=[keyword],
                confidence=0.5,  # Low confidence for fallback
                fallback_used=True
            )
    
    # Check for urgent keywords
    for keyword in URGENT_KEYWORDS:
        if keyword in combined_text:
            return TriageOutput(
                urgency_level=2,
                urgency_reasoning=f"Rule-based fallback: Urgent keyword detected '{keyword}'",
                recommended_specialty="general_practice",
                recommended_care_type=CareType.URGENT_CARE,
                red_flags=[keyword],
                confidence=0.5,
                fallback_used=True
            )
    
    # Determine specialty from symptoms
    specialty = "general_practice"
    for keyword, spec in SPECIALTY_MAP.items():
        if keyword in combined_text:
            specialty = spec
            break
    
    # Default to routine care
    return TriageOutput(
        urgency_level=3,
        urgency_reasoning="Rule-based fallback: No urgent keywords detected, defaulting to semi-urgent",
        recommended_specialty=specialty,
        recommended_care_type=CareType.IN_PERSON,
        red_flags=[],
        confidence=0.4,
        fallback_used=True
    )
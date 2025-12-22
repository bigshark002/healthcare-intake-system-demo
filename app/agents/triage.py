"""Triage agent - Classifies urgency and determines specialty."""

import json

try:
    from strands import tool
    from aws_lambda_powertools import Logger, Tracer
except ImportError:
    # Mock for local development
    from app.mock_dependencies import tool, MockLogger as Logger, MockTracer as Tracer

from app.models import TriageInput, TriageOutput
from app.agents.prompts import TRIAGE_AGENT_PROMPT
from app.agents.fallback import rule_based_triage
from app.config import settings

logger = Logger(child=True)
tracer = Tracer()


@tool
def triage_agent(patient_data: dict) -> dict:
    """
    Assess urgency and determine appropriate specialty based on patient data.
    
    Args:
        patient_data: Structured patient info from intake agent
        
    Returns:
        Dictionary with urgency level, specialty, care type, and confidence
    """
    logger.info("Triage agent started")
    
    return {
        "instruction": TRIAGE_AGENT_PROMPT,
        "input": patient_data,
        "expected_output": "TriageOutput JSON"
    }


def parse_triage_response(response: str) -> TriageOutput:
    """Parse LLM response into validated TriageOutput."""
    try:
        data = json.loads(response)
        return TriageOutput(**data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse triage response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")
    except Exception as e:
        logger.error(f"Failed to validate triage response: {e}")
        raise ValueError(f"Validation error: {e}")
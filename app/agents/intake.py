"""Intake agent - Extracts patient information from raw input."""

import json
from strands import tool
from aws_lambda_powertools import Logger, Tracer

from app.models import IntakeInput, IntakeOutput, Patient, Symptom
from app.agents.prompts import INTAKE_AGENT_PROMPT
from app.config import settings

logger = Logger(child=True)
tracer = Tracer()


@tool
def intake_agent(raw_input: str) -> dict:
    """
    Extract structured patient information from natural language input.
    
    Args:
        raw_input: Free-form text from patient describing their situation
        
    Returns:
        Dictionary with patient info, symptoms, history, and confidence score
    """
    logger.info("Intake agent started", extra={"input_length": len(raw_input)})
    
    # The agent will be called by the orchestrator which has access to Bedrock
    # This tool definition tells Strands what this agent does
    # The actual LLM call happens through the orchestrator's model
    
    # Return format that the LLM should produce
    return {
        "instruction": INTAKE_AGENT_PROMPT,
        "input": raw_input,
        "expected_output": "IntakeOutput JSON"
    }


def parse_intake_response(response: str) -> IntakeOutput:
    """Parse LLM response into validated IntakeOutput."""
    try:
        data = json.loads(response)
        return IntakeOutput(**data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse intake response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")
    except Exception as e:
        logger.error(f"Failed to validate intake response: {e}")
        raise ValueError(f"Validation error: {e}")
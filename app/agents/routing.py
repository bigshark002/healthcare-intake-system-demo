"""Routing agent - Matches patient with appropriate provider."""

import json
from strands import tool
from aws_lambda_powertools import Logger, Tracer

from app.models import RoutingInput, RoutingOutput
from app.agents.prompts import ROUTING_AGENT_PROMPT

logger = Logger(child=True)
tracer = Tracer()


@tool
def routing_agent(triage_data: dict, available_providers: list[dict]) -> dict:
    """
    Match patient with the most appropriate available provider.
    
    Args:
        triage_data: Triage results including urgency and specialty
        available_providers: List of available providers with their details
        
    Returns:
        Dictionary with recommended provider, slots, and reasoning
    """
    logger.info("Routing agent started", extra={"provider_count": len(available_providers)})
    
    return {
        "instruction": ROUTING_AGENT_PROMPT,
        "input": {
            "triage": triage_data,
            "providers": available_providers
        },
        "expected_output": "RoutingOutput JSON"
    }


def parse_routing_response(response: str) -> RoutingOutput:
    """Parse LLM response into validated RoutingOutput."""
    try:
        data = json.loads(response)
        return RoutingOutput(**data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse routing response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")
    except Exception as e:
        logger.error(f"Failed to validate routing response: {e}")
        raise ValueError(f"Validation error: {e}")
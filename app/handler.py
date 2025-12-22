"""AWS Lambda handler for the healthcare multi-agent system."""

import json

try:
    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools.logging import correlation_paths
except ImportError:
    # Mock for local development
    from app.mock_dependencies import LambdaContext
    
    class correlation_paths:
        API_GATEWAY_HTTP = "requestContext.requestId"

from app.agents.orchestrator import HealthcareOrchestrator
from app.observability import logger, tracer, metrics


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """
    Lambda handler for processing healthcare intake requests.
    
    Expected event body:
    {
        "patient_input": "I'm having chest pain..."
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        patient_input = body.get("patient_input", "")
        
        if not patient_input:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "patient_input is required"})
            }
        
        # Process the case
        orchestrator = HealthcareOrchestrator()
        result = orchestrator.process_case(patient_input)
        
        # Return response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(result.model_dump(), default=str)
        }
        
    except Exception as e:
        logger.exception("Handler error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
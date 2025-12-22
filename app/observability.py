"""Centralized observability setup using AWS Lambda Powertools."""

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Initialize Powertools
logger = Logger(service="healthcare-mas")
tracer = Tracer(service="healthcare-mas")
metrics = Metrics(namespace="HealthcareMAS", service="healthcare-mas")


def publish_agent_metrics(
    agent_name: str,
    duration_ms: float,
    confidence: float,
    success: bool,
    tokens_used: int = 0
):
    """Publish metrics for agent execution."""
    metrics.add_dimension(name="agent", value=agent_name)
    metrics.add_metric(name="Duration", unit=MetricUnit.Milliseconds, value=duration_ms)
    metrics.add_metric(name="Confidence", unit=MetricUnit.NoUnit, value=confidence)
    metrics.add_metric(name="Success", unit=MetricUnit.Count, value=1 if success else 0)
    if not success:
        metrics.add_metric(name="Errors", unit=MetricUnit.Count, value=1)
    if tokens_used > 0:
        metrics.add_metric(name="TokensUsed", unit=MetricUnit.Count, value=tokens_used)


def publish_case_metrics(
    total_duration_ms: float,
    urgency_level: int,
    requires_human_review: bool,
    estimated_cost_usd: float
):
    """Publish metrics for completed case."""
    metrics.add_metric(name="CaseDuration", unit=MetricUnit.Milliseconds, value=total_duration_ms)
    metrics.add_metric(name="UrgencyLevel", unit=MetricUnit.NoUnit, value=urgency_level)
    metrics.add_metric(name="HumanReviewRequired", unit=MetricUnit.Count, value=1 if requires_human_review else 0)
    metrics.add_metric(name="EstimatedCostUSD", unit=MetricUnit.NoUnit, value=estimated_cost_usd)
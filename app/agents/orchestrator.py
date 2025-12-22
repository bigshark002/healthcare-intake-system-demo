"""Orchestrator agent - Coordinates the multi-agent workflow."""

import json
import time
import uuid
from pathlib import Path
from strands import Agent
from aws_lambda_powertools import Logger, Tracer

from app.config import settings
from app.models import (
    CaseResult,
    AgentTrace,
    IntakeOutput,
    TriageOutput,
    RoutingOutput,
)
from app.agents.prompts import (
    ORCHESTRATOR_PROMPT,
    INTAKE_AGENT_PROMPT,
    TRIAGE_AGENT_PROMPT,
    ROUTING_AGENT_PROMPT,
)
from app.agents.fallback import rule_based_triage
from app.observability import (
    logger,
    tracer,
    metrics,
    publish_agent_metrics,
    publish_case_metrics,
)

# Load provider data
PROVIDERS_PATH = Path(__file__).parent.parent / "data" / "providers.json"


def load_providers() -> list[dict]:
    """Load mock provider data."""
    with open(PROVIDERS_PATH) as f:
        return json.load(f)


def determine_human_review(
    intake: IntakeOutput,
    triage: TriageOutput,
    routing: RoutingOutput
) -> tuple[bool, list[str]]:
    """Determine if case requires human review."""
    reasons = []
    
    # High urgency
    if triage.urgency_level <= settings.human_review_urgency_threshold:
        reasons.append(f"High urgency level: {triage.urgency_level}")
    
    # Low confidence in any agent
    if intake.confidence < settings.confidence_threshold:
        reasons.append(f"Low intake confidence: {intake.confidence:.2f}")
    
    if triage.confidence < settings.confidence_threshold:
        reasons.append(f"Low triage confidence: {triage.confidence:.2f}")
    
    if routing.confidence < settings.confidence_threshold:
        reasons.append(f"Low routing confidence: {routing.confidence:.2f}")
    
    # Fallback was used
    if triage.fallback_used:
        reasons.append("Rule-based fallback was used - LLM unavailable")
    
    # Red flags present
    if triage.red_flags:
        reasons.append(f"Red flags detected: {', '.join(triage.red_flags)}")
    
    return len(reasons) > 0, reasons


class HealthcareOrchestrator:
    """Orchestrates the healthcare intake multi-agent workflow."""
    
    def __init__(self):
        self.providers = load_providers()
        self.agent = Agent(
            system_prompt=ORCHESTRATOR_PROMPT,
            # Tools would be registered here in full implementation
        )
    
    @tracer.capture_method
    def process_case(self, raw_input: str) -> CaseResult:
        """
        Process a patient intake case through the multi-agent pipeline.
        
        Args:
            raw_input: Natural language input from patient
            
        Returns:
            CaseResult with complete processing results and audit trail
        """
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.perf_counter()
        audit_trail = []
        
        logger.info("Processing case", extra={"case_id": case_id})
        
        try:
            # Phase 1: Intake
            intake_result, intake_trace = self._run_intake(raw_input)
            audit_trail.append(intake_trace)
            
            # Phase 2: Triage
            triage_result, triage_trace = self._run_triage(intake_result)
            audit_trail.append(triage_trace)
            
            # Phase 3: Routing
            routing_result, routing_trace = self._run_routing(
                intake_result, 
                triage_result
            )
            audit_trail.append(routing_trace)
            
            # Determine human review
            requires_review, review_reasons = determine_human_review(
                intake_result,
                triage_result,
                routing_result
            )
            
            # Calculate totals
            total_duration = (time.perf_counter() - start_time) * 1000
            estimated_cost = self._estimate_cost(audit_trail)
            
            # Publish metrics
            publish_case_metrics(
                total_duration_ms=total_duration,
                urgency_level=triage_result.urgency_level,
                requires_human_review=requires_review,
                estimated_cost_usd=estimated_cost
            )
            
            return CaseResult(
                case_id=case_id,
                status="completed",
                intake=intake_result,
                triage=triage_result,
                routing=routing_result,
                audit_trail=audit_trail,
                total_duration_ms=total_duration,
                estimated_cost_usd=estimated_cost,
                requires_human_review=requires_review,
                review_reasons=review_reasons
            )
            
        except Exception as e:
            logger.exception("Case processing failed")
            total_duration = (time.perf_counter() - start_time) * 1000
            
            return CaseResult(
                case_id=case_id,
                status="failed",
                audit_trail=audit_trail,
                total_duration_ms=total_duration,
                error=str(e)
            )
    
    def _run_intake(self, raw_input: str) -> tuple[IntakeOutput, AgentTrace]:
        """Run intake agent."""
        start = time.perf_counter()
        
        try:
            # Here would be actual Strands agent call
            # For now, simulating the structure
            logger.info("Running intake agent")
            
            # This would be replaced with actual agent call:
            # result = self.agent.invoke(raw_input, tools=[intake_agent])
            
            # Placeholder - in real implementation, parse LLM response
            duration_ms = (time.perf_counter() - start) * 1000
            
            trace = AgentTrace(
                agent_name="intake",
                duration_ms=duration_ms,
                confidence=0.85,  # Would come from actual response
                success=True
            )
            
            publish_agent_metrics("intake", duration_ms, 0.85, True)
            
            # Return placeholder - actual implementation parses LLM response
            return IntakeOutput(
                patient={"name": None, "age": None, "gender": None},
                symptoms=[],
                confidence=0.85
            ), trace
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            trace = AgentTrace(
                agent_name="intake",
                duration_ms=duration_ms,
                confidence=0.0,
                success=False,
                error=str(e)
            )
            publish_agent_metrics("intake", duration_ms, 0.0, False)
            raise
    
    def _run_triage(self, intake: IntakeOutput) -> tuple[TriageOutput, AgentTrace]:
        """Run triage agent with fallback."""
        start = time.perf_counter()
        
        try:
            logger.info("Running triage agent")
            
            # Actual implementation would call LLM
            # On failure, use fallback
            duration_ms = (time.perf_counter() - start) * 1000
            
            trace = AgentTrace(
                agent_name="triage",
                duration_ms=duration_ms,
                confidence=0.90,
                success=True
            )
            
            publish_agent_metrics("triage", duration_ms, 0.90, True)
            
            # Placeholder
            return TriageOutput(
                urgency_level=3,
                urgency_reasoning="Placeholder",
                recommended_specialty="general_practice",
                recommended_care_type="in_person",
                confidence=0.90
            ), trace
            
        except Exception as e:
            logger.warning(f"Triage LLM failed, using fallback: {e}")
            
            if settings.enable_fallback:
                # Use rule-based fallback
                symptoms = [s.description for s in intake.symptoms]
                fallback_result = rule_based_triage(symptoms, intake.medical_history)
                
                duration_ms = (time.perf_counter() - start) * 1000
                trace = AgentTrace(
                    agent_name="triage",
                    duration_ms=duration_ms,
                    confidence=fallback_result.confidence,
                    success=True,
                    fallback_used=True
                )
                
                publish_agent_metrics("triage", duration_ms, fallback_result.confidence, True)
                return fallback_result, trace
            else:
                raise
    
    def _run_routing(
        self, 
        intake: IntakeOutput, 
        triage: TriageOutput
    ) -> tuple[RoutingOutput, AgentTrace]:
        """Run routing agent."""
        start = time.perf_counter()
        
        try:
            logger.info("Running routing agent")
            
            # Filter providers by specialty
            matching_providers = [
                p for p in self.providers 
                if p["specialty"] == triage.recommended_specialty
            ]
            
            # If no specialty match, include general practice
            if not matching_providers:
                matching_providers = [
                    p for p in self.providers
                    if p["specialty"] == "general_practice"
                ]
            
            duration_ms = (time.perf_counter() - start) * 1000
            
            trace = AgentTrace(
                agent_name="routing",
                duration_ms=duration_ms,
                confidence=0.88,
                success=True
            )
            
            publish_agent_metrics("routing", duration_ms, 0.88, True)
            
            # Placeholder
            return RoutingOutput(
                recommended_provider=matching_providers[0] if matching_providers else self.providers[0],
                available_slots=[],
                routing_reasoning="Placeholder",
                confidence=0.88
            ), trace
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            trace = AgentTrace(
                agent_name="routing",
                duration_ms=duration_ms,
                confidence=0.0,
                success=False,
                error=str(e)
            )
            publish_agent_metrics("routing", duration_ms, 0.0, False)
            raise
    
    def _estimate_cost(self, traces: list[AgentTrace]) -> float:
        """Estimate USD cost based on token usage."""
        # Claude Sonnet pricing (approximate)
        # Input: $3/M tokens, Output: $15/M tokens
        # Assuming ~500 input, ~200 output per agent call
        tokens_per_agent = 700
        cost_per_1k_tokens = 0.009  # Blended rate
        
        total_tokens = len(traces) * tokens_per_agent
        return (total_tokens / 1000) * cost_per_1k_tokens
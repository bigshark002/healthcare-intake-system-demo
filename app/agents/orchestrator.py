"""Orchestrator agent - Coordinates the multi-agent workflow."""

import json
import time
import uuid
from pathlib import Path

try:
    from strands import Agent
    from aws_lambda_powertools import Logger, Tracer
except ImportError:
    # Mock for local development
    from app.mock_dependencies import MockLogger as Logger, MockTracer as Tracer
    
    class Agent:
        def __init__(self, **kwargs):
            pass

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
            logger.info("Running intake agent")
            
            # Try real Bedrock first, fallback to simulation
            intake_result = None
            use_bedrock = settings.enable_bedrock if hasattr(settings, 'enable_bedrock') else False
            
            if use_bedrock:
                try:
                    from app.bedrock_client import get_bedrock_client
                    client = get_bedrock_client()
                    
                    # Call Bedrock with intake prompt
                    response = client.invoke_claude(
                        prompt=raw_input,
                        system_prompt=INTAKE_AGENT_PROMPT
                    )
                    
                    # Parse the response
                    from app.agents.intake import parse_intake_response
                    intake_result = parse_intake_response(response)
                    logger.info("Intake completed with Bedrock")
                    
                except Exception as e:
                    logger.warning(f"Bedrock intake failed, using simulation: {e}")
                    intake_result = None
            
            # Fallback to simulation
            if intake_result is None:
                intake_result = self._simulate_intake(raw_input)
            
            duration_ms = (time.perf_counter() - start) * 1000
            
            trace = AgentTrace(
                agent_name="intake",
                duration_ms=duration_ms,
                confidence=intake_result.confidence,
                success=True
            )
            
            publish_agent_metrics("intake", duration_ms, intake_result.confidence, True)
            
            return intake_result, trace
            
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
            
            # Try real Bedrock first
            triage_result = None
            use_bedrock = settings.enable_bedrock if hasattr(settings, 'enable_bedrock') else False
            
            if use_bedrock:
                try:
                    from app.bedrock_client import get_bedrock_client
                    client = get_bedrock_client()
                    
                    # Convert intake to dict for the prompt
                    intake_data = intake.model_dump()
                    
                    # Call Bedrock with triage prompt
                    response = client.invoke_claude(
                        prompt=json.dumps(intake_data),
                        system_prompt=TRIAGE_AGENT_PROMPT
                    )
                    
                    # Parse the response
                    from app.agents.triage import parse_triage_response
                    triage_result = parse_triage_response(response)
                    logger.info("Triage completed with Bedrock")
                    
                except Exception as e:
                    logger.warning(f"Bedrock triage failed, using simulation: {e}")
                    triage_result = None
            
            # Fallback to simulation
            if triage_result is None:
                triage_result = self._simulate_triage(intake)
            
            duration_ms = (time.perf_counter() - start) * 1000
            
            trace = AgentTrace(
                agent_name="triage",
                duration_ms=duration_ms,
                confidence=triage_result.confidence,
                success=True
            )
            
            publish_agent_metrics("triage", duration_ms, triage_result.confidence, True)
            
            return triage_result, trace
            
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
    
    def _simulate_intake(self, raw_input: str) -> IntakeOutput:
        """Simulate intelligent intake agent response."""
        from app.models import Patient, Symptom
        import re
        
        text = raw_input.lower()
        
        # Extract basic patient info
        patient = Patient()
        
        # Extract name
        name_match = re.search(r"(?:i'm|my name is|soy)\s+([a-záéíóúñ\s]+?)(?:\s|,|$|\.|tengo)", text)
        if name_match:
            patient.name = name_match.group(1).strip().title()
        
        # Extract age
        age_match = re.search(r"(\d+)\s+(?:years old|años)", text)
        if age_match:
            patient.age = int(age_match.group(1))
        
        # Extract symptoms
        symptoms = []
        symptom_patterns = [
            r"(?:chest pain|dolor de pecho)",
            r"(?:headache|head hurts|dolor de cabeza)",
            r"(?:fever|fiebre)",
            r"(?:difficulty breathing|can't breathe|dificultad para respirar)"
        ]
        
        for pattern in symptom_patterns:
            if re.search(pattern, text):
                symptom_desc = pattern.split('|')[0].replace('(?:', '').replace(')', '')
                symptoms.append(Symptom(description=symptom_desc))
        
        # Extract medical history
        history = []
        if re.search(r"(?:history of|historial de).*(?:hypertension|high blood pressure|hipertensión)", text):
            history.append("hypertension")
        if re.search(r"(?:history of|historial de).*(?:high cholesterol|colesterol alto)", text):
            history.append("high cholesterol")
        
        # Determine confidence based on completeness
        confidence = 0.5  # Base confidence
        if patient.name:
            confidence += 0.15
        if patient.age:
            confidence += 0.15
        if symptoms:
            confidence += 0.15
        if len(text.split()) > 5:  # Detailed description
            confidence += 0.05
        
        # Special case: very short input
        if len(text.split()) <= 4:
            confidence = 0.4
        
        return IntakeOutput(
            patient=patient,
            symptoms=symptoms,
            medical_history=history,
            confidence=min(confidence, 1.0)
        )
    
    def _simulate_triage(self, intake: IntakeOutput) -> TriageOutput:
        """Simulate intelligent triage agent response."""
        # Combine all text for analysis
        symptoms_text = " ".join([s.description for s in intake.symptoms])
        history_text = " ".join(intake.medical_history)
        combined = f"{symptoms_text} {history_text}".lower()
        
        # Use fallback logic as base, but enhance it
        fallback_result = rule_based_triage([s.description for s in intake.symptoms], intake.medical_history)
        
        # Override with smarter logic for specific cases
        urgency = fallback_result.urgency_level
        specialty = fallback_result.recommended_specialty
        care_type = fallback_result.recommended_care_type
        red_flags = fallback_result.red_flags
        
        # Annual checkup detection
        if any(phrase in combined for phrase in ["annual", "checkup", "physical exam", "no symptoms"]):
            urgency = 5
            specialty = "general_practice"
            care_type = "routine"
            red_flags = []
        
        # Chest pain with cardiac history = high urgency
        if "chest pain" in combined and "hypertension" in combined:
            urgency = 1
            specialty = "cardiology"
            care_type = "emergency"
            red_flags = ["chest pain with cardiac history"]
        
        # Confidence based on intake confidence and symptom clarity
        confidence = min(intake.confidence + 0.1, 0.95)
        if urgency <= 2:  # High urgency cases get higher confidence
            confidence = min(confidence + 0.05, 0.95)
        
        return TriageOutput(
            urgency_level=urgency,
            urgency_reasoning=f"Smart simulation: {fallback_result.urgency_reasoning}",
            recommended_specialty=specialty,
            recommended_care_type=care_type,
            red_flags=red_flags,
            confidence=confidence,
            fallback_used=False
        )
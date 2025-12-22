"""Case result model - Final output combining all agent results."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.intake import IntakeOutput
from app.models.triage import TriageOutput
from app.models.routing import RoutingOutput


class AgentTrace(BaseModel):
    """Execution trace for a single agent."""
    
    agent_name: str
    duration_ms: float
    confidence: float
    success: bool
    error: Optional[str] = None
    fallback_used: bool = False


class CaseResult(BaseModel):
    """Complete case processing result with audit trail."""
    
    case_id: str = Field(..., description="Unique case identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(..., description="completed, failed, requires_review")
    
    # Agent outputs
    intake: Optional[IntakeOutput] = None
    triage: Optional[TriageOutput] = None
    routing: Optional[RoutingOutput] = None
    
    # Audit trail
    audit_trail: list[AgentTrace] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    
    # Human review
    requires_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    
    # Error handling
    error: Optional[str] = None
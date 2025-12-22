"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # AWS
    aws_region: str = "us-east-1"
    
    # Bedrock
    bedrock_model_id: str = "claude-model-placeholder"  # Configure via environment
    enable_bedrock: bool = False  # Set to True to use real Bedrock
    
    # Agent behavior
    confidence_threshold: float = 0.70
    human_review_urgency_threshold: int = 2
    enable_fallback: bool = True
    
    # Observability
    log_level: str = "INFO"
    service_name: str = "healthcare-mas"
    
    class Config:
        env_prefix = "HEALTHCARE_MAS_"
        env_file = ".env"


settings = Settings()
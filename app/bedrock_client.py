"""Bedrock client for real LLM calls."""

import json
import boto3
from typing import Optional

from app.config import settings


class BedrockClient:
    """Client for AWS Bedrock Claude API."""
    
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region
        )
        self.model_id = settings.bedrock_model_id
    
    def invoke_claude(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Invoke Claude model with a prompt.
        
        Args:
            prompt: User prompt/input
            system_prompt: Optional system prompt for context
            
        Returns:
            Model response as string
        """
        # Prepare the request body for Claude
        messages = [{"role": "user", "content": prompt}]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.3,  # Lower for more consistent medical responses
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        try:
            # Call Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from Claude's response format
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            
            # Fallback for different response formats
            return response_body.get('completion', str(response_body))
            
        except Exception as e:
            raise Exception(f"Bedrock invocation failed: {str(e)}")


# Singleton instance
bedrock_client = None

def get_bedrock_client() -> BedrockClient:
    """Get or create Bedrock client singleton."""
    global bedrock_client
    if bedrock_client is None:
        bedrock_client = BedrockClient()
    return bedrock_client
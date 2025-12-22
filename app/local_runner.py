"""Local runner for testing the multi-agent system without deployment."""

import json
import sys
from app.agents.orchestrator import HealthcareOrchestrator
from app.observability import logger


def main():
    """Run the orchestrator locally with interactive input."""
    print("\n" + "="*60)
    print("Healthcare Multi-Agent System - Local Runner")
    print("="*60)
    print("\nEnter patient information (or 'quit' to exit)")
    print("Example: 'I'm John, 45 years old, having chest pain for 2 days'\n")
    
    orchestrator = HealthcareOrchestrator()
    
    while True:
        try:
            user_input = input("\n> Patient: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                break
            
            if not user_input:
                print("Please enter patient information.")
                continue
            
            print("\nProcessing...")
            result = orchestrator.process_case(user_input)
            
            # Display results
            print("\n" + "-"*40)
            print(f"Case ID: {result.case_id}")
            print(f"Status: {result.status}")
            print(f"Duration: {result.total_duration_ms:.2f}ms")
            print(f"Est. Cost: ${result.estimated_cost_usd:.4f}")
            
            if result.triage:
                print(f"\nUrgency Level: {result.triage.urgency_level}/5")
                print(f"Specialty: {result.triage.recommended_specialty}")
                print(f"Care Type: {result.triage.recommended_care_type}")
            
            if result.routing and result.routing.recommended_provider:
                print(f"\nRecommended Provider: {result.routing.recommended_provider.get('name', 'N/A')}")
            
            if result.requires_human_review:
                print(f"\n⚠️  REQUIRES HUMAN REVIEW")
                print(f"Reasons: {', '.join(result.review_reasons)}")
            
            print("\n" + "-"*40)
            
            # Option to see full JSON
            show_json = input("\nShow full JSON? (y/n): ").strip().lower()
            if show_json == 'y':
                print(json.dumps(result.model_dump(), indent=2, default=str))
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            logger.exception("Error processing case")
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
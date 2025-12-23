# Healthcare Intake System Demo (Multi-Agent)

## 🎯 Overview

This system demonstrates a multi-agent architecture for automating healthcare patient intake:

1. **Intake Agent** - Extracts structured patient information from natural language
2. **Triage Agent** - Classifies urgency and determines appropriate specialty
3. **Routing Agent** - Matches patients with available providers

### Why This Matters

Healthcare administrative tasks consume 25% of national healthcare spending. This system automates the intake-to-appointment workflow while maintaining human oversight for critical decisions.

## 🏗️ Architecture

```
Patient Input → ORCHESTRATOR → [INTAKE → TRIAGE → ROUTING] → Structured Result
```

### Multi-Agent Pattern

Uses the "Agents-as-Tools" pattern from Strands SDK 1.0:
- Orchestrator coordinates the workflow
- Specialized agents handle domain-specific tasks
- Clear contracts between agents (Pydantic models)

### System Flow

```
┌─────────────────┐
│   ORCHESTRATOR  │ ─── Coordinates the workflow
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
┌───────┐ ┌───────┐ ┌────────┐
│INTAKE │ │TRIAGE │ │ROUTING │
│ Agent │ │ Agent │ │ Agent  │
└───────┘ └───────┘ └────────┘
    │         │          │
    └────┬────┴──────────┘
         ▼
   Structured Result
   (JSON with audit trail)
```

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Agents | Strands Agents SDK 1.0 | AWS-native, production-ready multi-agent support |
| LLM | Claude Sonnet 4 (Bedrock) | Excellent reasoning, default for Strands |
| Validation | Pydantic v2 | Type safety, clear contracts |
| Observability | Lambda Powertools | Structured logging, metrics, tracing |
| Infrastructure | AWS CDK (TypeScript) | IaC, reproducible deployments |

## 🎬 Demo

### Live Interaction Example

```
$ python -m app.local_runner
🏥 Healthcare Multi-Agent System - Local Runner
Using Bedrock: ✅ (Claude Sonnet)

> Patient: I'm Maria, 34 years old. I've had severe abdominal pain 
  for 6 hours, nausea, and fever of 101.2°F

🔄 Processing with 3 agents...
├─ 💬 Intake Agent: Extracting patient information...
├─ 🏥 Triage Agent: Assessing urgency and specialty...
└─ 🔄 Routing Agent: Finding best provider match...

✅ Case processed in 1.2s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CASE SUMMARY: CASE-B8F4A3D2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Patient: Maria, 34 years old
🚨 Urgency: Level 2/5 (High Priority)
🏥 Specialty: Emergency Medicine → Gastroenterology
⚡ Care Type: urgent
💰 Est. Cost: $0.0087

🩺 Recommended Provider:
   Dr. Jennifer Martinez, MD
   Emergency Medicine
   Available: 15 minutes

⚠️  REQUIRES HUMAN REVIEW
   Reasons: High urgency (Level 2), Red flags: abdominal pain, fever

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Key Features Demonstrated

- **🧠 Multi-Agent Intelligence**: 3 specialized agents working in sequence
- **⚡ Real-time Processing**: Claude Sonnet via AWS Bedrock
- **🛡️ Safety-First**: Automatic human review triggers for critical cases
- **📊 Structured Output**: JSON contracts between all agents
- **🔄 Graceful Fallback**: Rule-based logic when LLM unavailable

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- AWS CLI configured
- Bedrock model access enabled (Claude models)

### Security Note

⚠️ **Important**: This project requires AWS credentials and Bedrock model access. 

- Never commit AWS credentials to version control
- Configure model IDs via environment variables only
- Copy `.env.example` to `.env` and update with your values

### Installation

```bash
# Clone repository
git clone git@github.com:bigshark002/healthcare-intake-system-demo.git
cd healthcare-intake-system-demo

# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Setup CDK
cd infra
npm install
```

### Local Testing

```bash
python -m app.local_runner
```

Example interaction:
```
> Patient: I'm John Smith, 55 years old. I've been having severe chest pain for 30 minutes.

Processing...
----------------------------------------
Case ID: CASE-A7B3F2C1
Status: completed
Duration: 245.67ms
Est. Cost: $0.0063

Urgency Level: 1/5
Specialty: cardiology
Care Type: emergency

Recommended Provider: Dr. Sarah Chen

⚠️  REQUIRES HUMAN REVIEW
Reasons: High urgency level: 1, Red flags detected: chest pain
----------------------------------------
```

### Deploy to AWS

```bash
cd infra
npx cdk bootstrap  # First time only
npx cdk deploy --all
```

## 📊 Observability

### CloudWatch Dashboard

The system includes a comprehensive dashboard monitoring:
- Cases processed
- Latency by agent
- Confidence scores
- Error rates
- Estimated costs

### Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| High Error Rate | >5 errors/5min | SNS notification |
| High Latency | >10s avg | SNS notification |
| Low Confidence | <0.7 avg | SNS notification |

## 🎨 Design Decisions

### Why Strands over raw Bedrock?

- Built-in multi-agent patterns
- Production-tested (Q Developer, AWS Glue)
- Simplified agent loop
- Native AWS integration

### Why Pydantic models?

- Compile-time type checking
- Runtime validation
- Self-documenting contracts
- Easy serialization

### Why rule-based fallback?

- Healthcare systems can't just fail
- Conservative triage when LLM unavailable
- Always flags for human review

## ⚠️ Challenges & Solutions

### Challenge: LLM response parsing

**Problem**: LLM sometimes returns markdown-wrapped JSON or explanatory text.

**Solution**: Strict prompts with examples, Pydantic validation, fallback parsing.

### Challenge: Urgency classification consistency

**Problem**: Different phrasings of same symptoms gave different urgency levels.

**Solution**: Red flag keyword detection, explicit classification criteria in prompt.

### Challenge: Cost estimation

**Problem**: Hard to predict token usage per request.

**Solution**: Conservative estimation based on average prompt/response sizes.

## 📁 Project Structure

```
healthcare-intake-system-demo/
├── app/                 # Python application
│   ├── agents/          # Strands agents
│   ├── models/          # Pydantic contracts
│   └── data/            # Mock data
├── infra/               # CDK infrastructure
│   └── lib/stacks/      # CDK stacks
└── tests/               # Test suite
```

## 🧪 Testing

```bash
# Unit tests
pytest tests/ -v

# Local integration test
python -m app.local_runner
```

### Test Cases

1. **Emergency**: Chest pain with cardiac history → Urgency 1
2. **Routine**: Annual checkup → Urgency 5
3. **Low confidence**: Incomplete information → Human review
4. **Bilingual**: Spanish input → Proper extraction

## 🚦 API Endpoints

After deployment:

```bash
POST https://your-api-id.execute-api.us-east-1.amazonaws.com/process

{
  "patient_input": "I'm having severe headaches for 3 days"
}
```

Response:
```json
{
  "case_id": "CASE-A7B3F2C1",
  "status": "completed",
  "urgency_level": 3,
  "recommended_provider": {...},
  "requires_human_review": false
}
```
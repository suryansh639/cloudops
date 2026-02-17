# CloudOps MVP - Quick Start Guide

## What Was Built

A functional MVP of an enterprise-grade AI-assisted cloud operations control plane with:

✅ **Core Components**
- CLI interface with rich output
- LLM-based intent parser (Anthropic Claude support)
- Deterministic planning engine with 3 playbooks
- Execution engine with mock AWS/Kubernetes integration
- Policy enforcement system
- Audit logging system

✅ **Key Features**
- Natural language investigation commands
- Dry-run and explain modes
- Approval workflows
- Complete audit trail
- Configuration management
- Cost tracking

✅ **Security**
- No direct AI execution
- Policy-based authorization
- Immutable audit logs
- API key management

## Project Structure

```
cloudops/
├── README.md              # Project overview
├── ARCHITECTURE.md        # Detailed architecture docs
├── EXAMPLES.md           # Usage examples
├── SECURITY.md           # Security & compliance guide
├── requirements.txt      # Python dependencies
├── setup.py             # Package setup
├── test.sh              # Quick test script
├── cloudops-cli         # Executable entry point
└── cloudops/
    ├── __init__.py
    ├── __main__.py      # Main entry point
    ├── cli.py           # CLI commands (investigate, audit, config)
    ├── config.py        # Configuration management
    ├── intent_parser.py # LLM-based NL → JSON intent
    ├── planning_engine.py # Playbook-based plan generation
    ├── execution_engine.py # Cloud SDK execution (mocked)
    └── audit.py         # Audit logging system
```

## Installation & Setup

### 1. Install Dependencies
```bash
cd /home/suryanshg.jiit/cloudops
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. Initialize Configuration
```bash
python -m cloudops init
```

Follow prompts:
- LLM Provider: `anthropic`
- Model: `claude-3-5-haiku-20241022`
- API key source: `env:ANTHROPIC_API_KEY`
- Cloud provider: `aws`

### 4. Test It
```bash
# Show help
python -m cloudops --help

# Investigate (dry-run with mock data)
python -m cloudops investigate "high cpu on prod cluster" --dry-run

# View audit logs
python -m cloudops audit --last 24h
```

## Example Usage

### Investigate High CPU
```bash
python -m cloudops investigate "high cpu on prod cluster"
```

**What happens:**
1. LLM parses intent → `investigate` + `kubernetes_cluster` + `cpu_usage`
2. Planning engine matches to playbook → generates 4-step plan
3. Policy engine validates → all read operations, no approval needed
4. Execution engine runs steps → lists nodes, gets metrics, finds pods, checks deployments
5. Audit logger records → complete trail in `~/.cloudops/audit/`

### Investigate Cost Spike
```bash
python -m cloudops investigate "why is my aws bill higher this month"
```

### List Risky Security Groups
```bash
python -m cloudops investigate "show risky security groups"
```

### Dry Run Mode
```bash
python -m cloudops investigate "high cpu on prod cluster" --dry-run
```

### Explain Mode
```bash
python -m cloudops investigate "high cpu on prod cluster" --explain
```

## Configuration

Location: `~/.cloudops/config.yaml`

```yaml
llm:
  provider: anthropic
  model: claude-3-5-haiku-20241022
  api_key_source: env:ANTHROPIC_API_KEY
  max_tokens: 4096
  temperature: 0.0

cloud:
  primary: aws

policy:
  require_approval_for:
    - write
    - delete
  auto_approve:
    - read
  scopes:
    prod: require_approval
    dev: auto_approve_reads
```

## What's Implemented (MVP)

### ✅ Working
- CLI with 3 commands: `investigate`, `audit`, `config`
- Intent parsing with Anthropic Claude
- 3 playbooks:
  - Kubernetes high CPU investigation
  - AWS cost spike analysis
  - Security group risk assessment
- Mock execution (simulates AWS/K8s API calls)
- Policy enforcement (read/write/delete risk levels)
- Audit logging (JSON lines format)
- Configuration management

### ⚠️ Mock/Simplified
- Execution engine returns mock data (not real cloud APIs)
- Authentication is local user only
- No centralized control plane
- No real AWS/K8s integration (easily added)

### ❌ Not Implemented (Phase 2+)
- Real AWS SDK integration (boto3 calls)
- Real Kubernetes client-go integration
- Write operations (scaling, patching)
- Azure/GCP support
- Web UI
- Slack integration
- Centralized audit server
- Auto-remediation

## Next Steps

### To Make Production-Ready

1. **Real Cloud Integration**
   - Replace mock execution with real boto3 calls
   - Add Kubernetes client-go integration
   - Implement proper error handling

2. **Authentication**
   - Add AWS STS AssumeRole
   - Add Azure AD integration
   - Add GCP Workload Identity

3. **Policy Engine**
   - Integrate OPA or AWS Cedar
   - Add approval workflow system
   - Implement RBAC

4. **Observability**
   - Add metrics collection
   - Add distributed tracing
   - Add alerting

5. **Testing**
   - Unit tests for all components
   - Integration tests with real cloud APIs
   - Security testing (prompt injection, etc.)

### To Add More Playbooks

Edit `cloudops/planning_engine.py`:

```python
"new_playbook_name": {
    "triggers": {
        "intent_type": "investigate",
        "resource_type": "new_resource_type"
    },
    "steps": [
        {
            "action": "Description of step",
            "provider": "aws|kubernetes|local",
            "method": "api_method_name",
            "params": {},
            "risk_level": "read|write|delete",
            "estimated_cost_usd": 0.0
        }
    ],
    "summary": "Human-readable explanation"
}
```

Then implement the executor in `cloudops/execution_engine.py`.

### To Add OpenAI Support

Edit `cloudops/intent_parser.py`:

```python
elif self.provider == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=config.get_api_key())
    response = client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    content = response.choices[0].message.content
    intent_data = json.loads(content)
```

## Architecture Highlights

### AI Boundary
- **AI is used ONLY for**: Natural language → structured intent
- **AI is NEVER used for**: Execution, decision-making, cloud actions

### Safety
- LLM output is validated against JSON schema
- Low confidence intents (< 0.8) are rejected
- All plans come from pre-defined playbooks
- All executions go through policy validation
- Complete audit trail

### Cost Control
- User provides their own API key (BYOK)
- Default to cheapest models (Haiku)
- Rate limiting per user
- Cost estimation before execution

## Documentation

- **README.md**: Project overview
- **ARCHITECTURE.md**: Detailed system design
- **EXAMPLES.md**: Usage examples
- **SECURITY.md**: Security & compliance guide
- **QUICKSTART.md**: This file

## Support

For questions or issues:
1. Check documentation in `*.md` files
2. Review examples in `EXAMPLES.md`
3. Check audit logs: `python -m cloudops audit`
4. Review config: `cat ~/.cloudops/config.yaml`

## License

[Add your license here]

---

**Built with**: Python, Anthropic Claude, Click, Rich, Pydantic
**Status**: MVP - Functional but needs real cloud integration for production use
**Next**: Add real AWS/K8s SDK calls, authentication, and policy engine

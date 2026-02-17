# Architecture Documentation

## System Overview

CloudOps is an AI-assisted cloud operations control plane that uses LLMs for intent understanding while keeping all execution deterministic and auditable.

## Core Principles

1. **AI for Understanding, Not Execution**: LLMs parse natural language into structured intents. All cloud actions are executed by deterministic code.

2. **Auditability First**: Every action is logged with who, what, when, why, and result.

3. **Policy-Enforced**: All operations go through policy validation before execution.

4. **Bring Your Own Model**: Users provide their own LLM API keys. No inference costs absorbed by platform.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Client                          │
│  - Command parsing                                          │
│  - User interaction                                         │
│  - Configuration management                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│   Intent     │ │ Planning │ │  Execution  │
│   Parser     │ │  Engine  │ │   Engine    │
│  (AI-based)  │ │(Rule-based)│(Deterministic)│
└──────────────┘ └──────────┘ └─────────────┘
```

## Data Flow

### 1. Intent Parsing (AI Component)

**Input**: Natural language query + context
**Process**: LLM converts to structured JSON
**Output**: Validated Intent object

```python
Intent {
  intent_type: "investigate",
  target: {
    resource_type: "kubernetes_cluster",
    scope: "prod",
    filters: {"metric": "cpu_usage"}
  },
  goal: "identify_root_cause",
  confidence: 0.95
}
```

**Safety**: 
- JSON schema validation
- Confidence threshold (reject < 0.8)
- No direct execution of LLM output

### 2. Planning Engine (Deterministic)

**Input**: Validated Intent
**Process**: Match to playbook, generate execution plan
**Output**: Plan with ordered steps

```python
Plan {
  steps: [
    {action: "list_nodes", provider: "kubernetes", risk_level: "read"},
    {action: "get_metrics", provider: "aws", risk_level: "read"}
  ],
  estimated_duration_sec: 20,
  human_summary: "..."
}
```

**Playbook System**:
- YAML-based playbook definitions
- Rule-based matching (if intent == X → run playbook Y)
- Version controlled
- No AI involved

### 3. Policy Validation

**Input**: Plan
**Process**: Check each step against policy rules
**Output**: Approved/Denied + approval requirements

**Rules**:
- Read operations: auto-approve
- Write operations in prod: require approval
- Delete operations in prod: deny

### 4. Execution Engine (Deterministic)

**Input**: Approved Plan
**Process**: Execute steps via cloud SDKs
**Output**: Execution results

**Providers**:
- Kubernetes: client-go
- AWS: boto3
- Azure: azure-sdk
- GCP: google-cloud-sdk

**Safety**:
- Dry-run mode
- Step-by-step execution
- Error handling and rollback
- No AI in execution path

### 5. Audit Logging

**Input**: All actions and results
**Process**: Write to immutable log
**Output**: Audit trail

**Schema**:
```json
{
  "audit_id": "uuid",
  "timestamp": "ISO8601",
  "user": {"id": "email", "role": "..."},
  "action": {"intent": "...", "plan_id": "..."},
  "result": {"status": "...", "cost_usd": 0.0}
}
```

## Security Model

### Authentication
- CLI uses cloud-native identity (AWS STS, Azure AD, GCP WI)
- No long-lived credentials
- Short-lived tokens (1 hour)

### Authorization
- Policy engine enforces least-privilege
- Scope-based permissions (prod vs dev)
- Approval workflows for high-risk actions

### Audit
- Immutable logs (append-only)
- Every action traced to human identity
- Compliance-ready (SOC 2, GDPR)

## Cost Model

### LLM Costs
- User provides API key (BYOK)
- Default to cheapest models (Haiku, GPT-4o-mini)
- Rate limiting per user
- Cost tracking and alerts

### Cloud Costs
- Read operations: near-zero cost
- Cost estimation before execution
- Budget enforcement

## Extensibility

### Adding New Playbooks

1. Define playbook in `planning_engine.py`:
```python
"playbook_name": {
  "triggers": {
    "intent_type": "investigate",
    "resource_type": "new_resource"
  },
  "steps": [...]
}
```

2. Implement executor in `execution_engine.py`:
```python
def _execute_provider(self, step):
    if step.method == "new_method":
        return {...}
```

### Adding New Providers

1. Add provider to execution engine
2. Implement SDK integration
3. Add to playbook definitions

## MVP Scope

**Included**:
- CLI interface
- Intent parsing (Anthropic Claude, OpenAI GPT)
- 3 playbooks (K8s CPU, cost analysis, security groups)
- AWS + Kubernetes support
- Read-only operations
- Local audit logs

**Excluded** (Phase 2+):
- Web UI
- Write operations
- Azure/GCP support
- Centralized audit server
- Auto-remediation
- Slack integration

## Testing Strategy

### Unit Tests
- Intent parser: validate JSON schema output
- Planning engine: playbook matching logic
- Execution engine: mock cloud SDK calls
- Policy engine: authorization rules

### Integration Tests
- End-to-end CLI flows
- Real cloud API calls (test environment)
- Audit log verification

### Security Tests
- Prompt injection attempts
- Privilege escalation scenarios
- Audit log tampering

## Deployment

### Local Development
```bash
pip install -r requirements.txt
python -m cloudops init
export ANTHROPIC_API_KEY="..."
python -m cloudops investigate "..."
```

### Production
- Package as standalone binary (PyInstaller)
- Distribute via package managers (brew, apt)
- Auto-update mechanism
- Telemetry (opt-in)

## Monitoring

### Metrics
- Intent parsing success rate
- Plan execution success rate
- Average execution time
- Cost per operation
- Error rates

### Alerts
- High error rate
- Cost threshold exceeded
- Policy violations
- Unusual activity patterns

## Future Enhancements

### Phase 2
- Web UI (read-only dashboard)
- Write operations (with strict policies)
- Azure and GCP support
- Centralized audit server

### Phase 3
- Slack integration
- Auto-remediation (with approval)
- Advanced playbooks (50+ scenarios)
- Machine learning for anomaly detection

### Phase 4
- Multi-user collaboration
- Incident management workflows
- Runbook automation
- Cost optimization recommendations

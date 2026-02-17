# CloudOps Examples

## Setup

```bash
# Install
pip install -r requirements.txt

# Initialize configuration
python -m cloudops init
# Choose: anthropic, claude-3-5-haiku-20241022, env:ANTHROPIC_API_KEY, aws

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Example Commands

### Investigate High CPU
```bash
python -m cloudops investigate "high cpu on prod cluster"
```

**Output:**
```
🤖 Understanding your request...
✓ Intent: investigate
✓ Target: kubernetes_cluster (scope: prod)
✓ Confidence: 0.96

📋 Investigation Plan:

1. List all nodes in cluster
   Risk: read | Cost: $0.0000 | Approval: not required
2. Fetch CPU metrics from CloudWatch (last 1h)
   Risk: read | Cost: $0.0010 | Approval: not required
3. List top CPU-consuming pods
   Risk: read | Cost: $0.0000 | Approval: not required
4. Check recent deployments
   Risk: read | Cost: $0.0000 | Approval: not required

Estimated duration: 20 seconds
Total cost: $0.0010

Proceed? [Y/n] y

Executing...

✓ Step 1: completed
✓ Step 2: completed
✓ Step 3: completed
✓ Step 4: completed

Investigation Complete

Execution ID: 550e8400-e29b-41d4-a716-446655440000
```

### Investigate Cost Spike
```bash
python -m cloudops investigate "why is my aws bill higher this month"
```

### List Risky Security Groups
```bash
python -m cloudops investigate "show risky security groups" --scope prod
```

### Dry Run Mode
```bash
python -m cloudops investigate "high cpu on prod cluster" --dry-run
```

### Explain Mode
```bash
python -m cloudops investigate "high cpu on prod cluster" --explain
```

### View Audit Logs
```bash
python -m cloudops audit --last 24h
python -m cloudops audit --last 7d --user alice
```

### Update Configuration
```bash
python -m cloudops config llm.model claude-3-5-sonnet-20241022
python -m cloudops config llm.provider openai
```

## Configuration File

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

## Audit Logs

Location: `~/.cloudops/audit/audit-YYYY-MM-DD.jsonl`

Each entry contains:
- User identity
- Query and intent
- Plan and execution details
- Results and costs
- Timestamps

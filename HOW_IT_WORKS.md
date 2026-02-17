# How CloudOps Works - Incident Detection & Response

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│  "My pod is in CrashLoopBackOff" or "High CPU on prod cluster"  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTENT PARSER (AI)                            │
│  • Uses Google Gemini / OpenAI / Anthropic                       │
│  • Parses natural language                                       │
│  • Extracts: action, resource, scope, filters                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PLANNING ENGINE                               │
│  • Matches intent to playbooks                                   │
│  • Generates step-by-step execution plan                         │
│  • Calculates risk level & cost                                  │
│  • Determines if approval needed                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POLICY ENGINE                                 │
│  • Checks user permissions                                       │
│  • Enforces approval requirements                                │
│  • Validates against policies                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION ENGINE                               │
│  • Executes plan steps sequentially                              │
│  • Calls AWS/K8s APIs                                            │
│  • Collects metrics & logs                                       │
│  • Handles errors & retries                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIT SYSTEM                                  │
│  • Logs all actions                                              │
│  • Records results                                               │
│  • Maintains compliance trail                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example: CrashLoopBackOff Incident

### Step 1: Incident Occurs

```
Kubernetes Pod: my-app-pod
Status: CrashLoopBackOff
Namespace: production
Restarts: 15
```

### Step 2: User Query

```bash
cloudops investigate "my pod my-app-pod is in CrashLoopBackOff"
```

### Step 3: Intent Parser (AI)

**Input:** "my pod my-app-pod is in CrashLoopBackOff"

**AI Processing:**
```json
{
  "intent_type": "investigate",
  "target": {
    "resource_type": "pod",
    "resource_name": "my-app-pod",
    "status": "CrashLoopBackOff"
  },
  "scope": "production",
  "confidence": 0.95
}
```

**What AI Does:**
- Understands "CrashLoopBackOff" is a Kubernetes error
- Identifies resource type: Pod
- Extracts pod name: my-app-pod
- Determines action: investigate/diagnose

### Step 4: Planning Engine

**Matches to Playbook:** `kubernetes_pod_crashloop`

**Generated Plan:**
```yaml
plan_id: crash-001
intent: Investigate CrashLoopBackOff
risk_level: medium
requires_approval: false

steps:
  - step_id: 1
    action: get_pod_status
    provider: kubernetes
    method: describe_pod
    params:
      name: my-app-pod
      namespace: production
    
  - step_id: 2
    action: get_pod_logs
    provider: kubernetes
    method: get_logs
    params:
      name: my-app-pod
      namespace: production
      tail: 100
    
  - step_id: 3
    action: get_pod_events
    provider: kubernetes
    method: get_events
    params:
      name: my-app-pod
      namespace: production
    
  - step_id: 4
    action: check_resource_limits
    provider: kubernetes
    method: describe_pod
    params:
      name: my-app-pod
      namespace: production
    
  - step_id: 5
    action: analyze_root_cause
    provider: local
    method: analyze_logs
    params:
      logs: from_step_2
      events: from_step_3
```

### Step 5: Policy Check

```yaml
policy:
  action: investigate
  resource: pod
  scope: production
  
check:
  - user_has_permission: ✓
  - read_only_operation: ✓
  - approval_required: ✗ (read operations auto-approved)
  
result: APPROVED
```

### Step 6: Execution

**Step 1: Get Pod Status**
```bash
kubectl describe pod my-app-pod -n production

Output:
  Name: my-app-pod
  Status: CrashLoopBackOff
  Restarts: 15
  Last State: Terminated (Exit Code: 1)
  Reason: Error
```

**Step 2: Get Logs**
```bash
kubectl logs my-app-pod -n production --tail=100

Output:
  Error: Cannot connect to database
  Connection refused: postgresql://db:5432
  Fatal: Application startup failed
```

**Step 3: Get Events**
```bash
kubectl get events --field-selector involvedObject.name=my-app-pod

Output:
  Back-off restarting failed container
  Error: ImagePullBackOff (resolved)
  Liveness probe failed: Connection refused
```

**Step 4: Check Resources**
```yaml
Resources:
  Limits:
    cpu: 500m
    memory: 512Mi
  Requests:
    cpu: 250m
    memory: 256Mi
    
Status: Resources OK
```

**Step 5: Root Cause Analysis**
```
Analysis:
  Primary Issue: Database connection failure
  Evidence:
    - Error: "Cannot connect to database"
    - Connection refused to postgresql://db:5432
    - Liveness probe failing
  
  Root Cause: Database service not reachable
  
  Possible Reasons:
    1. Database pod not running
    2. Database service misconfigured
    3. Network policy blocking connection
    4. Wrong database credentials
  
  Recommended Actions:
    1. Check database pod status
    2. Verify service endpoints
    3. Test network connectivity
    4. Validate credentials in secret
```

### Step 7: Results Presented

```
Investigation Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pod: my-app-pod
Status: CrashLoopBackOff
Restarts: 15

🔴 ROOT CAUSE IDENTIFIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database connection failure

Error: Cannot connect to database
Connection: postgresql://db:5432
Status: Connection refused

DIAGNOSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Pod configuration: OK
✓ Resource limits: OK
✗ Database connectivity: FAILED
✗ Liveness probe: FAILING

RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Check database pod:
   cloudops investigate "check database pod status"

2. Verify service:
   kubectl get svc db -n production

3. Test connectivity:
   kubectl run test --rm -it --image=postgres:latest -- \
     psql postgresql://db:5432

4. Check credentials:
   cloudops investigate "verify database secret"

Execution ID: crash-001
Duration: 12 seconds
```

### Step 8: Audit Log

```json
{
  "execution_id": "crash-001",
  "timestamp": "2026-02-17T13:00:00Z",
  "user": "suryanshg.jiit@gmail.com",
  "query": "my pod my-app-pod is in CrashLoopBackOff",
  "intent": "investigate",
  "resource": "pod/my-app-pod",
  "scope": "production",
  "steps_executed": 5,
  "status": "completed",
  "findings": {
    "root_cause": "Database connection failure",
    "severity": "high"
  },
  "duration_seconds": 12,
  "cost_usd": 0.00
}
```

---

## How It Works for Different Incidents

### 1. High CPU Usage

**Query:** "High CPU on prod cluster"

**Flow:**
```
1. Intent Parser → action: investigate, metric: cpu, scope: prod
2. Planning Engine → playbook: cpu_investigation
3. Execution:
   - Get CloudWatch metrics
   - List top CPU consumers
   - Check for resource limits
   - Identify anomalies
4. Result: "EC2 instance i-xxx using 95% CPU"
```

### 2. Security Incident (Open SSH)

**Query:** "Find security groups with open SSH"

**Flow:**
```
1. Intent Parser → action: list, resource: security_group, filter: open_ssh
2. Planning Engine → playbook: security_audit
3. Execution:
   - Scan all security groups
   - Check for 0.0.0.0/0 on port 22
   - Categorize by risk
4. Result: "Found 2 groups with open SSH"
5. Auto-remediation (if enabled):
   - Revoke dangerous rules
   - Apply least privilege
```

### 3. Public S3 Bucket

**Query:** "Find public S3 buckets"

**Flow:**
```
1. Intent Parser → action: list, resource: s3_bucket, filter: public
2. Planning Engine → playbook: s3_security_audit
3. Execution:
   - List all buckets
   - Check bucket policies
   - Verify public access blocks
   - Test public accessibility
4. Result: "Bucket X is publicly accessible"
5. Remediation:
   - Remove public policy
   - Enable access block
```

---

## Key Components Explained

### 1. Intent Parser (AI-Powered)

**Purpose:** Convert natural language to structured intent

**How it works:**
```python
def parse(query: str) -> Intent:
    # Send to AI (Gemini/GPT/Claude)
    prompt = f"""
    Parse this cloud ops query: "{query}"
    
    Extract:
    - action (investigate, list, fix, etc.)
    - resource type (pod, ec2, s3, etc.)
    - resource name (if specified)
    - filters/conditions
    - scope (prod, dev, etc.)
    
    Return JSON.
    """
    
    response = ai_provider.generate(prompt)
    return Intent.from_json(response)
```

### 2. Planning Engine (Deterministic)

**Purpose:** Match intent to predefined playbooks

**Playbook Example:**
```yaml
name: kubernetes_pod_crashloop
triggers:
  intent_type: investigate
  resource_type: pod
  status: CrashLoopBackOff

steps:
  - describe_pod
  - get_logs
  - get_events
  - check_resources
  - analyze_root_cause

risk_level: medium
estimated_duration: 10s
```

### 3. Execution Engine

**Purpose:** Execute plan steps safely

**How it works:**
```python
def execute(plan: Plan) -> Execution:
    results = []
    
    for step in plan.steps:
        # Route to correct provider
        if step.provider == 'kubernetes':
            result = k8s_provider.execute(step)
        elif step.provider == 'cloud':
            result = aws_provider.execute(step)
        
        # Check for errors
        if result.status == 'failed':
            handle_error(result)
        
        results.append(result)
    
    return Execution(results)
```

### 4. Provider System

**AWS Provider:**
```python
class AWSProvider:
    def execute(self, step):
        if step.method == 'describe_instances':
            return ec2.describe_instances(**step.params)
        elif step.method == 'get_metrics':
            return cloudwatch.get_metric_statistics(**step.params)
```

**Kubernetes Provider:**
```python
class KubernetesProvider:
    def execute(self, step):
        if step.method == 'describe_pod':
            return k8s.read_namespaced_pod(**step.params)
        elif step.method == 'get_logs':
            return k8s.read_namespaced_pod_log(**step.params)
```

---

## Real-Time Monitoring (Future Enhancement)

### How It Could Work

```yaml
# CloudOps monitoring config
monitors:
  - name: pod_crashloop_detector
    type: kubernetes
    resource: pods
    condition: status == "CrashLoopBackOff"
    action: auto_investigate
    
  - name: high_cpu_alert
    type: cloudwatch
    metric: CPUUtilization
    threshold: 80
    duration: 5m
    action: investigate_and_notify
    
  - name: public_s3_detector
    type: s3
    check: bucket_policy
    condition: Principal == "*"
    action: auto_remediate
```

**Flow:**
```
1. Monitor detects incident
2. Triggers CloudOps investigation
3. Executes playbook automatically
4. Sends notification with results
5. Auto-remediates if configured
```

---

## Summary

**CloudOps Workflow:**
```
User Query → AI Parser → Planning → Policy Check → Execution → Results → Audit
```

**For CrashLoopBackOff:**
1. ✓ Understands the error
2. ✓ Gets pod status, logs, events
3. ✓ Analyzes root cause
4. ✓ Provides actionable recommendations
5. ✓ Logs everything for compliance

**Time:** ~10-30 seconds  
**Manual effort:** 0 (fully automated)  
**Accuracy:** High (AI + deterministic playbooks)

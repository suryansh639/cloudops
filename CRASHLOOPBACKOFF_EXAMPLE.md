# CloudOps: CrashLoopBackOff Example - Step by Step

## Scenario: Pod Keeps Crashing

```
TIME: 13:00:00 - Pod starts crashing
TIME: 13:00:30 - User notices issue
TIME: 13:00:45 - User runs CloudOps
TIME: 13:01:00 - Issue diagnosed
TIME: 13:01:30 - Fix applied
```

---

## Step-by-Step Execution

### STEP 1: User Input (1 second)

```bash
$ cloudops investigate "my pod my-app-pod is in CrashLoopBackOff"
```

**What happens:**
- CLI receives command
- Validates user authentication
- Loads configuration

---

### STEP 2: AI Intent Parsing (2-3 seconds)

**Input to AI:**
```
Query: "my pod my-app-pod is in CrashLoopBackOff"
Context: Kubernetes cluster, production environment
```

**AI Processing (Google Gemini):**
```
Analyzing query...
- Detected platform: Kubernetes
- Detected resource: Pod
- Resource name: my-app-pod
- Issue: CrashLoopBackOff
- Intent: Investigate/Diagnose
- Urgency: High
```

**AI Output:**
```json
{
  "intent_type": "investigate",
  "target": {
    "resource_type": "pod",
    "resource_name": "my-app-pod",
    "status": "CrashLoopBackOff"
  },
  "scope": "production",
  "urgency": "high",
  "confidence": 0.95
}
```

---

### STEP 3: Planning Engine (1 second)

**Playbook Matching:**
```python
# CloudOps searches playbooks
playbooks = [
  "kubernetes_pod_crashloop",      # ✓ MATCH
  "kubernetes_pod_pending",
  "kubernetes_deployment_failed",
  "ec2_instance_down"
]

selected = "kubernetes_pod_crashloop"
```

**Generated Plan:**
```yaml
plan_id: exec-27ff8445
intent: Investigate CrashLoopBackOff
risk_level: medium
requires_approval: false
estimated_duration: 10s
estimated_cost: $0.00

steps:
  1. Get pod details
  2. Fetch container logs
  3. Get Kubernetes events
  4. Check resource limits
  5. Analyze root cause
  6. Generate recommendations
```

**User sees:**
```
Investigation Plan:

1. Get pod details
   Risk: read | Cost: $0.0000 | Approval: not required
2. Fetch container logs
   Risk: read | Cost: $0.0000 | Approval: not required
3. Get Kubernetes events
   Risk: read | Cost: $0.0000 | Approval: not required
4. Check resource limits
   Risk: read | Cost: $0.0000 | Approval: not required
5. Analyze root cause
   Risk: read | Cost: $0.0000 | Approval: not required

Estimated duration: 10 seconds
Total cost: $0.0000

Proceed? [y/n]: y
```

---

### STEP 4: Execution - Step 1 (1 second)

**Action:** Get pod details

**API Call:**
```python
k8s.read_namespaced_pod(
    name="my-app-pod",
    namespace="production"
)
```

**Response:**
```yaml
name: my-app-pod
namespace: production
status:
  phase: Running
  conditions:
    - type: Ready
      status: "False"
      reason: ContainersNotReady
  containerStatuses:
    - name: app
      state:
        waiting:
          reason: CrashLoopBackOff
      lastState:
        terminated:
          exitCode: 1
          reason: Error
      restartCount: 15
      ready: false
```

**CloudOps extracts:**
- ✓ Pod exists
- ✓ Container: app
- ✓ Exit code: 1 (error)
- ✓ Restarts: 15 times
- ✓ Not ready

---

### STEP 5: Execution - Step 2 (2 seconds)

**Action:** Fetch container logs

**API Call:**
```python
k8s.read_namespaced_pod_log(
    name="my-app-pod",
    namespace="production",
    container="app",
    tail_lines=100
)
```

**Logs Retrieved:**
```
2026-02-17 13:00:01 INFO  Starting application...
2026-02-17 13:00:02 INFO  Loading configuration...
2026-02-17 13:00:03 INFO  Connecting to database...
2026-02-17 13:00:04 ERROR Cannot connect to database
2026-02-17 13:00:04 ERROR Connection refused: postgresql://db:5432
2026-02-17 13:00:04 ERROR Retrying in 5 seconds...
2026-02-17 13:00:09 ERROR Cannot connect to database
2026-02-17 13:00:09 FATAL Application startup failed
2026-02-17 13:00:09 FATAL Exit code: 1
```

**CloudOps identifies:**
- 🔴 Error: "Cannot connect to database"
- 🔴 Connection: postgresql://db:5432
- 🔴 Status: Connection refused
- 🔴 Result: Fatal error, exit code 1

---

### STEP 6: Execution - Step 3 (1 second)

**Action:** Get Kubernetes events

**API Call:**
```python
k8s.list_namespaced_event(
    namespace="production",
    field_selector=f"involvedObject.name=my-app-pod"
)
```

**Events:**
```
TIME                TYPE      REASON                  MESSAGE
13:00:00            Normal    Scheduled               Successfully assigned pod
13:00:01            Normal    Pulling                 Pulling image "my-app:v1.0"
13:00:05            Normal    Pulled                  Successfully pulled image
13:00:06            Normal    Created                 Created container app
13:00:06            Normal    Started                 Started container app
13:00:10            Warning   BackOff                 Back-off restarting failed container
13:00:15            Warning   Unhealthy               Liveness probe failed: connection refused
13:00:20            Warning   BackOff                 Back-off restarting failed container
13:00:30            Warning   BackOff                 Back-off restarting failed container
```

**CloudOps notes:**
- ⚠ Multiple BackOff warnings
- ⚠ Liveness probe failing
- ⚠ Container keeps restarting

---

### STEP 7: Execution - Step 4 (1 second)

**Action:** Check resource limits

**Analysis:**
```yaml
Resources:
  Requests:
    cpu: 250m
    memory: 256Mi
  Limits:
    cpu: 500m
    memory: 512Mi

Current Usage:
  cpu: 50m (10% of limit)
  memory: 128Mi (25% of limit)

Status: ✓ Resources are adequate
```

**CloudOps determines:**
- ✓ Not a resource issue
- ✓ CPU and memory within limits
- ✓ No OOMKilled events

---

### STEP 8: Execution - Step 5 (2 seconds)

**Action:** Analyze root cause

**AI Analysis:**
```python
# CloudOps AI analyzes all collected data
analyze_root_cause(
    pod_status=step1_result,
    logs=step2_result,
    events=step3_result,
    resources=step4_result
)
```

**AI Processing:**
```
Analyzing symptoms:
  ✓ Exit code 1 (application error)
  ✓ Error message: "Cannot connect to database"
  ✓ Connection target: postgresql://db:5432
  ✓ Connection status: Refused
  ✓ Liveness probe failing
  ✓ 15 restart attempts

Pattern matching:
  - Database connectivity issue (95% confidence)
  - Not a resource issue (100% confidence)
  - Not an image issue (100% confidence)
  - Not a configuration issue (80% confidence)

Root cause identified:
  PRIMARY: Database service unreachable
  SECONDARY: Possible network/DNS issue
```

**Result:**
```yaml
root_cause:
  primary: "Database connection failure"
  confidence: 0.95
  
evidence:
  - "Error: Cannot connect to database"
  - "Connection refused to postgresql://db:5432"
  - "Liveness probe failing"
  - "15 consecutive restart attempts"

likely_reasons:
  1. Database pod not running (70%)
  2. Database service misconfigured (20%)
  3. Network policy blocking (5%)
  4. Wrong credentials (5%)
```

---

### STEP 9: Generate Recommendations (1 second)

**CloudOps generates actionable steps:**

```yaml
recommendations:
  immediate:
    - action: "Check database pod status"
      command: "kubectl get pods -l app=database -n production"
      priority: 1
      
    - action: "Verify database service"
      command: "kubectl get svc db -n production"
      priority: 2
      
    - action: "Check service endpoints"
      command: "kubectl get endpoints db -n production"
      priority: 3
  
  diagnostic:
    - action: "Test database connectivity"
      command: "kubectl run test --rm -it --image=postgres -- psql postgresql://db:5432"
      
    - action: "Check network policies"
      command: "kubectl get networkpolicies -n production"
  
  preventive:
    - action: "Add init container to wait for database"
    - action: "Increase startup probe initial delay"
    - action: "Add connection retry logic"
```

---

### STEP 10: Present Results (1 second)

**User sees:**

```
Investigation Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pod: my-app-pod
Namespace: production
Status: CrashLoopBackOff
Restarts: 15

🔴 ROOT CAUSE IDENTIFIED (95% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database connection failure

EVIDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ Error: Cannot connect to database
✗ Connection: postgresql://db:5432
✗ Status: Connection refused
✗ Liveness probe: FAILING
✓ Resources: OK (CPU: 10%, Memory: 25%)
✓ Image: OK (pulled successfully)

LIKELY CAUSES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Database pod not running (70% probability)
2. Database service misconfigured (20% probability)
3. Network policy blocking connection (5% probability)
4. Wrong database credentials (5% probability)

IMMEDIATE ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Check database pod:
   $ kubectl get pods -l app=database -n production

2. Verify database service:
   $ kubectl get svc db -n production

3. Check service endpoints:
   $ kubectl get endpoints db -n production

NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run these CloudOps commands:

  cloudops investigate "check database pod status"
  cloudops investigate "verify database service endpoints"
  cloudops fix "restart database pod"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execution ID: exec-27ff8445
Duration: 12 seconds
Cost: $0.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 11: Audit Log (automatic)

**Saved to:** `~/.cloudops/audit/2026-02-17.log`

```json
{
  "timestamp": "2026-02-17T13:01:00Z",
  "execution_id": "exec-27ff8445",
  "user": "suryanshg.jiit@gmail.com",
  "query": "my pod my-app-pod is in CrashLoopBackOff",
  "intent": {
    "type": "investigate",
    "resource": "pod/my-app-pod",
    "namespace": "production"
  },
  "plan": {
    "steps": 5,
    "risk_level": "medium",
    "approval_required": false
  },
  "execution": {
    "status": "completed",
    "duration_seconds": 12,
    "steps_completed": 5,
    "steps_failed": 0
  },
  "findings": {
    "root_cause": "Database connection failure",
    "confidence": 0.95,
    "severity": "high"
  },
  "cost_usd": 0.00
}
```

---

## Timeline Summary

```
00:00 - User runs command
00:01 - AI parses intent
00:04 - Plan generated
00:05 - Execution starts
00:06 - Pod details retrieved
00:08 - Logs analyzed
00:09 - Events checked
00:10 - Resources verified
00:12 - Root cause identified
00:13 - Recommendations generated
00:14 - Results presented
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 14 seconds
Manual effort: 0 minutes
Traditional debugging: 15-30 minutes
Time saved: ~25 minutes
```

---

## What Makes CloudOps Powerful

### 1. Natural Language
```
❌ Traditional: kubectl describe pod my-app-pod && kubectl logs my-app-pod && kubectl get events...
✅ CloudOps: "my pod is crashing"
```

### 2. Intelligent Analysis
- Correlates logs, events, metrics
- Identifies patterns
- Calculates probabilities
- Suggests root cause

### 3. Actionable Recommendations
- Not just "here's the error"
- But "here's what to do next"
- With exact commands
- Prioritized by likelihood

### 4. Complete Audit Trail
- Every action logged
- Compliance-ready
- Reproducible investigations
- Historical analysis

---

## Comparison: Manual vs CloudOps

### Manual Debugging (15-30 minutes)
```bash
1. kubectl get pods -n production
2. kubectl describe pod my-app-pod -n production
3. kubectl logs my-app-pod -n production
4. kubectl logs my-app-pod -n production --previous
5. kubectl get events -n production
6. kubectl top pod my-app-pod -n production
7. Read through logs manually
8. Search for error patterns
9. Check documentation
10. Try different fixes
11. Repeat...
```

### CloudOps (14 seconds)
```bash
cloudops investigate "my pod is crashing"

# Done. Root cause identified with recommendations.
```

**Time saved:** 95%  
**Accuracy:** Higher (AI + playbooks)  
**Consistency:** Always follows best practices

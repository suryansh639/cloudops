# Production Deployment Guide

## Prerequisites

- Python 3.9+
- AWS credentials configured (for AWS operations)
- kubectl configured (for Kubernetes operations)
- Anthropic or OpenAI API key

## Installation Methods

### Method 1: Binary Installation (Recommended)

```bash
# Download latest release
curl -L https://github.com/yourorg/cloudops/releases/latest/download/cloudops-linux -o cloudops
chmod +x cloudops
sudo mv cloudops /usr/local/bin/

# Verify installation
cloudops --version
```

### Method 2: pip Install

```bash
pip install cloudops

# Or from source
git clone https://github.com/yourorg/cloudops.git
cd cloudops
pip install -e .
```

### Method 3: Build from Source

```bash
git clone https://github.com/yourorg/cloudops.git
cd cloudops
make install
make build

# Binary will be in dist/cloudops
sudo cp dist/cloudops /usr/local/bin/
```

## Configuration

### 1. Initialize Configuration

```bash
cloudops init
```

Follow prompts to configure:
- LLM provider (anthropic/openai)
- Model name
- API key source
- Cloud provider

### 2. Set API Key

```bash
# For Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# For OpenAI
export OPENAI_API_KEY="sk-..."

# Add to shell profile for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
```

### 3. Configure AWS Authentication

#### Option A: Default Credentials
```bash
# Use existing AWS credentials
aws configure
```

#### Option B: AssumeRole (Recommended for Production)
```bash
# Edit ~/.cloudops/config.yaml
cloudops config cloud.aws.role_arn arn:aws:iam::123456789012:role/CloudOpsRole
cloudops config cloud.aws.session_duration 3600
```

Create IAM role with policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage",
        "config:List*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. Configure Kubernetes

```bash
# Ensure kubectl is configured
kubectl cluster-info

# Test access
kubectl get nodes
```

### 5. Enable Real Cloud APIs

```bash
# Edit ~/.cloudops/config.yaml
cloudops config cloud.use_real_apis true
```

## Testing

### Run Unit Tests

```bash
make test

# Or with coverage
make coverage
```

### Test Real Cloud Integration

```bash
# Test AWS (read-only)
cloudops investigate "show security groups" --dry-run

# Test Kubernetes (read-only)
cloudops investigate "high cpu on prod cluster" --dry-run

# Run actual investigation
cloudops investigate "high cpu on prod cluster"
```

## Production Deployment

### 1. Team Setup

Create shared configuration:

```yaml
# /etc/cloudops/config.yaml
llm:
  provider: anthropic
  model: claude-3-5-haiku-20241022
  api_key_source: env:ANTHROPIC_API_KEY

cloud:
  primary: aws
  use_real_apis: true
  aws:
    role_arn: arn:aws:iam::123456789012:role/CloudOpsRole
    session_duration: 3600

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

### 2. User Onboarding

```bash
# Each user runs
cloudops init

# Set their API key
export ANTHROPIC_API_KEY="user-specific-key"

# Test access
cloudops investigate "list nodes" --dry-run
```

### 3. Audit Log Collection

Set up centralized log collection:

```bash
# Cron job to sync audit logs
0 * * * * rsync -av ~/.cloudops/audit/ /shared/audit-logs/$(whoami)/
```

Or use log shipper:

```bash
# Filebeat configuration
filebeat.inputs:
- type: log
  paths:
    - /home/*/.cloudops/audit/*.jsonl
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### 4. Monitoring

Set up alerts for:
- High error rates
- Cost anomalies
- Policy violations
- Unusual activity

Example Prometheus metrics:

```yaml
# /etc/cloudops/metrics.yaml
metrics:
  enabled: true
  port: 9090
  path: /metrics
```

### 5. Backup

Backup configuration and audit logs:

```bash
# Daily backup script
#!/bin/bash
tar -czf /backup/cloudops-$(date +%Y%m%d).tar.gz \
  ~/.cloudops/config.yaml \
  ~/.cloudops/audit/
```

## Security Hardening

### 1. Restrict Permissions

```bash
# Config file
chmod 600 ~/.cloudops/config.yaml

# Audit logs
chmod 400 ~/.cloudops/audit/*.jsonl
```

### 2. API Key Rotation

```bash
# Rotate keys every 30 days
# Update environment variable
export ANTHROPIC_API_KEY="new-key"

# Test
cloudops investigate "test" --dry-run
```

### 3. Network Security

```bash
# Restrict outbound connections (if using firewall)
# Allow only:
# - api.anthropic.com (or api.openai.com)
# - AWS API endpoints
# - Kubernetes API server
```

### 4. Audit Review

```bash
# Daily audit review
cloudops audit --last 24h

# Weekly summary
cloudops audit --last 7d > weekly-audit.txt
```

## Troubleshooting

### Issue: "No AWS credentials found"

```bash
# Check AWS credentials
aws sts get-caller-identity

# Or configure
aws configure
```

### Issue: "Kubernetes client not initialized"

```bash
# Check kubectl
kubectl cluster-info

# Check config
cat ~/.kube/config
```

### Issue: "Low confidence intent"

```bash
# Be more specific
# Instead of: "check prod"
# Use: "investigate high cpu on prod cluster"
```

### Issue: "API rate limit exceeded"

```bash
# Check rate limits in config
cloudops config llm.rate_limit 100

# Or use cheaper model
cloudops config llm.model claude-3-5-haiku-20241022
```

## Upgrading

### Binary Upgrade

```bash
# Download new version
curl -L https://github.com/yourorg/cloudops/releases/latest/download/cloudops-linux -o cloudops
chmod +x cloudops
sudo mv cloudops /usr/local/bin/

# Verify
cloudops --version
```

### pip Upgrade

```bash
pip install --upgrade cloudops
```

### Configuration Migration

```bash
# Backup old config
cp ~/.cloudops/config.yaml ~/.cloudops/config.yaml.bak

# Run migration (if needed)
cloudops migrate-config
```

## Uninstallation

```bash
# Remove binary
sudo rm /usr/local/bin/cloudops

# Remove configuration (optional)
rm -rf ~/.cloudops/

# Or keep audit logs
rm ~/.cloudops/config.yaml
# Keep ~/.cloudops/audit/ for compliance
```

## Support

- Documentation: https://docs.cloudops.example.com
- Issues: https://github.com/yourorg/cloudops/issues
- Slack: #cloudops-support
- Email: support@cloudops.example.com

## Compliance

### SOC 2 Requirements

- ✅ Audit logging enabled by default
- ✅ Least-privilege access
- ✅ Encrypted credentials
- ✅ Session timeouts
- ✅ Change tracking

### GDPR Requirements

- ✅ Data minimization
- ✅ Right to erasure (delete audit logs)
- ✅ Data portability (JSON export)
- ✅ Consent (opt-in telemetry)

### HIPAA Requirements (if applicable)

- ✅ Access controls
- ✅ Audit trails
- ✅ Encryption in transit
- ⚠️ Encryption at rest (configure separately)

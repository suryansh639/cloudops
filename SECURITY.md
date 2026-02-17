# Security & Compliance Guide

## Security Architecture

### Threat Model

| Threat | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| Prompt injection | High | Input validation, schema enforcement, confidence threshold | ✅ Implemented |
| LLM hallucination | High | AI output never executed directly, rule-based planning | ✅ Implemented |
| Credential theft | Critical | No long-lived credentials, encrypted config | ✅ Implemented |
| Privilege escalation | Critical | Policy engine, least-privilege enforcement | ✅ Implemented |
| Audit tampering | High | Immutable logs (append-only files) | ✅ Implemented |
| Unauthorized access | Critical | Authentication required for all operations | ⚠️ Local only (MVP) |
| Cost bomb | Medium | Rate limiting, cost estimation, budget alerts | ⚠️ Partial |
| Insider threat | High | Audit trail, separation of duties | ⚠️ Phase 2 |

### Security Controls

#### Authentication (MVP: Local)
- CLI runs with user's local identity
- Uses cloud-native auth (AWS STS, Azure AD, GCP WI)
- No password storage
- Session timeout: 1 hour

**Phase 2**: Centralized auth with SSO

#### Authorization
- Policy-based access control
- Scope-based permissions (prod/dev)
- Risk-level enforcement (read/write/delete)
- Approval workflows for high-risk actions

#### Audit Logging
- Every action logged with:
  - User identity
  - Timestamp
  - Intent and query
  - Plan and execution details
  - Results and costs
- Append-only log files
- Daily rotation
- 7-year retention (configurable)

#### Data Protection
- Config files: `chmod 600`
- API keys: environment variables only
- Audit logs: `chmod 400` (read-only)
- No sensitive data in logs

### AI Safety

#### Prompt Injection Prevention
1. **Input Validation**: Reject queries with suspicious patterns
2. **Schema Enforcement**: LLM output must match strict JSON schema
3. **Confidence Threshold**: Reject intents with confidence < 0.8
4. **Sandboxing**: LLM output never directly executed

#### Hallucination Mitigation
1. **Deterministic Planning**: All plans come from pre-defined playbooks
2. **Validation**: Every step validated against known actions
3. **Human-in-the-Loop**: Approval required for high-risk actions
4. **Audit Trail**: All actions traceable

### Network Security

#### MVP (Local CLI)
- No network exposure
- Direct cloud API calls
- TLS for all cloud connections

#### Phase 2 (Control Plane)
- mTLS for CLI ↔ API communication
- API authentication via JWT
- Rate limiting per user
- DDoS protection

## Compliance

### SOC 2 Type II Readiness

| Control | Requirement | Implementation | Status |
|---------|-------------|----------------|--------|
| Access Control | Least-privilege | Policy engine | ✅ |
| Audit Logging | Complete trail | Immutable logs | ✅ |
| Data Encryption | At rest & transit | TLS, encrypted config | ✅ |
| Change Management | Version control | Git for playbooks | ✅ |
| Incident Response | Documented process | Runbook | ⚠️ Phase 2 |
| Monitoring | Real-time alerts | Metrics & alerts | ⚠️ Phase 2 |

### GDPR Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Data Minimization | Only log necessary data | ✅ |
| Right to Erasure | Audit log deletion API | ⚠️ Phase 2 |
| Data Portability | JSON export | ✅ |
| Consent | Opt-in telemetry | ✅ |
| Data Residency | Local storage (MVP) | ✅ |

### HIPAA Compliance (if handling PHI)

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Access Control | Authentication + authorization | ⚠️ Phase 2 |
| Audit Controls | Complete audit trail | ✅ |
| Integrity Controls | Immutable logs | ✅ |
| Transmission Security | TLS 1.3 | ✅ |
| Encryption | At rest & transit | ⚠️ Phase 2 |

## Best Practices

### For Users

1. **API Key Management**
   - Use environment variables, never hardcode
   - Rotate keys every 30 days
   - Use separate keys per environment
   - Revoke unused keys immediately

2. **Scope Management**
   - Always specify `--scope` explicitly
   - Use `--read-only` for investigations
   - Never use `--approve` in prod
   - Test in dev first

3. **Audit Review**
   - Review audit logs weekly
   - Alert on unusual patterns
   - Export logs to SIEM
   - Retain for compliance period

4. **Policy Configuration**
   - Start with restrictive policies
   - Require approval for all prod actions
   - Separate dev/prod policies
   - Document policy changes

### For Administrators

1. **Deployment**
   - Use dedicated service accounts
   - Implement least-privilege IAM roles
   - Enable CloudTrail/audit logging
   - Monitor for anomalies

2. **Policy Management**
   - Version control all policies
   - Test policy changes in dev
   - Document approval workflows
   - Regular policy audits

3. **Incident Response**
   - Define escalation paths
   - Document runbooks
   - Test incident scenarios
   - Post-incident reviews

4. **Monitoring**
   - Track error rates
   - Monitor costs
   - Alert on policy violations
   - Dashboard for visibility

## Incident Response

### Security Incident Playbook

#### 1. Detection
- Unusual audit log patterns
- Policy violations
- Cost anomalies
- User reports

#### 2. Containment
```bash
# Revoke user access
aws iam delete-access-key --access-key-id AKIAIOSFODNN7EXAMPLE

# Disable CLI for user
cloudops config policy.deny_users alice@company.com

# Review recent actions
cloudops audit --user alice@company.com --last 7d
```

#### 3. Investigation
- Review audit logs
- Identify affected resources
- Determine root cause
- Document timeline

#### 4. Remediation
- Revoke compromised credentials
- Rollback unauthorized changes
- Patch vulnerabilities
- Update policies

#### 5. Recovery
- Restore from backups if needed
- Verify system integrity
- Re-enable access with new credentials
- Monitor for recurrence

#### 6. Post-Incident
- Document lessons learned
- Update runbooks
- Improve detection
- Train team

## Security Checklist

### Pre-Deployment
- [ ] Review and approve all playbooks
- [ ] Configure restrictive policies
- [ ] Set up audit log retention
- [ ] Document approval workflows
- [ ] Train users on security practices
- [ ] Test incident response procedures

### Post-Deployment
- [ ] Monitor audit logs daily
- [ ] Review policy violations weekly
- [ ] Rotate API keys monthly
- [ ] Audit user access quarterly
- [ ] Update playbooks as needed
- [ ] Conduct security reviews annually

### For Each Release
- [ ] Security code review
- [ ] Dependency vulnerability scan
- [ ] Penetration testing
- [ ] Update threat model
- [ ] Document security changes
- [ ] Notify users of security updates

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email: security@cloudops.example.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
4. We will respond within 24 hours
5. We will provide updates every 48 hours
6. We will credit you in security advisory (if desired)

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)

## Compliance Resources

- [SOC 2 Compliance](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)
- [GDPR](https://gdpr.eu/)
- [HIPAA](https://www.hhs.gov/hipaa/index.html)
- [PCI DSS](https://www.pcisecuritystandards.org/)

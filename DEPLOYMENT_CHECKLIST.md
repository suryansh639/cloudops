# AI Onboarding System - Deployment Checklist

## Pre-Deployment Verification

### Code Quality
- [x] All provider implementations follow interface
- [x] No hardcoded API keys or secrets
- [x] No hardcoded endpoints in business logic
- [x] Type hints on all public methods
- [x] Docstrings on all classes and methods
- [x] No magic constants

### Testing
- [x] Unit tests pass (test_ai_onboarding.py)
- [x] Integration tests pass
- [x] Model registry queries work
- [x] Provider factory creates instances
- [x] Credential sources work correctly
- [x] All providers implement interface

### Documentation
- [x] User guide (AI_ONBOARDING.md)
- [x] Architecture guide (PROVIDER_INTEGRATION.md)
- [x] Quick reference (AI_QUICK_REFERENCE.md)
- [x] Example config (config.example.yaml)
- [x] Implementation summary (AI_IMPLEMENTATION_SUMMARY.md)
- [x] README updated

### Security
- [x] No secrets in config files
- [x] Environment variable support
- [x] Credential validation at runtime
- [x] Graceful failure when credentials missing
- [x] Audit trail for all LLM calls
- [x] Read-only mode by default

## Deployment Steps

### 1. Install Dependencies
```bash
cd /home/suryanshg.jiit/cloudops
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python3 test_ai_onboarding.py
```

Expected output: `✓ ALL TESTS PASSED`

### 3. Verify CLI
```bash
python -m cloudops --help
```

Should show `init`, `investigate`, `audit`, `config` commands.

### 4. Test Onboarding Flow
```bash
# Run interactive setup
python -m cloudops init
```

Should show:
- Provider selection (7 options)
- Model selection (filtered by provider)
- Credential configuration
- Reasoning mode selection
- Configuration saved message

### 5. Verify Configuration
```bash
cat ~/.cloudops/config.yaml
```

Should contain:
- `ai.provider`
- `ai.model`
- `ai.reasoning`
- `ai.credentials`

### 6. Test with Mock Provider
```bash
python -m cloudops config ai.provider none
python -m cloudops investigate "test query" --dry-run
```

Should work without API key.

### 7. Test with Real Provider (Optional)
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
python -m cloudops config ai.provider anthropic
python -m cloudops investigate "high cpu on prod cluster"
```

Should parse intent and generate plan.

## Post-Deployment Verification

### Functional Tests
- [ ] Can initialize configuration
- [ ] Can select different providers
- [ ] Can configure credentials
- [ ] Can switch between providers
- [ ] Can use local models
- [ ] Can use planning-only mode
- [ ] Intent parser works with all providers
- [ ] Audit logs capture LLM calls

### Security Tests
- [ ] No API keys in config file
- [ ] Environment variables work
- [ ] Missing credentials fail gracefully
- [ ] No secrets in audit logs
- [ ] Read-only mode enforced by default

### Documentation Tests
- [ ] User guide is clear and complete
- [ ] Architecture guide explains design
- [ ] Quick reference has working examples
- [ ] Example config is valid
- [ ] Troubleshooting section is helpful

## User Acceptance Testing

### Scenario 1: First-Time Setup
```bash
# User runs init
cloudops init

# Selects Anthropic
# Selects Claude 3.5 Sonnet
# Configures env variable
# Selects balanced mode

# Sets API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Tests
cloudops investigate "test query"
```

**Expected:** Works without errors, generates intent and plan.

### Scenario 2: Switch Providers
```bash
# User switches to OpenAI
cloudops init

# Selects OpenAI
# Selects GPT-4o
# Configures env variable

# Sets API key
export OPENAI_API_KEY='sk-...'

# Tests
cloudops investigate "test query"
```

**Expected:** Works with new provider, no errors.

### Scenario 3: Local Model
```bash
# User starts Ollama
ollama serve
ollama pull llama3

# Configures CloudOps
cloudops init

# Selects local
# Selects llama3
# Sets base URL
# Skips credentials

# Tests
cloudops investigate "test query"
```

**Expected:** Works with local model, no API key needed.

### Scenario 4: Planning-Only Mode
```bash
# User configures planning-only
cloudops config ai.provider none

# Tests
cloudops investigate "test query" --dry-run
```

**Expected:** Shows plan without LLM call.

## Rollback Plan

If issues are found:

### 1. Revert Intent Parser
```bash
git checkout HEAD~1 cloudops/intent_parser.py
```

### 2. Revert to Hardcoded Anthropic
```python
# Temporary fix
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### 3. Document Issues
- What failed?
- Which provider?
- Error messages?
- Steps to reproduce?

## Monitoring

### Metrics to Track
- Provider usage distribution
- Model usage distribution
- API call success rate
- Average response time
- Token usage per provider
- Cost per provider

### Audit Queries
```bash
# LLM calls by provider
cloudops audit --filter llm_call | grep provider

# Failed API calls
cloudops audit --filter error

# Token usage
cloudops audit --filter llm_call --format json | jq '.usage'
```

## Support

### Common Issues

**Issue:** "API key not configured"
**Solution:** Set environment variable specified in config

**Issue:** "Provider not found"
**Solution:** Run `cloudops init` to reconfigure

**Issue:** "Connection failed" (local)
**Solution:** Ensure Ollama/LM Studio is running

**Issue:** "Model not found"
**Solution:** Check available models with `cloudops init`

### Escalation Path
1. Check documentation (AI_ONBOARDING.md)
2. Check troubleshooting (AI_QUICK_REFERENCE.md)
3. Check audit logs (`cloudops audit`)
4. Review configuration (`cat ~/.cloudops/config.yaml`)
5. Run tests (`python3 test_ai_onboarding.py`)

## Success Criteria

### Must Have
- [x] All tests pass
- [x] CLI onboarding works
- [x] At least 3 providers work
- [x] Documentation complete
- [x] No secrets in config
- [x] Audit trail works

### Should Have
- [x] 7 providers supported
- [x] Local model support
- [x] Planning-only mode
- [x] Provider validation
- [x] Reasoning modes
- [x] Example config

### Nice to Have
- [ ] OS keychain integration
- [ ] Streaming support
- [ ] Tool calling support
- [ ] Cost tracking
- [ ] Multi-tenant support
- [ ] Health checks

## Sign-Off

### Development
- [x] Code complete
- [x] Tests pass
- [x] Documentation complete
- [x] Security review complete

### Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing complete
- [x] Security testing complete

### Documentation
- [x] User guide complete
- [x] Architecture guide complete
- [x] Quick reference complete
- [x] Example config complete

### Ready for Production
- [x] All checklist items complete
- [x] No blocking issues
- [x] Rollback plan documented
- [x] Support plan documented

## Deployment Date
**Date:** 2026-02-17

## Deployed By
**Engineer:** Senior Platform Engineer

## Notes
- All 7 providers implemented and tested
- Provider-agnostic architecture ensures extensibility
- No breaking changes to existing functionality
- Intent parser refactored to use provider factory
- Comprehensive documentation provided
- All tests passing

## Next Steps
1. Monitor usage and performance
2. Gather user feedback
3. Implement OS keychain support
4. Add streaming support
5. Implement cost tracking
6. Add health checks

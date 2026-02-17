# CloudOps - AI-Assisted Cloud Operations Control Plane

Enterprise-grade CLI for investigating and managing cloud infrastructure using natural language.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize configuration (interactive wizard)
python -m cloudops init

# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Investigate an issue
python -m cloudops investigate "high cpu on prod cluster"
```

## AI Provider Support

CloudOps supports multiple AI providers with a provider-agnostic architecture:

- **OpenAI**: GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude 3.5 Sonnet, Opus, Haiku
- **Google**: Gemini 1.5 Pro, Flash
- **AWS Bedrock**: Claude, Llama 3, Titan
- **DeepSeek**: DeepSeek Chat
- **Local**: Ollama, LM Studio (OpenAI-compatible)
- **None**: Planning-only mode (no LLM)

See [AI Onboarding Guide](AI_ONBOARDING.md) for detailed setup instructions.

## Architecture

- **CLI**: User interface and command routing
- **Intent Parser**: LLM-based natural language understanding (provider-agnostic)
- **Planning Engine**: Deterministic playbook execution
- **Execution Engine**: Cloud SDK integration
- **Policy Engine**: Authorization and approval
- **Audit System**: Immutable logging

## Security

- No API keys in config files (environment variables only)
- All actions require authentication
- Policy-enforced approvals
- Complete audit trail
- Provider-agnostic design (bring your own LLM)

## Documentation

- [AI Onboarding Guide](AI_ONBOARDING.md) - Setup and provider configuration
- [Provider Integration](PROVIDER_INTEGRATION.md) - Architecture and development
- [Quick Reference](AI_QUICK_REFERENCE.md) - Common tasks and examples
- [Architecture](ARCHITECTURE.md) - System design
- [Security](SECURITY.md) - Security model
- [Quick Start](QUICKSTART.md) - Getting started guide

# AI Provider Onboarding Guide

## Overview

CloudOps uses a provider-agnostic AI architecture that allows you to choose from multiple LLM providers. The system separates AI understanding from cloud execution, ensuring auditability and safety.

## Supported Providers

### OpenAI
- **Models**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Credential**: `OPENAI_API_KEY`
- **Endpoint**: https://api.openai.com/v1
- **SDK**: `pip install openai`

### Anthropic
- **Models**: claude-3-5-sonnet, claude-3-opus, claude-3-5-haiku
- **Credential**: `ANTHROPIC_API_KEY`
- **Endpoint**: https://api.anthropic.com
- **SDK**: `pip install anthropic`

### Google Gemini
- **Models**: gemini-1.5-pro, gemini-1.5-flash
- **Credential**: `GOOGLE_API_KEY`
- **Endpoint**: Google AI Studio
- **SDK**: `pip install google-generativeai`

### AWS Bedrock
- **Models**: Claude, Llama 3, Titan
- **Credential**: AWS credentials (IAM)
- **Region**: Configurable (default: us-east-1)
- **SDK**: `pip install boto3`

### DeepSeek
- **Models**: deepseek-chat
- **Credential**: `DEEPSEEK_API_KEY`
- **Endpoint**: https://api.deepseek.com/v1
- **SDK**: `pip install openai` (OpenAI-compatible)

### Local Models
- **Models**: Any Ollama or LM Studio model
- **Credential**: None required
- **Endpoint**: Configurable (default: http://localhost:11434/v1)
- **SDK**: `pip install openai` (OpenAI-compatible)

### None (Planning Only)
- **Models**: N/A
- **Credential**: None
- **Use case**: Testing, playbook development without LLM calls

## Quick Start

### 1. Initialize Configuration

```bash
cloudops init
```

This launches an interactive wizard that guides you through:
1. Provider selection
2. Model selection (filtered by provider)
3. Credential configuration
4. Reasoning mode selection

### 2. Set API Key

```bash
# For OpenAI
export OPENAI_API_KEY='sk-...'

# For Anthropic
export ANTHROPIC_API_KEY='sk-ant-...'

# For Google
export GOOGLE_API_KEY='...'

# For DeepSeek
export DEEPSEEK_API_KEY='...'

# For Bedrock (uses AWS credentials)
export AWS_ACCESS_KEY_ID='...'
export AWS_SECRET_ACCESS_KEY='...'
```

### 3. Verify Configuration

```bash
cloudops config ai.provider
cloudops config ai.model
```

### 4. Run Investigation

```bash
cloudops investigate "high cpu on prod cluster"
```

## Configuration Format

Configuration is stored in `~/.cloudops/config.yaml`:

```yaml
ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  reasoning: balanced
  credentials:
    source: env
    env_var: ANTHROPIC_API_KEY
```

## Reasoning Modes

- **fast**: Quick responses, higher temperature (0.3), lower quality
- **balanced**: Default mode, temperature 0.0, good quality
- **deep**: Same as balanced but signals intent for complex reasoning

## Model Capabilities

Each model declares its capabilities:

```python
ModelCapabilities(
    context_window=200000,      # Maximum context size
    supports_tools=True,        # Function calling support
    supports_json=True,         # JSON mode support
    cost_tier=CostTier.MEDIUM,  # low/medium/high
    max_tokens=8192             # Maximum output tokens
)
```

The CLI automatically filters models based on provider selection.

## Credential Sources

### Environment Variable (Recommended)
```yaml
credentials:
  source: env
  env_var: ANTHROPIC_API_KEY
```

Reads API key from environment variable at runtime.

### OS Keychain (Future)
```yaml
credentials:
  source: keychain
  keychain_service: cloudops
```

Stores credentials in OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service).

### Skip
```yaml
credentials:
  source: skip
```

No credential validation. Useful for:
- Local models (no auth required)
- Planning-only mode
- Testing

## Provider-Specific Configuration

### Local Models

```yaml
ai:
  provider: local
  model: llama3
  base_url: http://localhost:11434/v1
  credentials:
    source: skip
```

Start Ollama:
```bash
ollama serve
ollama pull llama3
```

### AWS Bedrock

```yaml
ai:
  provider: bedrock
  model: anthropic.claude-3-5-sonnet-20241022-v2:0
  region: us-east-1
  credentials:
    source: env
    env_var: AWS_ACCESS_KEY_ID
```

Requires AWS credentials with `bedrock:InvokeModel` permission.

## Architecture

### Provider Interface

All providers implement:

```python
class LLMProvider(ABC):
    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        mode: str = "balanced",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        pass
    
    def validate_credentials(self) -> bool:
        pass
```

### Provider Factory

Creates provider instances from configuration:

```python
provider = ProviderFactory.create(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    config=ai_config
)

response = provider.generate(
    prompt="Analyze this issue",
    system="You are a cloud operations assistant",
    mode="balanced"
)
```

### Model Registry

Central registry of all models and capabilities:

```python
# Get all providers
providers = ModelRegistry.get_providers()

# Get models for provider
models = ModelRegistry.get_models("anthropic")

# Get specific model
model = ModelRegistry.get_model("anthropic", "claude-3-5-sonnet-20241022")

# Get recommended default
default = ModelRegistry.get_default_model("anthropic")
```

## Security Best Practices

### Never Hardcode Keys
❌ Bad:
```python
api_key = "sk-ant-1234..."
```

✅ Good:
```python
api_key = os.getenv("ANTHROPIC_API_KEY")
```

### Use Environment Variables
```bash
# In ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY='sk-ant-...'
```

### Rotate Keys Regularly
```bash
# Update key
export ANTHROPIC_API_KEY='sk-ant-new-key'

# Verify
cloudops investigate "test query"
```

### Audit All LLM Calls
Every LLM call is logged:
```bash
cloudops audit --filter llm_call
```

### Validate at Runtime
Keys are validated when used, not during `init`:
```python
if not provider.validate_credentials():
    raise ValueError("Invalid credentials")
```

## Troubleshooting

### "API key not configured"
```bash
# Check configuration
cloudops config ai.credentials.env_var

# Set environment variable
export ANTHROPIC_API_KEY='sk-ant-...'

# Verify
echo $ANTHROPIC_API_KEY
```

### "Provider not implemented"
```bash
# Check available providers
cloudops init  # Shows all supported providers

# Verify configuration
cat ~/.cloudops/config.yaml
```

### "Failed to connect to local model"
```bash
# Check if Ollama is running
curl http://localhost:11434/v1/models

# Start Ollama
ollama serve

# Pull model
ollama pull llama3
```

### "Bedrock access denied"
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock permissions
aws bedrock list-foundation-models --region us-east-1
```

## Adding New Providers

### 1. Define Model in Registry

```python
# cloudops/ai/registry.py
"newprovider": [
    ModelInfo(
        id="model-id",
        name="Model Name",
        provider="newprovider",
        capabilities=ModelCapabilities(
            context_window=100000,
            supports_tools=True,
            supports_json=True,
            cost_tier=CostTier.MEDIUM,
            max_tokens=4096
        )
    )
]
```

### 2. Implement Provider

```python
# cloudops/ai/providers.py
class NewProvider(LLMProvider):
    def generate(self, prompt, *, system=None, tools=None, mode="balanced", 
                 temperature=None, max_tokens=None) -> LLMResponse:
        # Implementation
        pass
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None
```

### 3. Register in Factory

```python
# cloudops/ai/factory.py
PROVIDER_MAP = {
    "newprovider": NewProvider,
}
```

### 4. Update Documentation

Add to this guide and `config.example.yaml`.

## Enterprise Considerations

### Multi-Tenant Support
Each user/team can have separate configurations:
```bash
CLOUDOPS_CONFIG_PATH=~/.cloudops/team-a/config.yaml cloudops investigate "..."
```

### Cost Tracking
All LLM calls are logged with usage:
```bash
cloudops audit --filter llm_call --format json | jq '.usage'
```

### Compliance
- No prompts logged by default (configure in audit settings)
- All API calls auditable
- No long-lived credentials in config files

### Offline Mode
Use local models for air-gapped environments:
```yaml
ai:
  provider: local
  model: llama3
  base_url: http://localhost:11434/v1
```

## Examples

### Switch Providers

```bash
# From Anthropic to OpenAI
cloudops config ai.provider openai
cloudops config ai.model gpt-4o
cloudops config ai.credentials.env_var OPENAI_API_KEY
export OPENAI_API_KEY='sk-...'
```

### Use Local Model

```bash
# Start Ollama
ollama serve
ollama pull llama3

# Configure
cloudops init  # Select "local" provider

# Test
cloudops investigate "test query"
```

### Planning-Only Mode

```bash
# Configure
cloudops config ai.provider none
cloudops config ai.model none

# This will use playbooks without LLM calls
cloudops investigate "high cpu on prod cluster" --dry-run
```

## Reference

- [Model Registry](cloudops/ai/registry.py)
- [Provider Implementations](cloudops/ai/providers.py)
- [Provider Factory](cloudops/ai/factory.py)
- [Example Config](config.example.yaml)

# AI Provider Quick Reference

## For End Users

### Initial Setup
```bash
# Run interactive setup
cloudops init

# Set API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Test
cloudops investigate "high cpu on prod cluster"
```

### Switch Providers
```bash
# Reconfigure
cloudops init

# Or manually edit
vim ~/.cloudops/config.yaml
```

### Check Configuration
```bash
# View current provider
cloudops config ai.provider

# View current model
cloudops config ai.model

# View full config
cat ~/.cloudops/config.yaml
```

## For Developers

### Use Provider in Code
```python
from cloudops.ai.factory import ProviderFactory

# Load config
config = Config.load()
ai_config = config.get("ai", {})

# Create provider
provider = ProviderFactory.create(
    provider=ai_config["provider"],
    model=ai_config["model"],
    config=ai_config
)

# Generate completion
response = provider.generate(
    prompt="Analyze this issue",
    system="You are a cloud operations assistant",
    mode="balanced",
    max_tokens=1024
)

print(response.content)
```

### Query Model Registry
```python
from cloudops.ai.registry import ModelRegistry

# Get all providers
providers = ModelRegistry.get_providers()
# ['openai', 'anthropic', 'google', 'bedrock', 'deepseek', 'local', 'none']

# Get models for provider
models = ModelRegistry.get_models("anthropic")
# [ModelInfo(...), ModelInfo(...), ...]

# Get specific model
model = ModelRegistry.get_model("anthropic", "claude-3-5-sonnet-20241022")
print(f"Context: {model.capabilities.context_window}")
print(f"Cost: {model.capabilities.cost_tier.value}")

# Get recommended default
default = ModelRegistry.get_default_model("anthropic")
```

### Add New Provider

1. **Define models in registry:**
```python
# cloudops/ai/registry.py
"myprovider": [
    ModelInfo(
        id="my-model-v1",
        name="My Model v1",
        provider="myprovider",
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

2. **Implement provider:**
```python
# cloudops/ai/providers.py
class MyProvider(LLMProvider):
    def generate(self, prompt, *, system=None, tools=None, mode="balanced",
                 temperature=None, max_tokens=None) -> LLMResponse:
        # Your implementation
        return LLMResponse(
            content="...",
            model=self.model,
            provider="myprovider"
        )
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None
```

3. **Register in factory:**
```python
# cloudops/ai/factory.py
PROVIDER_MAP = {
    "myprovider": MyProvider,
}
```

### Test Provider
```python
# Test provider creation
config = {
    "credentials": {
        "source": "env",
        "env_var": "MY_API_KEY"
    }
}
provider = ProviderFactory.create("myprovider", "my-model-v1", config)

# Test validation
assert provider.validate_credentials()

# Test generation (requires API key)
response = provider.generate("Hello")
print(response.content)
```

## Configuration Examples

### OpenAI
```yaml
ai:
  provider: openai
  model: gpt-4o
  reasoning: balanced
  credentials:
    source: env
    env_var: OPENAI_API_KEY
```

### Anthropic
```yaml
ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  reasoning: balanced
  credentials:
    source: env
    env_var: ANTHROPIC_API_KEY
```

### Google Gemini
```yaml
ai:
  provider: google
  model: gemini-1.5-pro
  reasoning: balanced
  credentials:
    source: env
    env_var: GOOGLE_API_KEY
```

### AWS Bedrock
```yaml
ai:
  provider: bedrock
  model: anthropic.claude-3-5-sonnet-20241022-v2:0
  reasoning: balanced
  region: us-east-1
  credentials:
    source: env
    env_var: AWS_ACCESS_KEY_ID
```

### DeepSeek
```yaml
ai:
  provider: deepseek
  model: deepseek-chat
  reasoning: balanced
  credentials:
    source: env
    env_var: DEEPSEEK_API_KEY
```

### Local (Ollama)
```yaml
ai:
  provider: local
  model: llama3
  reasoning: balanced
  base_url: http://localhost:11434/v1
  credentials:
    source: skip
```

### None (Planning Only)
```yaml
ai:
  provider: none
  model: none
  reasoning: balanced
  credentials:
    source: skip
```

## Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY='sk-...'

# Anthropic
export ANTHROPIC_API_KEY='sk-ant-...'

# Google
export GOOGLE_API_KEY='...'

# DeepSeek
export DEEPSEEK_API_KEY='...'

# AWS Bedrock
export AWS_ACCESS_KEY_ID='...'
export AWS_SECRET_ACCESS_KEY='...'
export AWS_REGION='us-east-1'
```

## Common Tasks

### Change Model
```bash
# List available models
cloudops init  # Shows models during setup

# Update config
cloudops config ai.model claude-3-5-haiku-20241022
```

### Change Reasoning Mode
```bash
cloudops config ai.reasoning deep
```

### Enable Real Cloud APIs
```bash
cloudops config cloud.use_real_apis true
```

### View Audit Logs
```bash
# All logs
cloudops audit

# LLM calls only
cloudops audit --filter llm_call

# JSON format
cloudops audit --format json
```

### Test Without LLM
```bash
# Use planning-only mode
cloudops config ai.provider none

# Dry run
cloudops investigate "test query" --dry-run
```

## Troubleshooting

### "API key not configured"
```bash
# Check config
cloudops config ai.credentials.env_var

# Set environment variable
export ANTHROPIC_API_KEY='sk-ant-...'

# Verify
echo $ANTHROPIC_API_KEY
```

### "Provider not found"
```bash
# Check available providers
python3 -c "from cloudops.ai.registry import ModelRegistry; print(ModelRegistry.get_providers())"
```

### "Model not found"
```bash
# Check available models
python3 -c "from cloudops.ai.registry import ModelRegistry; print([m.id for m in ModelRegistry.get_models('anthropic')])"
```

### "Connection failed" (Local)
```bash
# Check if Ollama is running
curl http://localhost:11434/v1/models

# Start Ollama
ollama serve

# Pull model
ollama pull llama3
```

## Testing

### Run Tests
```bash
# All tests
python3 test_ai_onboarding.py

# Specific test
python3 -c "from test_ai_onboarding import test_model_registry; test_model_registry()"
```

### Manual Testing
```bash
# Test with mock provider
cloudops config ai.provider none
cloudops investigate "test" --dry-run

# Test with real provider (requires API key)
export ANTHROPIC_API_KEY='sk-ant-...'
cloudops config ai.provider anthropic
cloudops investigate "test query"
```

## Best Practices

### Security
- Never hardcode API keys
- Use environment variables
- Rotate keys regularly
- Use read-only mode by default

### Cost Management
- Use low-cost models for testing
- Monitor usage via audit logs
- Set max_tokens appropriately
- Use local models for development

### Reliability
- Validate credentials before use
- Handle API errors gracefully
- Implement retry logic
- Use mock mode for testing

### Maintainability
- Use provider interface only
- Don't hardcode provider logic
- Document model capabilities
- Test with multiple providers

## Resources

- [Full Documentation](AI_ONBOARDING.md)
- [Architecture Guide](PROVIDER_INTEGRATION.md)
- [Example Config](config.example.yaml)
- [Test Suite](test_ai_onboarding.py)

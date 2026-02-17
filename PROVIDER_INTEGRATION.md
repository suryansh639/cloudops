# AI Provider Integration Architecture

## Overview

This document describes the provider-agnostic AI architecture implemented in CloudOps, designed for enterprise production usage.

## Design Principles

### 1. Provider Agnostic
- No hardcoded provider logic in business code
- All providers implement the same interface
- Easy to add new providers without refactoring

### 2. Explicit Model Capabilities
- Each model declares its capabilities
- Context window, tool support, JSON mode, cost tier
- CLI filters models based on provider selection

### 3. Safe Defaults
- No write operations enabled by default
- Credentials validated at runtime, not during init
- Graceful failure when credentials missing

### 4. Separation of Concerns
- **Registry**: Model metadata and capabilities
- **Factory**: Provider instantiation
- **Providers**: LLM API implementations
- **Business Logic**: Uses provider interface only

### 5. Enterprise Ready
- Audit all LLM calls
- No secrets in config files
- Support for multiple credential sources
- Offline mode support

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Business Logic                       │
│              (IntentParser, PlanningEngine)             │
└────────────────────┬────────────────────────────────────┘
                     │ Uses LLMProvider interface
┌────────────────────▼────────────────────────────────────┐
│                  Provider Factory                       │
│         Creates provider from configuration             │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐
│   OpenAI     │ │ Anthropic │ │   Google   │
│   Provider   │ │  Provider │ │  Provider  │
└──────────────┘ └───────────┘ └────────────┘
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐
│  Bedrock     │ │ DeepSeek  │ │   Local    │
│  Provider    │ │  Provider │ │  Provider  │
└──────────────┘ └───────────┘ └────────────┘
```

## Component Details

### Model Registry (`cloudops/ai/registry.py`)

Central registry of all supported models and their capabilities.

**Key Classes:**
- `ModelInfo`: Model metadata (id, name, provider)
- `ModelCapabilities`: Technical capabilities
- `ModelRegistry`: Static registry with query methods

**Usage:**
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

**Adding Models:**
```python
"newprovider": [
    ModelInfo(
        id="model-id",
        name="Display Name",
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

### Provider Interface (`cloudops/ai/base.py`)

Abstract base class defining the provider contract.

**Interface:**
```python
class LLMProvider(ABC):
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        pass
    
    @abstractmethod
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
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        pass
```

**Response Format:**
```python
@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
```

### Provider Implementations (`cloudops/ai/providers.py`)

Concrete implementations for each provider.

**Structure:**
```python
class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
    
    def generate(self, prompt, *, system=None, tools=None, mode="balanced",
                 temperature=None, max_tokens=None) -> LLMResponse:
        # OpenAI-specific implementation
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        # ... API call ...
        return LLMResponse(content=..., model=self.model, provider="openai")
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)
```

**Key Points:**
- Each provider handles its own API client initialization
- Temperature mapping is provider-specific
- Validation is lightweight (no API calls)
- Error handling is provider-specific

### Provider Factory (`cloudops/ai/factory.py`)

Creates provider instances from configuration.

**Factory Pattern:**
```python
class ProviderFactory:
    PROVIDER_MAP = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        # ...
    }
    
    @classmethod
    def create(cls, provider: str, model: str, config: dict) -> LLMProvider:
        provider_class = cls.PROVIDER_MAP[provider]
        api_key = cls._get_api_key(config)
        kwargs = {}  # Provider-specific config
        return provider_class(model=model, api_key=api_key, **kwargs)
```

**Credential Resolution:**
```python
@classmethod
def _get_api_key(cls, config: dict) -> Optional[str]:
    creds = config.get("credentials", {})
    source = creds.get("source")
    
    if source == "env":
        env_var = creds.get("env_var")
        return os.getenv(env_var)
    elif source == "keychain":
        # Future: OS keychain integration
        raise NotImplementedError()
    elif source == "skip":
        return None
```

### CLI Onboarding (`cloudops/cli.py`)

Interactive wizard for configuration.

**Flow:**
1. Select provider from registry
2. Select model (filtered by provider)
3. Configure credentials (env/keychain/skip)
4. Select reasoning mode (fast/balanced/deep)
5. Provider-specific config (base_url, region, etc.)
6. Save to `~/.cloudops/config.yaml`

**Implementation:**
```python
@cli.command()
def init():
    # Step 1: Provider selection
    providers = ModelRegistry.get_providers()
    provider = prompt_choice(providers)
    
    # Step 2: Model selection
    models = ModelRegistry.get_models(provider)
    model = prompt_choice(models)
    
    # Step 3: Credentials
    cred_source = prompt_choice(["env", "keychain", "skip"])
    
    # Step 4: Reasoning mode
    mode = prompt_choice(["fast", "balanced", "deep"])
    
    # Step 5: Save config
    config = build_config(provider, model, cred_source, mode)
    save_config(config)
```

### Business Logic Integration (`cloudops/intent_parser.py`)

Business logic uses provider interface only.

**Before (Hardcoded):**
```python
class IntentParser:
    def __init__(self, config):
        self.client = Anthropic(api_key=config.get_api_key())
    
    def parse(self, query):
        response = self.client.messages.create(...)  # Anthropic-specific
```

**After (Provider-Agnostic):**
```python
class IntentParser:
    def __init__(self, config):
        ai_config = config.get("ai", {})
        provider = ai_config.get("provider")
        model = ai_config.get("model")
        self.provider = ProviderFactory.create(provider, model, ai_config)
        self.reasoning_mode = ai_config.get("reasoning", "balanced")
    
    def parse(self, query):
        response = self.provider.generate(  # Provider-agnostic
            prompt=query,
            system=system_prompt,
            mode=self.reasoning_mode
        )
```

## Configuration Format

### Structure
```yaml
ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  reasoning: balanced
  credentials:
    source: env
    env_var: ANTHROPIC_API_KEY
  # Provider-specific (optional)
  base_url: http://localhost:11434/v1  # For local
  region: us-east-1                     # For bedrock

cloud:
  primary: aws
  use_real_apis: false

policy:
  require_approval_for: [write, delete]
  auto_approve: [read]
```

### Credential Sources

**Environment Variable:**
```yaml
credentials:
  source: env
  env_var: ANTHROPIC_API_KEY
```

**OS Keychain (Future):**
```yaml
credentials:
  source: keychain
  keychain_service: cloudops
```

**Skip:**
```yaml
credentials:
  source: skip
```

## Security Model

### No Secrets in Config
- API keys stored in environment variables
- Config file contains only variable names
- Future: OS keychain integration

### Runtime Validation
- Credentials validated when used, not during init
- Graceful failure with clear error messages
- No API calls during validation

### Audit Trail
- Every LLM call logged with metadata
- Provider, model, timestamp, usage
- No prompts logged by default (configurable)

### Safe Defaults
- Read-only mode by default
- No write operations without approval
- Mock mode for testing

## Adding New Providers

### Step 1: Define Models in Registry

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

### Step 2: Implement Provider

```python
# cloudops/ai/providers.py
class NewProvider(LLMProvider):
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        # Provider-specific initialization
    
    def generate(self, prompt, *, system=None, tools=None, mode="balanced",
                 temperature=None, max_tokens=None) -> LLMResponse:
        # Implement API call
        # Return normalized LLMResponse
        pass
    
    def validate_credentials(self) -> bool:
        # Lightweight validation (no API call)
        return self.api_key is not None
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)
```

### Step 3: Register in Factory

```python
# cloudops/ai/factory.py
PROVIDER_MAP = {
    "newprovider": NewProvider,
}
```

### Step 4: Update Documentation

- Add to `AI_ONBOARDING.md`
- Add example to `config.example.yaml`
- Update README

## Testing

### Unit Tests
```bash
python3 test_ai_onboarding.py
```

Tests:
- Model registry queries
- Provider factory creation
- Credential source handling
- Provider validation
- Model capabilities
- Interface compliance

### Integration Tests
```bash
# Test with real provider (requires API key)
export ANTHROPIC_API_KEY='sk-ant-...'
cloudops investigate "test query"

# Test with mock provider
cloudops config ai.provider none
cloudops investigate "test query" --dry-run
```

### Manual Testing
```bash
# Initialize with different providers
cloudops init

# Verify configuration
cat ~/.cloudops/config.yaml

# Test investigation
cloudops investigate "high cpu on prod cluster"

# Check audit logs
cloudops audit --filter llm_call
```

## Troubleshooting

### Provider Not Found
```
ValueError: Unknown provider: xyz
```
**Solution:** Check `ModelRegistry.get_providers()` for supported providers.

### Credentials Not Configured
```
ValueError: API key not configured
```
**Solution:** Set environment variable specified in config.

### Model Not Supported
```
ValueError: Model not found
```
**Solution:** Check `ModelRegistry.get_models(provider)` for available models.

### Connection Failed (Local)
```
ConnectionError: Failed to connect to local model
```
**Solution:** Ensure Ollama/LM Studio is running and accessible.

## Performance Considerations

### Lazy Initialization
- Providers created on first use
- No API calls during init
- Fast startup time

### Connection Pooling
- SDK clients handle connection pooling
- No manual connection management

### Caching
- Model registry is static (no runtime queries)
- Provider instances can be reused

## Future Enhancements

### OS Keychain Integration
```python
# macOS Keychain
import keyring
api_key = keyring.get_password("cloudops", "anthropic")

# Windows Credential Manager
# Linux Secret Service
```

### Multi-Tenant Support
```bash
CLOUDOPS_CONFIG_PATH=~/.cloudops/team-a/config.yaml cloudops investigate "..."
```

### Cost Tracking
```python
# Track usage per provider
audit.log_llm_call(
    provider=provider,
    model=model,
    usage=response.usage,
    cost_estimate=calculate_cost(response.usage, model)
)
```

### Streaming Support
```python
def generate_stream(self, prompt, **kwargs) -> Iterator[str]:
    # Yield tokens as they arrive
    pass
```

### Tool/Function Calling
```python
tools = [
    {
        "name": "get_metrics",
        "description": "Get metrics from cloud provider",
        "parameters": {...}
    }
]

response = provider.generate(prompt, tools=tools)
```

## References

- [Model Registry](cloudops/ai/registry.py)
- [Provider Interface](cloudops/ai/base.py)
- [Provider Implementations](cloudops/ai/providers.py)
- [Provider Factory](cloudops/ai/factory.py)
- [CLI Onboarding](cloudops/cli.py)
- [Intent Parser](cloudops/intent_parser.py)
- [Example Config](config.example.yaml)
- [Onboarding Guide](AI_ONBOARDING.md)

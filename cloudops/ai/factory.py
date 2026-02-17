"""AI provider factory"""
import os
from typing import Optional
from cloudops.ai.base import LLMProvider
from cloudops.ai.providers import (
    OpenAIProvider, AnthropicProvider, GoogleProvider,
    BedrockProvider, DeepSeekProvider, LocalProvider, NoneProvider
)


class ProviderFactory:
    """Factory for creating LLM providers"""
    
    PROVIDER_MAP = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "bedrock": BedrockProvider,
        "deepseek": DeepSeekProvider,
        "local": LocalProvider,
        "none": NoneProvider,
    }
    
    @classmethod
    def create(cls, provider: str, model: str, config: dict) -> LLMProvider:
        """Create provider instance from configuration"""
        
        if provider not in cls.PROVIDER_MAP:
            raise ValueError(f"Unknown provider: {provider}")
        
        provider_class = cls.PROVIDER_MAP[provider]
        
        # Get API key from configured source
        api_key = cls._get_api_key(config)
        
        # Get additional config
        kwargs = {}
        if provider == "local":
            kwargs["base_url"] = config.get("base_url", "http://localhost:11434/v1")
        elif provider == "bedrock":
            kwargs["region"] = config.get("region", "us-east-1")
        
        return provider_class(model=model, api_key=api_key, **kwargs)
    
    @classmethod
    def _get_api_key(cls, config: dict) -> Optional[str]:
        """Get API key from configured source"""
        creds = config.get("credentials", {})
        source = creds.get("source")
        
        if source == "env":
            env_var = creds.get("env_var")
            if env_var:
                return os.getenv(env_var)
        
        elif source == "keychain":
            # Stub for OS keychain integration
            raise NotImplementedError("Keychain support not yet implemented")
        
        elif source == "skip":
            return None
        
        return None

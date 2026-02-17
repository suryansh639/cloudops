#!/usr/bin/env python3
"""Test AI provider onboarding system"""
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cloudops.ai.registry import ModelRegistry, CostTier
from cloudops.ai.factory import ProviderFactory
from cloudops.ai.providers import (
    OpenAIProvider, AnthropicProvider, GoogleProvider,
    BedrockProvider, DeepSeekProvider, LocalProvider, NoneProvider
)


def test_model_registry():
    """Test model registry functionality"""
    print("Testing Model Registry...")
    
    # Test get_providers
    providers = ModelRegistry.get_providers()
    assert len(providers) == 7, f"Expected 7 providers, got {len(providers)}"
    assert "openai" in providers
    assert "anthropic" in providers
    assert "google" in providers
    assert "bedrock" in providers
    assert "deepseek" in providers
    assert "local" in providers
    assert "none" in providers
    print("✓ All providers registered")
    
    # Test get_models
    openai_models = ModelRegistry.get_models("openai")
    assert len(openai_models) >= 3, "Expected at least 3 OpenAI models"
    print(f"✓ OpenAI has {len(openai_models)} models")
    
    anthropic_models = ModelRegistry.get_models("anthropic")
    assert len(anthropic_models) >= 3, "Expected at least 3 Anthropic models"
    print(f"✓ Anthropic has {len(anthropic_models)} models")
    
    # Test get_model
    model = ModelRegistry.get_model("anthropic", "claude-3-5-sonnet-20241022")
    assert model is not None
    assert model.name == "Claude 3.5 Sonnet"
    assert model.capabilities.context_window == 200000
    assert model.capabilities.supports_tools is True
    assert model.capabilities.cost_tier == CostTier.MEDIUM
    print("✓ Model lookup works")
    
    # Test get_default_model
    default = ModelRegistry.get_default_model("anthropic")
    assert default is not None
    assert default.capabilities.cost_tier in [CostTier.MEDIUM, CostTier.LOW]
    print(f"✓ Default model for Anthropic: {default.name}")
    
    print("✓ Model Registry tests passed\n")


def test_provider_factory():
    """Test provider factory"""
    print("Testing Provider Factory...")
    
    # Test OpenAI provider creation
    config = {
        "credentials": {
            "source": "env",
            "env_var": "OPENAI_API_KEY"
        }
    }
    provider = ProviderFactory.create("openai", "gpt-4o", config)
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-4o"
    print("✓ OpenAI provider created")
    
    # Test Anthropic provider creation
    config = {
        "credentials": {
            "source": "env",
            "env_var": "ANTHROPIC_API_KEY"
        }
    }
    provider = ProviderFactory.create("anthropic", "claude-3-5-sonnet-20241022", config)
    assert isinstance(provider, AnthropicProvider)
    print("✓ Anthropic provider created")
    
    # Test local provider with base_url
    config = {
        "base_url": "http://localhost:11434/v1",
        "credentials": {"source": "skip"}
    }
    provider = ProviderFactory.create("local", "llama3", config)
    assert isinstance(provider, LocalProvider)
    assert provider.base_url == "http://localhost:11434/v1"
    print("✓ Local provider created with custom base_url")
    
    # Test Bedrock provider with region
    config = {
        "region": "us-west-2",
        "credentials": {"source": "env", "env_var": "AWS_ACCESS_KEY_ID"}
    }
    provider = ProviderFactory.create("bedrock", "anthropic.claude-3-5-sonnet-20241022-v2:0", config)
    assert isinstance(provider, BedrockProvider)
    assert provider.config.get("region") == "us-west-2"
    print("✓ Bedrock provider created with region")
    
    # Test None provider
    config = {"credentials": {"source": "skip"}}
    provider = ProviderFactory.create("none", "none", config)
    assert isinstance(provider, NoneProvider)
    print("✓ None provider created")
    
    # Test invalid provider
    try:
        ProviderFactory.create("invalid", "model", {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown provider" in str(e)
        print("✓ Invalid provider rejected")
    
    print("✓ Provider Factory tests passed\n")


def test_credential_sources():
    """Test credential source handling"""
    print("Testing Credential Sources...")
    
    # Test env source
    os.environ["TEST_API_KEY"] = "test-key-123"
    config = {
        "credentials": {
            "source": "env",
            "env_var": "TEST_API_KEY"
        }
    }
    provider = ProviderFactory.create("openai", "gpt-4o", config)
    assert provider.api_key == "test-key-123"
    print("✓ Environment variable credential source works")
    
    # Test skip source
    config = {
        "credentials": {
            "source": "skip"
        }
    }
    provider = ProviderFactory.create("local", "llama3", config)
    assert provider.api_key is None
    print("✓ Skip credential source works")
    
    # Test missing env var
    config = {
        "credentials": {
            "source": "env",
            "env_var": "NONEXISTENT_KEY"
        }
    }
    provider = ProviderFactory.create("openai", "gpt-4o", config)
    assert provider.api_key is None
    print("✓ Missing environment variable handled gracefully")
    
    print("✓ Credential source tests passed\n")


def test_provider_validation():
    """Test provider credential validation"""
    print("Testing Provider Validation...")
    
    # OpenAI with key
    provider = OpenAIProvider("gpt-4o", api_key="sk-test")
    assert provider.validate_credentials() is True
    print("✓ OpenAI validates with key")
    
    # OpenAI without key
    provider = OpenAIProvider("gpt-4o", api_key=None)
    assert provider.validate_credentials() is False
    print("✓ OpenAI rejects without key")
    
    # Anthropic with valid key format
    provider = AnthropicProvider("claude-3-5-sonnet-20241022", api_key="sk-ant-test")
    assert provider.validate_credentials() is True
    print("✓ Anthropic validates with correct key format")
    
    # Anthropic with invalid key format
    provider = AnthropicProvider("claude-3-5-sonnet-20241022", api_key="invalid")
    assert provider.validate_credentials() is False
    print("✓ Anthropic rejects invalid key format")
    
    # Local provider (no validation needed)
    provider = LocalProvider("llama3", api_key=None)
    assert provider.validate_credentials() is True
    print("✓ Local provider always validates")
    
    # None provider (no validation needed)
    provider = NoneProvider("none", api_key=None)
    assert provider.validate_credentials() is True
    print("✓ None provider always validates")
    
    print("✓ Provider validation tests passed\n")


def test_model_capabilities():
    """Test model capability declarations"""
    print("Testing Model Capabilities...")
    
    # Test high-context models
    gemini = ModelRegistry.get_model("google", "gemini-1.5-pro")
    assert gemini.capabilities.context_window == 1000000
    print(f"✓ Gemini 1.5 Pro: {gemini.capabilities.context_window:,} tokens")
    
    # Test tool support
    gpt4 = ModelRegistry.get_model("openai", "gpt-4o")
    assert gpt4.capabilities.supports_tools is True
    print("✓ GPT-4o supports tools")
    
    # Test cost tiers
    haiku = ModelRegistry.get_model("anthropic", "claude-3-5-haiku-20241022")
    assert haiku.capabilities.cost_tier == CostTier.LOW
    print("✓ Haiku is low-cost tier")
    
    opus = ModelRegistry.get_model("anthropic", "claude-3-opus-20240229")
    assert opus.capabilities.cost_tier == CostTier.HIGH
    print("✓ Opus is high-cost tier")
    
    # Test JSON support
    for provider in ModelRegistry.get_providers():
        models = ModelRegistry.get_models(provider)
        for model in models:
            if provider != "none":
                assert model.capabilities.supports_json is True
    print("✓ All models support JSON mode")
    
    print("✓ Model capability tests passed\n")


def test_provider_agnostic_interface():
    """Test that all providers implement the same interface"""
    print("Testing Provider-Agnostic Interface...")
    
    providers = [
        ("openai", "gpt-4o", {"credentials": {"source": "skip"}}),
        ("anthropic", "claude-3-5-sonnet-20241022", {"credentials": {"source": "skip"}}),
        ("google", "gemini-1.5-pro", {"credentials": {"source": "skip"}}),
        ("deepseek", "deepseek-chat", {"credentials": {"source": "skip"}}),
        ("local", "llama3", {"credentials": {"source": "skip"}}),
        ("none", "none", {"credentials": {"source": "skip"}}),
    ]
    
    for provider_name, model, config in providers:
        provider = ProviderFactory.create(provider_name, model, config)
        
        # Check interface methods exist
        assert hasattr(provider, "generate")
        assert hasattr(provider, "validate_credentials")
        assert hasattr(provider, "model")
        assert hasattr(provider, "api_key")
        
        print(f"✓ {provider_name} implements LLMProvider interface")
    
    print("✓ Provider interface tests passed\n")


def test_reasoning_modes():
    """Test reasoning mode to temperature mapping"""
    print("Testing Reasoning Modes...")
    
    provider = OpenAIProvider("gpt-4o", api_key="test")
    
    assert provider._mode_to_temperature("fast") == 0.3
    assert provider._mode_to_temperature("balanced") == 0.0
    assert provider._mode_to_temperature("deep") == 0.0
    assert provider._mode_to_temperature("unknown") == 0.0  # Default
    
    print("✓ Reasoning mode mapping works")
    print("✓ Reasoning mode tests passed\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("CloudOps AI Provider Onboarding System Tests")
    print("=" * 60 + "\n")
    
    try:
        test_model_registry()
        test_provider_factory()
        test_credential_sources()
        test_provider_validation()
        test_model_capabilities()
        test_provider_agnostic_interface()
        test_reasoning_modes()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

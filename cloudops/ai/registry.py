"""AI model registry with provider capabilities"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class CostTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReasoningMode(Enum):
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


@dataclass
class ModelCapabilities:
    """Model capability definition"""
    context_window: int
    supports_tools: bool
    supports_json: bool
    cost_tier: CostTier
    max_tokens: int = 4096


@dataclass
class ModelInfo:
    """Model metadata"""
    id: str
    name: str
    provider: str
    capabilities: ModelCapabilities


class ModelRegistry:
    """Central registry of AI models and their capabilities"""
    
    MODELS: Dict[str, List[ModelInfo]] = {
        "openai": [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
                capabilities=ModelCapabilities(
                    context_window=128000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.HIGH,
                    max_tokens=4096
                )
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="openai",
                capabilities=ModelCapabilities(
                    context_window=128000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.HIGH,
                    max_tokens=4096
                )
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                capabilities=ModelCapabilities(
                    context_window=16385,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=4096
                )
            ),
        ],
        "anthropic": [
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                capabilities=ModelCapabilities(
                    context_window=200000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.MEDIUM,
                    max_tokens=8192
                )
            ),
            ModelInfo(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                provider="anthropic",
                capabilities=ModelCapabilities(
                    context_window=200000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.HIGH,
                    max_tokens=4096
                )
            ),
            ModelInfo(
                id="claude-3-5-haiku-20241022",
                name="Claude 3.5 Haiku",
                provider="anthropic",
                capabilities=ModelCapabilities(
                    context_window=200000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=8192
                )
            ),
        ],
        "google": [
            ModelInfo(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                provider="google",
                capabilities=ModelCapabilities(
                    context_window=1000000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.MEDIUM,
                    max_tokens=8192
                )
            ),
            ModelInfo(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                provider="google",
                capabilities=ModelCapabilities(
                    context_window=1000000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=8192
                )
            ),
        ],
        "bedrock": [
            ModelInfo(
                id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                name="Claude 3.5 Sonnet (Bedrock)",
                provider="bedrock",
                capabilities=ModelCapabilities(
                    context_window=200000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.MEDIUM,
                    max_tokens=4096
                )
            ),
            ModelInfo(
                id="meta.llama3-70b-instruct-v1:0",
                name="Llama 3 70B",
                provider="bedrock",
                capabilities=ModelCapabilities(
                    context_window=8192,
                    supports_tools=False,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=2048
                )
            ),
            ModelInfo(
                id="amazon.titan-text-premier-v1:0",
                name="Titan Text Premier",
                provider="bedrock",
                capabilities=ModelCapabilities(
                    context_window=32000,
                    supports_tools=False,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=3072
                )
            ),
        ],
        "deepseek": [
            ModelInfo(
                id="deepseek-chat",
                name="DeepSeek Chat",
                provider="deepseek",
                capabilities=ModelCapabilities(
                    context_window=64000,
                    supports_tools=True,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=4096
                )
            ),
        ],
        "local": [
            ModelInfo(
                id="local-model",
                name="Local Model (Ollama/LM Studio)",
                provider="local",
                capabilities=ModelCapabilities(
                    context_window=8192,
                    supports_tools=False,
                    supports_json=True,
                    cost_tier=CostTier.LOW,
                    max_tokens=2048
                )
            ),
        ],
        "none": [
            ModelInfo(
                id="none",
                name="None (Planning Only)",
                provider="none",
                capabilities=ModelCapabilities(
                    context_window=0,
                    supports_tools=False,
                    supports_json=False,
                    cost_tier=CostTier.LOW,
                    max_tokens=0
                )
            ),
        ],
    }
    
    @classmethod
    def get_providers(cls) -> List[str]:
        """Get list of supported providers"""
        return list(cls.MODELS.keys())
    
    @classmethod
    def get_models(cls, provider: str) -> List[ModelInfo]:
        """Get models for a specific provider"""
        return cls.MODELS.get(provider, [])
    
    @classmethod
    def get_model(cls, provider: str, model_id: str) -> Optional[ModelInfo]:
        """Get specific model info"""
        models = cls.get_models(provider)
        for model in models:
            if model.id == model_id:
                return model
        return None
    
    @classmethod
    def get_default_model(cls, provider: str) -> Optional[ModelInfo]:
        """Get recommended default model for provider"""
        models = cls.get_models(provider)
        if not models:
            return None
        
        # Prefer balanced cost/performance
        for model in models:
            if model.capabilities.cost_tier == CostTier.MEDIUM:
                return model
        
        # Fallback to first low-cost model
        for model in models:
            if model.capabilities.cost_tier == CostTier.LOW:
                return model
        
        return models[0]

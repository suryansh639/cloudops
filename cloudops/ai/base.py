"""AI provider base interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class LLMResponse:
    """Normalized LLM response"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """Abstract interface for LLM providers"""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        self.model = model
        self.api_key = api_key
        self.config = kwargs
    
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
        """Generate completion from prompt"""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check if credentials are valid (without making API call)"""
        pass

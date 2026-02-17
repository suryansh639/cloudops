"""AI provider implementations"""
from typing import Optional, List, Dict
from cloudops.ai.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        temp = temperature if temperature is not None else self._mode_to_temperature(mode)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tokens or 4096
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="openai",
            usage={"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens},
            finish_reason=response.choices[0].finish_reason
        )
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)


class AnthropicProvider(LLMProvider):
    """Anthropic provider implementation"""
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        client = Anthropic(api_key=self.api_key)
        
        temp = temperature if temperature is not None else self._mode_to_temperature(mode)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            temperature=temp,
            system=system or "",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            provider="anthropic",
            usage={"prompt_tokens": response.usage.input_tokens, "completion_tokens": response.usage.output_tokens},
            finish_reason=response.stop_reason
        )
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None and self.api_key.startswith("sk-ant-")
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)


class GoogleProvider(LLMProvider):
    """Google Gemini provider implementation"""
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature if temperature is not None else self._mode_to_temperature(mode),
                max_output_tokens=max_tokens or 8192
            )
        )
        
        return LLMResponse(
            content=response.text,
            model=self.model,
            provider="google",
            finish_reason="stop"
        )
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)


class BedrockProvider(LLMProvider):
    """AWS Bedrock provider implementation"""
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
        
        client = boto3.client('bedrock-runtime', region_name=self.config.get('region', 'us-east-1'))
        
        # Bedrock uses model-specific formats
        if "claude" in self.model:
            import json
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens or 4096,
                "temperature": temperature if temperature is not None else self._mode_to_temperature(mode),
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = client.invoke_model(modelId=self.model, body=body)
            result = json.loads(response['body'].read())
            
            return LLMResponse(
                content=result['content'][0]['text'],
                model=self.model,
                provider="bedrock",
                usage={"prompt_tokens": result['usage']['input_tokens'], "completion_tokens": result['usage']['output_tokens']}
            )
        else:
            raise NotImplementedError(f"Bedrock model {self.model} not yet supported")
    
    def validate_credentials(self) -> bool:
        # Bedrock uses AWS credentials, not API key
        return True
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)


class DeepSeekProvider(LLMProvider):
    """DeepSeek provider implementation"""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self.base_url = "https://api.deepseek.com/v1"
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")
        
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self._mode_to_temperature(mode),
            max_tokens=max_tokens or 4096
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="deepseek",
            usage={"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens}
        )
    
    def validate_credentials(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)


class LocalProvider(LLMProvider):
    """Local model provider (Ollama/LM Studio compatible)"""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "http://localhost:11434/v1")
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        client = OpenAI(api_key="not-needed", base_url=self.base_url)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self._mode_to_temperature(mode),
                max_tokens=max_tokens or 2048
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider="local"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to local model at {self.base_url}: {e}")
    
    def validate_credentials(self) -> bool:
        return True  # Local models don't need credentials
    
    def _mode_to_temperature(self, mode: str) -> float:
        return {"fast": 0.3, "balanced": 0.0, "deep": 0.0}.get(mode, 0.0)


class NoneProvider(LLMProvider):
    """No-op provider for planning-only mode"""
    
    def generate(self, prompt: str, *, system: Optional[str] = None, tools: Optional[List[Dict]] = None,
                 mode: str = "balanced", temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        raise RuntimeError("AI provider is set to 'none'. Cannot generate completions.")
    
    def validate_credentials(self) -> bool:
        return True

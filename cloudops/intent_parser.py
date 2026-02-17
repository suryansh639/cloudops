"""Intent parsing using LLM"""
import json
import uuid
from typing import Dict, Any
from pydantic import BaseModel, Field
from cloudops.ai.factory import ProviderFactory


class Target(BaseModel):
    resource_type: str
    scope: str
    filters: Dict[str, Any] = Field(default_factory=dict)


class Intent(BaseModel):
    intent_id: str
    intent_type: str
    target: Target
    goal: str
    constraints: Dict[str, Any]
    confidence: float


class IntentParser:
    def __init__(self, config):
        self.config = config
        
        # Get AI configuration
        ai_config = config.get("ai", {})
        provider = ai_config.get("provider")
        model = ai_config.get("model")
        
        if not provider or not model:
            raise ValueError("AI provider and model must be configured. Run 'cloudops init'")
        
        # Create provider instance using factory
        try:
            self.provider = ProviderFactory.create(provider, model, ai_config)
            self.reasoning_mode = ai_config.get("reasoning", "balanced")
        except Exception as e:
            raise ValueError(f"Failed to initialize AI provider: {e}")
    
    def parse(self, query: str, scope: str, read_only: bool) -> Intent:
        """Parse natural language query into structured intent"""
        
        system_prompt = """You are an intent parser for a cloud operations system.
Convert natural language queries into structured JSON intents.

Output ONLY valid JSON matching this schema:
{
  "intent_type": "investigate|remediate|describe|list",
  "target": {
    "resource_type": "kubernetes_cluster|ec2_instance|security_group|cost|deployment",
    "scope": "prod|dev|staging",
    "filters": {}
  },
  "goal": "identify_root_cause|optimize|audit|understand",
  "constraints": {
    "read_only": true|false,
    "max_cost_usd": 0.0
  },
  "confidence": 0.0-1.0
}

Examples:
Query: "investigate high cpu on prod cluster"
Output: {"intent_type": "investigate", "target": {"resource_type": "kubernetes_cluster", "scope": "prod", "filters": {"metric": "cpu_usage"}}, "goal": "identify_root_cause", "constraints": {"read_only": true, "max_cost_usd": 0.0}, "confidence": 0.95}

Query: "why is my aws bill higher this month"
Output: {"intent_type": "investigate", "target": {"resource_type": "cost", "scope": "prod", "filters": {"period": "month"}}, "goal": "identify_root_cause", "constraints": {"read_only": true, "max_cost_usd": 0.0}, "confidence": 0.90}

Query: "show risky security groups"
Output: {"intent_type": "list", "target": {"resource_type": "security_group", "scope": "prod", "filters": {"risk_level": "high"}}, "goal": "audit", "constraints": {"read_only": true, "max_cost_usd": 0.0}, "confidence": 0.92}"""

        user_prompt = f"Query: {query}\nScope: {scope}\nRead-only: {read_only}"
        
        # Use provider-agnostic interface
        response = self.provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            mode=self.reasoning_mode,
            max_tokens=1024
        )
        
        # Parse JSON response
        content = response.content.strip()
        # Handle markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        intent_data = json.loads(content)
        
        # Generate unique ID
        intent_data["intent_id"] = str(uuid.uuid4())
        
        # Override scope and read_only from CLI
        intent_data["target"]["scope"] = scope
        intent_data["constraints"]["read_only"] = read_only
        
        return Intent(**intent_data)

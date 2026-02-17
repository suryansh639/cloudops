"""Configuration management"""
import os
import yaml
from pathlib import Path
from typing import Optional


class Config:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.data = {}
        
    @classmethod
    def load(cls) -> "Config":
        config_path = Path.home() / ".cloudops" / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found at {config_path}")
        
        config = cls(config_path)
        with open(config_path) as f:
            config.data = yaml.safe_load(f)
        return config
    
    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.data, f, default_flow_style=False)
    
    def get(self, key: str, default=None):
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value):
        keys = key.split(".")
        data = self.data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
    
    def get_api_key(self) -> Optional[str]:
        source = self.get("llm.api_key_source", "")
        if source.startswith("env:"):
            env_var = source.split(":", 1)[1]
            return os.getenv(env_var)
        return source


def init_config(provider: str, model: str, api_key_source: str, cloud: str) -> Config:
    config_path = Path.home() / ".cloudops" / "config.yaml"
    config = Config(config_path)
    
    config.data = {
        "llm": {
            "provider": provider,
            "model": model,
            "api_key_source": api_key_source,
            "max_tokens": 4096,
            "temperature": 0.0
        },
        "cloud": {
            "primary": cloud
        },
        "policy": {
            "require_approval_for": ["write", "delete"],
            "auto_approve": ["read"],
            "scopes": {
                "prod": "require_approval",
                "dev": "auto_approve_reads"
            }
        }
    }
    
    config.save()
    
    # Create audit log directory
    (config_path.parent / "audit").mkdir(exist_ok=True)
    
    return config

"""Configuration management for Sekha CLI."""
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import yaml


class Config:
    """Sekha CLI configuration management."""
    
    DEFAULT_BASE_URL = "http://localhost:8080"
    
    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.api_key = api_key
        
        # Validate URL format
        try:
            result = urlparse(self.base_url)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"Invalid URL format: {self.base_url}")
            
            # Additional validation: scheme must be http/https
            if result.scheme not in ["http", "https"]:
                raise ValueError(f"URL scheme must be http or https: {self.base_url}")
                
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file."""
        config_path = config_path or cls._get_default_config_path()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        
        sekha_config = data.get("sekha", {})
        return cls(
            base_url=sekha_config.get("base_url", ""),
            api_key=sekha_config.get("api_key", "")
        )
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = config_path or self._get_default_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "sekha": {
                "base_url": self.base_url,
                "api_key": self.api_key
            }
        }
        
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    
    @classmethod
    def create_default(cls, config_path: Optional[Path] = None) -> "Config":
        """Create a default configuration file."""
        config = cls()
        config.save(config_path)
        return config
    
    @staticmethod
    def _get_default_config_path() -> Path:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".config" / "sekha"
        return config_dir / "config.yaml"
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.base_url and self.api_key)
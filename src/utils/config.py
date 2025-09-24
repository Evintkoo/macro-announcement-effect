"""
Configuration utilities for the macro announcement research project.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration manager for the research project."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        if config_path is None:
            # Get the project root directory
            self.project_root = Path(__file__).parent.parent.parent
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)
            self.project_root = config_path.parent.parent
            
        self.config_path = config_path
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dots).
        
        Args:
            key: Configuration key (e.g., 'data_sources.fred.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def get_data_dir(self, subdir: str = None) -> Path:
        """Get data directory path."""
        data_dir = self.project_root / "data"
        if subdir:
            data_dir = data_dir / subdir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_results_dir(self, subdir: str = None) -> Path:
        """Get results directory path."""
        results_dir = self.project_root / "results"
        if subdir:
            results_dir = results_dir / subdir
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir
    
    def get_api_key(self, service: str) -> str:
        """
        Get API key from environment variables.
        
        Args:
            service: Service name (e.g., 'fred', 'alpha_vantage')
            
        Returns:
            API key
            
        Raises:
            ValueError: If API key not found
        """
        key_mapping = {
            'fred': 'FRED_API_KEY',
            'alpha_vantage': 'ALPHA_VANTAGE_API_KEY',
            'coingecko': 'COINGECKO_API_KEY',
            'binance': 'BINANCE_API_KEY'
        }
        
        env_var = key_mapping.get(service.lower())
        if not env_var:
            raise ValueError(f"Unknown service: {service}")
            
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"API key not found for {service}. Please set {env_var} in your .env file.")
            
        return api_key

# Global configuration instance
config = Config()
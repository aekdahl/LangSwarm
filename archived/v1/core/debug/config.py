"""
Debug Configuration Management

This module provides centralized configuration management for debug operations,
including API keys, database connections, and project settings.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None
    organization: Optional[str] = None


@dataclass
class GoogleCloudConfig:
    """Google Cloud Platform configuration"""
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None
    service_account_key: Optional[Dict[str, Any]] = None


@dataclass
class BigQueryConfig:
    """BigQuery-specific configuration"""
    dataset_id: str = "vector_search"
    table_name: str = "embeddings"
    embedding_model: str = "text-embedding-3-small"
    max_results: int = 10
    similarity_threshold: float = 0.01


@dataclass
class DatabaseConfig:
    """General database configuration"""
    postgres_url: Optional[str] = None
    mysql_url: Optional[str] = None
    sqlite_path: Optional[str] = None


@dataclass
class DebugConfig:
    """Complete debug configuration"""
    openai: OpenAIConfig
    google_cloud: GoogleCloudConfig
    bigquery: BigQueryConfig
    database: DatabaseConfig
    output_dir: str = "debug_traces"
    log_level: str = "INFO"
    enable_file_logging: bool = True
    enable_console_logging: bool = True


class DebugConfigManager:
    """Manages debug configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[DebugConfig] = None
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path"""
        # Look for config in multiple locations
        possible_paths = [
            "debug_config.yaml",
            "debug_config.json", 
            "langswarm/core/debug/debug_config.yaml",
            "langswarm/core/debug/debug_config.json",
            os.path.expanduser("~/.langswarm/debug_config.yaml"),
            os.path.expanduser("~/.langswarm/debug_config.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Default to the debug module directory
        return str(Path(__file__).parent / "debug_config.yaml")
    
    def load_config(self) -> DebugConfig:
        """Load configuration from file with environment variable fallbacks"""
        if self._config is not None:
            return self._config
        
        # Start with default config
        config_data = self._get_default_config()
        
        # Load from file if it exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                
                # Deep merge file config with defaults
                config_data = self._deep_merge(config_data, file_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file {self.config_path}: {e}")
                print("Using defaults and environment variables...")
        
        # Apply environment variable overrides
        config_data = self._apply_env_overrides(config_data)
        
        # Create config objects with safe defaults
        self._config = DebugConfig(
            openai=OpenAIConfig(**config_data.get('openai', {})),
            google_cloud=GoogleCloudConfig(**config_data.get('google_cloud', {})),
            bigquery=BigQueryConfig(**config_data.get('bigquery', {})),
            database=DatabaseConfig(**(config_data.get('database') or {})),
            output_dir=config_data.get('output_dir', 'debug_traces'),
            log_level=config_data.get('log_level', 'INFO'),
            enable_file_logging=config_data.get('enable_file_logging', True),
            enable_console_logging=config_data.get('enable_console_logging', True)
        )
        
        return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure"""
        return {
            'openai': {
                'api_key': None,
                'model': 'gpt-4o-mini',
                'base_url': None,
                'organization': None
            },
            'google_cloud': {
                'project_id': None,
                'credentials_path': None,
                'service_account_key': None
            },
            'bigquery': {
                'dataset_id': 'vector_search',
                'table_name': 'embeddings',
                'embedding_model': 'text-embedding-3-small',
                'max_results': 10,
                'similarity_threshold': 0.7
            },
            'database': {
                'postgres_url': None,
                'mysql_url': None,
                'sqlite_path': None
            },
            'output_dir': 'debug_traces',
            'log_level': 'INFO',
            'enable_file_logging': True,
            'enable_console_logging': True
        }
    
    def _resolve_env_variables(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve ${VAR} style environment variables in config values"""
        import re
        
        def resolve_value(value):
            if isinstance(value, str):
                # Find ${VAR} patterns and replace with environment variables
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for match in matches:
                    env_value = os.getenv(match)
                    if env_value is not None:
                        value = value.replace(f'${{{match}}}', env_value)
                    else:
                        print(f"⚠️  Warning: Environment variable {match} not set")
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        return resolve_value(config_data)

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # First resolve ${VAR} style variables in the config
        config_data = self._resolve_env_variables(config_data)
        
        # Then apply direct environment variable overrides
        # OpenAI overrides
        if os.getenv('OPENAI_API_KEY'):
            config_data['openai']['api_key'] = os.getenv('OPENAI_API_KEY')
        if os.getenv('OPENAI_BASE_URL'):
            config_data['openai']['base_url'] = os.getenv('OPENAI_BASE_URL')
        if os.getenv('OPENAI_ORGANIZATION'):
            config_data['openai']['organization'] = os.getenv('OPENAI_ORGANIZATION')
        
        # Google Cloud overrides
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            config_data['google_cloud']['project_id'] = os.getenv('GOOGLE_CLOUD_PROJECT')
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            config_data['google_cloud']['credentials_path'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Database overrides
        if os.getenv('DATABASE_URL'):
            config_data['database']['postgres_url'] = os.getenv('DATABASE_URL')
        if os.getenv('POSTGRES_URL'):
            config_data['database']['postgres_url'] = os.getenv('POSTGRES_URL')
        if os.getenv('MYSQL_URL'):
            config_data['database']['mysql_url'] = os.getenv('MYSQL_URL')
        
        return config_data
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self, for_case: Optional[str] = None) -> tuple[bool, list[str]]:
        """Validate the configuration and return (is_valid, errors)
        
        Args:
            for_case: Optional case name to validate only relevant components
        """
        config = self.load_config()
        errors = []
        
        # Always check OpenAI since all cases use it
        if not config.openai.api_key:
            errors.append("OpenAI API key is required (set OPENAI_API_KEY or add to config)")
        
        # Only validate Google Cloud for BigQuery-related cases
        if for_case and 'bigquery' in for_case.lower():
            if not config.google_cloud.project_id:
                errors.append("Google Cloud project ID is required for BigQuery (set GOOGLE_CLOUD_PROJECT or add to config)")
            
            # Check if credentials file exists (if specified)
            if config.google_cloud.credentials_path and not os.path.exists(config.google_cloud.credentials_path):
                errors.append(f"Google Cloud credentials file not found: {config.google_cloud.credentials_path}")
            
            # Note: We don't require explicit credentials since gcloud auth is sufficient
        
        return len(errors) == 0, errors
    
    def create_sample_config(self, output_path: Optional[str] = None) -> str:
        """Create a sample configuration file"""
        output_path = output_path or self.config_path
        
        sample_config = {
            "# LangSwarm Debug Configuration": None,
            "# This file configures debug operations including API keys, databases, and project settings": None,
            "# You can also use environment variables which will override these settings": None,
            "": None,
            "openai": {
                "api_key": "your-openai-api-key-here",
                "model": "gpt-4o-mini",
                "base_url": "null  # Optional: custom OpenAI base URL",
                "organization": "null  # Optional: OpenAI organization ID"
            },
            "": None,
            "google_cloud": {
                "project_id": "your-gcp-project-id",
                "credentials_path": "/path/to/your/service-account.json",
                "service_account_key": "null  # Alternative: inline service account JSON"
            },
            "": None,
            "bigquery": {
                "dataset_id": "my_dataset",
                "table_name": "embeddings", 
                "embedding_model": "text-embedding-3-small",
                "max_results": 10,
                "similarity_threshold": 0.01
            },
            "": None,
            "database": {
                "postgres_url": "null  # Optional: PostgreSQL connection URL",
                "mysql_url": "null     # Optional: MySQL connection URL", 
                "sqlite_path": "null   # Optional: SQLite database path"
            },
            "": None,
            "# Debug Output Settings": None,
            "output_dir": "debug_traces",
            "log_level": "INFO",
            "enable_file_logging": True,
            "enable_console_logging": True
        }
        
        # Clean up the sample config (remove comment keys)
        clean_config = {}
        for key, value in sample_config.items():
            if not key.startswith('#') and key != '':
                clean_config[key] = value
        
        # Write the file
        with open(output_path, 'w') as f:
            # Write comments manually for better formatting
            f.write("# LangSwarm Debug Configuration\n")
            f.write("# This file configures debug operations including API keys, databases, and project settings\n")
            f.write("# You can also use environment variables which will override these settings\n\n")
            
            yaml.dump(clean_config, f, default_flow_style=False, indent=2)
        
        return output_path
    
    def get_config(self) -> DebugConfig:
        """Get the current configuration (alias for load_config)"""
        return self.load_config()
    
    def set_environment_variables(self):
        """Set environment variables from config (useful for subprocess calls)"""
        config = self.load_config()
        
        if config.openai.api_key:
            os.environ['OPENAI_API_KEY'] = config.openai.api_key
        
        if config.google_cloud.project_id:
            os.environ['GOOGLE_CLOUD_PROJECT'] = config.google_cloud.project_id
        
        if config.google_cloud.credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.google_cloud.credentials_path


# Global configuration manager instance
_config_manager: Optional[DebugConfigManager] = None


def get_debug_config(config_path: Optional[str] = None) -> DebugConfig:
    """Get the debug configuration (creates manager if needed)"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = DebugConfigManager(config_path)
    
    return _config_manager.get_config()


def validate_debug_config(config_path: Optional[str] = None, for_case: Optional[str] = None) -> tuple[bool, list[str]]:
    """Validate debug configuration"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = DebugConfigManager(config_path)
    
    return _config_manager.validate_config(for_case=for_case)


def create_sample_debug_config(output_path: Optional[str] = None) -> str:
    """Create a sample debug configuration file"""
    manager = DebugConfigManager()
    return manager.create_sample_config(output_path)


def set_debug_environment_variables(config_path: Optional[str] = None):
    """Set environment variables from debug config"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = DebugConfigManager(config_path)
    
    _config_manager.set_environment_variables()

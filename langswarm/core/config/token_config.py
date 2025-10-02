"""
LangSwarm V2 Token Tracking Configuration System

Provides easy configuration loading and management for token tracking features
with support for different deployment environments and custom settings.
"""

import os
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

from ..observability.token_tracking import TokenBudgetConfig, CompressionUrgency
from ..errors import ConfigurationError

logger = logging.getLogger(__name__)


class TokenTrackingConfig:
    """Configuration manager for token tracking system"""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize token tracking configuration.
        
        Args:
            config_data: Configuration dictionary or None to load from default
        """
        self._config = config_data or {}
        self._model_pricing = {}
        self._context_limits = {}
        
        # Load default configuration if not provided
        if not config_data:
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration from YAML file"""
        try:
            config_path = self._get_config_path()
            if config_path.exists():
                with open(config_path, 'r') as f:
                    full_config = yaml.safe_load(f)
                    
                # Extract relevant sections
                self._model_pricing = full_config.get('model_pricing', {})
                self._context_limits = full_config.get('model_context_limits', {})
                
                # Load production config as default
                self._config = full_config.get('production', {})
                
                logger.info("Loaded default token tracking configuration")
            else:
                # STRICT MODE: No fallbacks - fail if config file not found
                raise ConfigurationError("Token tracking configuration file not found. Please create a valid token configuration file.")
                
        except Exception as e:
            # STRICT MODE: No fallbacks - fail on any loading error
            raise ConfigurationError(f"Failed to load token tracking config: {e}") from e
    
    def _get_config_path(self) -> Path:
        """Get path to configuration file"""
        # Try environment variable first
        config_path = os.getenv('LANGSWARM_TOKEN_CONFIG')
        if config_path:
            return Path(config_path)
        
        # Try relative to current module
        current_dir = Path(__file__).parent
        config_path = current_dir / "token_tracking_config.yaml"
        if config_path.exists():
            return config_path
        
        # Try project root
        project_root = current_dir.parent.parent.parent.parent
        config_path = project_root / "langswarm" / "v2" / "config" / "token_tracking_config.yaml"
        
        return config_path
    
    def _get_minimal_defaults(self) -> Dict[str, Any]:
        """Get minimal default configuration"""
        return {
            "observability": {
                "enabled": True,
                "log_level": "INFO",
                "metrics_enabled": True,
                "tracing_enabled": False
            },
            "token_tracking": {
                "enabled": True,
                "budget_enforcement": False,
                "context_monitoring": True,
                "budget_limits": {
                    "daily_token_limit": 100000,
                    "session_token_limit": 10000,
                    "cost_limit_usd": 10.0
                },
                "alerts": {
                    "token_alert_threshold": 0.8,
                    "cost_alert_threshold": 0.8,
                    "context_alert_threshold": 0.9
                },
                "enforcement": {
                    "enforce_limits": False,
                    "auto_compress_context": True,
                    "compression_threshold": 0.85
                }
            }
        }
    
    @classmethod
    def from_environment(cls, environment: str = "production") -> "TokenTrackingConfig":
        """
        Load configuration for specific environment.
        
        Args:
            environment: Environment name (production, development, testing, etc.)
        
        Returns:
            TokenTrackingConfig instance
        """
        instance = cls()
        
        try:
            config_path = instance._get_config_path()
            if config_path.exists():
                with open(config_path, 'r') as f:
                    full_config = yaml.safe_load(f)
                
                env_config = full_config.get(environment)
                if env_config:
                    instance._config = env_config
                    instance._model_pricing = full_config.get('model_pricing', {})
                    instance._context_limits = full_config.get('model_context_limits', {})
                    logger.info(f"Loaded {environment} token tracking configuration")
                else:
                    # STRICT MODE: No fallbacks - fail if environment not found
                    raise ConfigurationError(f"Environment '{environment}' not found in token tracking configuration")
            
        except Exception as e:
            # STRICT MODE: No fallbacks - fail on any loading error
            raise ConfigurationError(f"Failed to load {environment} config: {e}") from e
        
        return instance
    
    @classmethod
    def from_file(cls, config_file: Union[str, Path]) -> "TokenTrackingConfig":
        """
        Load configuration from specific file.
        
        Args:
            config_file: Path to configuration file
        
        Returns:
            TokenTrackingConfig instance
        """
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            logger.info(f"Loaded token tracking configuration from {config_file}")
            return cls(config_data)
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            return cls()  # Return with defaults
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TokenTrackingConfig":
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
        
        Returns:
            TokenTrackingConfig instance
        """
        return cls(config_dict)
    
    # Configuration accessors
    
    def is_enabled(self) -> bool:
        """Check if token tracking is enabled"""
        return self._config.get("token_tracking", {}).get("enabled", True)
    
    def is_budget_enforcement_enabled(self) -> bool:
        """Check if budget enforcement is enabled"""
        return self._config.get("token_tracking", {}).get("budget_enforcement", False)
    
    def is_context_monitoring_enabled(self) -> bool:
        """Check if context monitoring is enabled"""
        return self._config.get("token_tracking", {}).get("context_monitoring", True)
    
    def get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration"""
        return self._config.get("observability", {})
    
    def get_token_tracking_config(self) -> Dict[str, Any]:
        """Get token tracking configuration"""
        return self._config.get("token_tracking", {})
    
    def get_budget_config(self) -> TokenBudgetConfig:
        """Get token budget configuration as structured object"""
        token_config = self.get_token_tracking_config()
        budget_limits = token_config.get("budget_limits", {})
        alerts = token_config.get("alerts", {})
        enforcement = token_config.get("enforcement", {})
        
        return TokenBudgetConfig(
            daily_token_limit=budget_limits.get("daily_token_limit"),
            session_token_limit=budget_limits.get("session_token_limit"),
            hourly_token_limit=budget_limits.get("hourly_token_limit"),
            cost_limit_usd=budget_limits.get("cost_limit_usd"),
            token_alert_threshold=alerts.get("token_alert_threshold", 0.8),
            cost_alert_threshold=alerts.get("cost_alert_threshold", 0.8),
            enforce_limits=enforcement.get("enforce_limits", False),
            auto_compress_context=enforcement.get("auto_compress_context", True),
            compression_threshold=enforcement.get("compression_threshold", 0.85)
        )
    
    def get_model_pricing(self, provider: str, model: str) -> Optional[Dict[str, float]]:
        """
        Get pricing information for a specific model.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            model: Model name
        
        Returns:
            Dictionary with 'input' and 'output' pricing per 1K tokens
        """
        return self._model_pricing.get(provider, {}).get(model)
    
    def get_context_limit(self, provider: str, model: str) -> int:
        """
        Get context window limit for a specific model.
        
        Args:
            provider: Provider name
            model: Model name
        
        Returns:
            Context limit in tokens
        """
        return self._context_limits.get(provider, {}).get(model, 
               self._context_limits.get('default', 4096))
    
    def estimate_cost(
        self, 
        provider: str, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            provider: Provider name
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Estimated cost in USD
        """
        pricing = self.get_model_pricing(provider, model)
        if not pricing:
            return 0.0
        
        input_cost = (input_tokens / 1000) * pricing.get("input", 0)
        output_cost = (output_tokens / 1000) * pricing.get("output", 0)
        
        return input_cost + output_cost
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self._deep_update(self._config, updates)
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            "config": self._config,
            "model_pricing": self._model_pricing,
            "context_limits": self._context_limits
        }
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: Path to save configuration
        """
        try:
            config_data = self.to_dict()
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved token tracking configuration to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise


# Predefined configuration factories
def get_production_config() -> TokenTrackingConfig:
    """Get production configuration"""
    return TokenTrackingConfig.from_environment("production")


def get_development_config() -> TokenTrackingConfig:
    """Get development configuration"""
    return TokenTrackingConfig.from_environment("development")


def get_testing_config() -> TokenTrackingConfig:
    """Get testing configuration (minimal tracking)"""
    return TokenTrackingConfig.from_environment("testing")


def get_enterprise_config() -> TokenTrackingConfig:
    """Get enterprise configuration (high-volume)"""
    return TokenTrackingConfig.from_environment("enterprise")


def get_research_config() -> TokenTrackingConfig:
    """Get research configuration (no enforcement, full tracking)"""
    return TokenTrackingConfig.from_environment("research")


def get_demo_config() -> TokenTrackingConfig:
    """Get demo configuration (low limits, early alerts)"""
    return TokenTrackingConfig.from_environment("demo")


def get_migration_config() -> TokenTrackingConfig:
    """Get migration configuration (gradual enablement)"""
    return TokenTrackingConfig.from_environment("migration")


# Environment detection
def detect_environment() -> str:
    """
    Detect current environment from environment variables or defaults.
    
    Returns:
        Environment name
    """
    # Check explicit environment variable
    env = os.getenv('LANGSWARM_ENV', '').lower()
    if env in ['production', 'prod']:
        return 'production'
    elif env in ['development', 'dev']:
        return 'development'
    elif env in ['testing', 'test']:
        return 'testing'
    elif env in ['staging', 'stage']:
        return 'staging'
    elif env == 'enterprise':
        return 'enterprise'
    elif env == 'research':
        return 'research'
    elif env == 'demo':
        return 'demo'
    
    # Check other common environment indicators
    if os.getenv('DEBUG') == 'true' or os.getenv('FLASK_ENV') == 'development':
        return 'development'
    elif os.getenv('TESTING') == 'true' or os.getenv('PYTEST_CURRENT_TEST'):
        return 'testing'
    
    # Default to development for safety
    return 'development'


def get_auto_config() -> TokenTrackingConfig:
    """
    Automatically detect environment and return appropriate configuration.
    
    Returns:
        TokenTrackingConfig for detected environment
    """
    environment = detect_environment()
    logger.info(f"Auto-detected environment: {environment}")
    return TokenTrackingConfig.from_environment(environment)


# Configuration validation
def validate_config(config: TokenTrackingConfig) -> List[str]:
    """
    Validate token tracking configuration.
    
    Args:
        config: Configuration to validate
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check basic structure
    if not isinstance(config._config, dict):
        errors.append("Configuration must be a dictionary")
        return errors
    
    token_config = config.get_token_tracking_config()
    
    # Validate budget limits
    budget_limits = token_config.get("budget_limits", {})
    
    if budget_limits.get("daily_token_limit") and budget_limits["daily_token_limit"] <= 0:
        errors.append("Daily token limit must be positive")
    
    if budget_limits.get("session_token_limit") and budget_limits["session_token_limit"] <= 0:
        errors.append("Session token limit must be positive")
    
    if budget_limits.get("cost_limit_usd") and budget_limits["cost_limit_usd"] <= 0:
        errors.append("Cost limit must be positive")
    
    # Validate alert thresholds
    alerts = token_config.get("alerts", {})
    
    for threshold_name in ["token_alert_threshold", "cost_alert_threshold", "context_alert_threshold"]:
        threshold = alerts.get(threshold_name, 0.8)
        if not 0.0 <= threshold <= 1.0:
            errors.append(f"{threshold_name} must be between 0.0 and 1.0")
    
    # Validate enforcement settings
    enforcement = token_config.get("enforcement", {})
    compression_threshold = enforcement.get("compression_threshold", 0.85)
    
    if not 0.0 <= compression_threshold <= 1.0:
        errors.append("Compression threshold must be between 0.0 and 1.0")
    
    return errors

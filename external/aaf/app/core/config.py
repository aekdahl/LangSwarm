"""
AAF Backend Configuration Management
"""
import os
from typing import List, Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LangSwarm Configuration
    langswarm_config_path: str = Field(
        default="/app/config/langswarm.yaml",
        env="LANGSWARM_CONFIG_PATH"
    )
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Google Cloud Configuration
    google_application_credentials: Optional[str] = Field(
        default=None, env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_cloud_project: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    bigquery_dataset_id: str = Field(
        default="aaf_chatbot_memory", env="BIGQUERY_DATASET_ID"
    )
    bigquery_table_id: str = Field(
        default="conversations", env="BIGQUERY_TABLE_ID"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Session Configuration
    session_backend: str = Field(default="bigquery", env="SESSION_BACKEND")
    session_ttl: int = Field(default=3600, env="SESSION_TTL")
    
    # FastAPI Configuration
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    app_reload: bool = Field(default=False, env="APP_RELOAD")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"], env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(
        default=True, env="CORS_ALLOW_CREDENTIALS"
    )
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"], env="CORS_ALLOW_HEADERS"
    )
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Cloud Run Configuration
    port: int = Field(default=8080, env="PORT")
    
    # WebSocket Configuration
    websocket_cors_origins: List[str] = Field(
        default=["*"], env="WEBSOCKET_CORS_ORIGINS"
    )
    
    # Management API Configuration
    management_api_enabled: bool = Field(
        default=True, env="MANAGEMENT_API_ENABLED"
    )
    management_api_secret: str = Field(..., env="MANAGEMENT_API_SECRET")
    
    # Agent Configuration
    default_agent_model: str = Field(
        default="gpt-4", env="DEFAULT_AGENT_MODEL"
    )
    default_agent_behavior: str = Field(
        default="helpful", env="DEFAULT_AGENT_BEHAVIOR"
    )
    default_system_prompt: str = Field(
        default="You are a helpful AI assistant for customer support. Be professional, concise, and helpful.",
        env="DEFAULT_SYSTEM_PROMPT"
    )
    
    # Memory Configuration
    memory_enabled: bool = Field(default=True, env="MEMORY_ENABLED")
    memory_backend: str = Field(default="bigquery", env="MEMORY_BACKEND")
    memory_auto_store: bool = Field(default=True, env="MEMORY_AUTO_STORE")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Web scraping configuration
    crawl4ai_base_url: Optional[str] = Field(default=None, env="CRAWL4AI_BASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_langswarm_config() -> Dict[str, Any]:
    """Load LangSwarm configuration with environment variable substitution"""
    import yaml
    from string import Template
    
    config_path = Path(settings.langswarm_config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"LangSwarm config not found: {config_path}")
    
    # Read the YAML file
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    # Substitute environment variables
    template = Template(config_content)
    substituted_content = template.safe_substitute(os.environ)
    
    # Parse the substituted YAML
    config = yaml.safe_load(substituted_content)
    
    # Normalize agent tool configurations for compatibility
    if 'agents' in config:
        for agent in config['agents']:
            if 'tools' in agent and isinstance(agent['tools'], list):
                # Convert complex tool objects to simple tool IDs
                normalized_tools = []
                for tool in agent['tools']:
                    if isinstance(tool, dict):
                        # Extract tool ID/name from complex object
                        tool_id = tool.get('name') or tool.get('id', '')
                        if tool_id:
                            normalized_tools.append(tool_id)
                    elif isinstance(tool, str):
                        # Already a string, use as-is
                        normalized_tools.append(tool)
                agent['tools'] = normalized_tools
                # Log the normalization for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Normalized tools for agent {agent.get('id')}: {normalized_tools}")
    
    return config


def update_langswarm_config(new_config: Dict[str, Any]) -> None:
    """Update LangSwarm configuration file"""
    import yaml
    
    config_path = Path(settings.langswarm_config_path)
    
    # Ensure the directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the new configuration
    with open(config_path, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False, indent=2)

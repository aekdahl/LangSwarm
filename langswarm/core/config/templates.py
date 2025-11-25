"""
Standard configuration templates for LangSwarm agents and tools.
These templates provide a starting point for code-first configuration.
"""

from typing import Dict, Any, List

def basic_agent_config(
    model: str = "gpt-4-turbo-preview",
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Basic agent configuration template"""
    return {
        "model": model,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "max_tokens": 4096,
        "timeout": 30,
        "retry_attempts": 3
    }

def tool_enabled_agent_config(
    tools: List[str],
    tool_configs: Dict[str, Dict[str, Any]] = None,
    model: str = "gpt-4-turbo-preview"
) -> Dict[str, Any]:
    """Agent configuration with tools enabled"""
    return {
        "model": model,
        "system_prompt": "You are a helpful assistant with access to tools.",
        "temperature": 0.5,  # Lower temperature for better tool use
        "tools_enabled": True,
        "available_tools": tools,
        "tool_configs": tool_configs or {}
    }

def memory_enabled_agent_config(
    model: str = "gpt-4-turbo-preview"
) -> Dict[str, Any]:
    """Agent configuration with memory enabled"""
    return {
        "model": model,
        "system_prompt": "You are a helpful assistant with memory of our conversation.",
        "memory_enabled": True,
        "max_memory_messages": 50,
        "memory_summary_enabled": True
    }

# Tool Configuration Templates

def bigquery_config(
    project_id: str,
    dataset_id: str,
    location: str = "US"
) -> Dict[str, Any]:
    """Configuration for BigQuery tool"""
    return {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "location": location
    }

def daytona_config(
    api_key: str,
    server_url: str,
    target: str = "local"
) -> Dict[str, Any]:
    """Configuration for Daytona tool"""
    return {
        "api_key": api_key,
        "server_url": server_url,
        "target": target
    }

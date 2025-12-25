"""
LangSwarm - Simple Multi-Agent AI Framework

Build powerful multi-agent AI systems with just a few lines of code.

Quick Start:
    from langswarm import create_agent
    
    # Create an agent
    agent = create_agent(model="gpt-3.5-turbo")
    response = await agent.chat("Hello!")
    
    # With memory
    agent = create_agent(model="gpt-4", memory=True)
    
    # Load from configuration
    config = load_config("langswarm.yaml")
    agent = config.get_agent("assistant")
"""

# Dynamic version from package metadata (single source of truth: pyproject.toml)
from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("langswarm")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"  # Fallback for development/editable installs

# Simple API - primary interface for most users
try:
    from langswarm.simple_api import (
        create_agent,
        create_workflow,
        load_config,
        Agent,
        Workflow,
        Config
    )
except ImportError:
    # Fallback during development
    pass

# Advanced API - for power users
try:
    from langswarm.core.agents import (
        create_openai_agent,
        create_anthropic_agent,
        create_gemini_agent,
        AgentBuilder
    )
except (ImportError, AttributeError):
    pass

try:
    from langswarm.core.config import (
        LangSwarmConfig
    )
except (ImportError, AttributeError):
    pass

try:
    from langswarm.core.workflows import (
        get_workflow_engine,
        WorkflowBuilder
    )
except (ImportError, AttributeError):
    # Skip advanced workflows if there are import issues
    pass

# Core session management
try:
    from langswarm.core.session.storage import SessionStorage
    from langswarm.core.session.interfaces import SessionProvider
except (ImportError, AttributeError):
    # Define minimal fallbacks
    class SessionStorage:
        pass
    class SessionProvider:
        pass

__all__ = [
    # Simple API (recommended)
    'create_agent',
    'create_workflow', 
    'load_config',
    'Agent',
    'Workflow',
    'Config',
    
    # Core components
    'SessionStorage',
    'SessionProvider',
    
    # Version
    '__version__'
]
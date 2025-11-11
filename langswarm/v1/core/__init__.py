"""
LangSwarm Core Module

This module provides the main interfaces for LangSwarm functionality.
During V2 migration, this module provides smart routing between V1 and V2 implementations.
"""

import os
import warnings
from typing import TYPE_CHECKING, Optional, Any

# V2 Availability Check
try:
    from ..v2.core.agents import AgentBuilder, BaseAgent
    from ..v2.core.config import ConfigurationManager
    from ..v2.core.middleware import Pipeline
    from ..v2.core.workflows import WorkflowBuilder
    from ..v2.tools import ToolRegistry
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False

# V1 Legacy Imports
from .wrappers import AgentWrapper as _V1AgentWrapper
from .factory import AgentFactory as _V1AgentFactory

try:
    from .config import Config as _V1Config
except ImportError:
    _V1Config = None


def get_feature_flag(flag_name: str, default: bool = False) -> bool:
    """Get feature flag from environment or configuration"""
    env_var = f"LANGSWARM_{flag_name.upper()}"
    return os.getenv(env_var, str(default)).lower() in ('true', '1', 'yes', 'on')


class SmartAgentWrapper:
    """Smart wrapper that routes between V1 and V2 agent implementations"""
    
    def __new__(cls, *args, **kwargs):
        # Check for explicit V2 request
        use_v2 = kwargs.pop('use_v2', None)
        if use_v2 is None:
            use_v2 = get_feature_flag('USE_V2_AGENTS', False)
        
        if use_v2 and V2_AVAILABLE:
            # Route to V2 with migration warning
            warnings.warn(
                "Using V2 agent system. This will become the default in the next release.",
                FutureWarning,
                stacklevel=2
            )
            # Convert V1-style kwargs to V2 builder pattern
            return cls._create_v2_agent(*args, **kwargs)
        else:
            # Use V1 implementation
            return _V1AgentWrapper(*args, **kwargs)
    
    @staticmethod
    def _create_v2_agent(*args, **kwargs):
        """Convert V1 parameters to V2 AgentBuilder pattern"""
        builder = AgentBuilder()
        
        # Map common V1 parameters to V2 builder methods
        if 'name' in kwargs:
            builder = builder.name(kwargs['name'])
        if 'model' in kwargs:
            builder = builder.model(kwargs['model'])
        if 'provider' in kwargs:
            if kwargs['provider'].lower() == 'openai':
                builder = builder.openai()
            elif kwargs['provider'].lower() == 'anthropic':
                builder = builder.anthropic()
        if 'system_prompt' in kwargs:
            builder = builder.system_prompt(kwargs['system_prompt'])
        if 'tools' in kwargs:
            builder = builder.tools(kwargs['tools'])
        
        return builder.build()


class SmartConfig:
    """Smart configuration that routes between V1 and V2 config systems"""
    
    def __new__(cls, *args, **kwargs):
        use_v2 = kwargs.pop('use_v2', None)
        if use_v2 is None:
            use_v2 = get_feature_flag('USE_V2_CONFIG', False)
        
        if use_v2 and V2_AVAILABLE:
            warnings.warn(
                "Using V2 configuration system. This will become the default in the next release.",
                FutureWarning,
                stacklevel=2
            )
            return ConfigurationManager(*args, **kwargs)
        else:
            if _V1Config:
                return _V1Config(*args, **kwargs)
            else:
                raise ImportError("V1 Config not available and V2 not enabled")


# Main exports - Smart routing during migration
AgentWrapper = SmartAgentWrapper
AgentFactory = _V1AgentFactory  # Keep V1 for now
Config = SmartConfig

# V2 exports (when available)
if V2_AVAILABLE:
    # V2 native classes for new development
    AgentBuilder = AgentBuilder
    BaseAgent = BaseAgent
    ConfigurationManager = ConfigurationManager
    WorkflowBuilder = WorkflowBuilder
    Pipeline = Pipeline
    ToolRegistry = ToolRegistry
    
    # Convenience aliases
    Agent = AgentBuilder  # Shorter name for new code
    Configuration = ConfigurationManager
    Workflow = WorkflowBuilder

# Legacy V1 exports
from .wrappers import *
from .factory import *

# Migration utilities
def enable_v2_globally():
    """Enable V2 implementations globally for this session"""
    os.environ['LANGSWARM_USE_V2_AGENTS'] = 'true'
    os.environ['LANGSWARM_USE_V2_CONFIG'] = 'true'
    print("✅ V2 implementations enabled globally")

def disable_v2_globally():
    """Disable V2 implementations globally for this session"""
    os.environ['LANGSWARM_USE_V2_AGENTS'] = 'false'
    os.environ['LANGSWARM_USE_V2_CONFIG'] = 'false'
    print("✅ V1 implementations enabled globally")

def get_version_info():
    """Get information about available versions and current configuration"""
    return {
        'v2_available': V2_AVAILABLE,
        'v2_agents_enabled': get_feature_flag('USE_V2_AGENTS'),
        'v2_config_enabled': get_feature_flag('USE_V2_CONFIG'),
        'environment_flags': {
            k: v for k, v in os.environ.items() 
            if k.startswith('LANGSWARM_')
        }
    }

__all__ = [
    # Main interfaces (smart routing)
    'AgentWrapper',
    'AgentFactory', 
    'Config',
    
    # V2 interfaces (when available)
    'AgentBuilder',
    'BaseAgent',
    'ConfigurationManager',
    'WorkflowBuilder',
    'Pipeline',
    'ToolRegistry',
    
    # Convenience aliases
    'Agent',
    'Configuration',
    'Workflow',
    
    # Migration utilities
    'enable_v2_globally',
    'disable_v2_globally',
    'get_version_info'
]
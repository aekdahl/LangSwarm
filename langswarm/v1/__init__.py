"""
LangSwarm V1 (with automatic compatibility patches)

This module provides LangSwarm V1 functionality with automatic fixes for:
- Modern LangChain compatibility (0.3.x+)
- UTF-8 encoding (Swedish and all international characters)

Usage:
    from langswarm.v1.core.config import LangSwarmConfigLoader
    # Patches are applied automatically when AgentWrapper is first used!

Patches fix:
1. LangChain API: .run() → .invoke() compatibility
2. UTF-8 encoding: ö→f6, ä→e4, å→e5 corruption

For V2 (recommended), use: from langswarm.core import ...
"""

__version__ = "0.0.54.dev46"

import logging

logger = logging.getLogger(__name__)

# Import patches module (will apply later when AgentWrapper is actually used)
from . import _patches

# Patches are applied lazily when AgentWrapper is first imported/used
# This avoids import errors if V1 dependencies aren't fully present

# Export commonly used V1 modules for convenience
# Users can still do: from langswarm.v1.core.config import LangSwarmConfigLoader
__all__ = ['__version__', '_patches']


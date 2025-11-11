"""
LangSwarm V1 Compatibility Package

Automatic patches for LangSwarm V1 to work with modern dependencies:
1. LangChain 0.3.x+ compatibility (.invoke() vs .run())
2. UTF-8 encoding fixes (Swedish characters and all international text)

Usage:
    # Just import the package - patches auto-apply!
    import langswarm_v1_compat
    
    # Or explicitly apply:
    import langswarm_v1_compat
    langswarm_v1_compat.apply()
    
    # Then use LangSwarm V1 normally
    from archived.v1.core.config import LangSwarmConfigLoader
    # ... rest of your V1 code

Auto-applies on import by default (can be disabled with environment variable).
"""

__version__ = "1.0.0"
__author__ = "LangSwarm Team"
__license__ = "MIT"

import os
import sys
import logging

logger = logging.getLogger(__name__)

# Import the patch functions
from .patches import (
    patch_agent_wrapper_call_agent,
    patch_agent_wrapper_parse_response,
    apply_all_patches,
    is_applied
)

# Export public API
__all__ = [
    'apply',
    'is_applied',
    'patch_agent_wrapper_call_agent',
    'patch_agent_wrapper_parse_response',
    '__version__'
]


def apply():
    """
    Apply all V1 compatibility patches.
    
    This is safe to call multiple times - patches are only applied once.
    
    Returns:
        bool: True if patches were applied successfully
    """
    return apply_all_patches()


# Auto-apply on import (can be disabled with env var)
_AUTO_APPLY = os.getenv('LANGSWARM_V1_COMPAT_DISABLE_AUTO_APPLY', '').lower() not in ('1', 'true', 'yes')

if _AUTO_APPLY and not is_applied():
    logger.info("Auto-applying LangSwarm V1 compatibility patches...")
    if apply():
        logger.info("✅ LangSwarm V1 compatibility patches applied successfully")
    else:
        logger.warning("⚠️  Some patches failed to apply - check logs for details")


"""
LangSwarm Workflow Utilities - V2/V1 Compatibility Layer

This module provides a compatibility shim for workflow utilities.
"""

# V2/V1 compatibility for workflows utilities
try:
    # Try V2 first (primary)
    from langswarm.core.v2.utils.workflows import *
except ImportError:
    # Fall back to V1
    from langswarm.v1.core.utils.workflows import *


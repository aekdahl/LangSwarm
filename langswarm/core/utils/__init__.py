"""
LangSwarm Core Utils - V2/V1 Compatibility Layer

This module provides a compatibility shim that routes imports to V2 (primary)
or falls back to V1 implementations when V2 is not available.
"""

# V2/V1 compatibility shim
try:
    # Try V2 first (primary)
    from langswarm.core.v2.utils import *
except ImportError:
    # Fall back to V1
    try:
        from langswarm.v1.core.utils import *
    except ImportError:
        # Neither available - minimal environment
        pass


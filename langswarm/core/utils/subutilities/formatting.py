"""
Formatting Utilities - V2/V1 Compatibility Shim

Routes Formatting import to V2 or V1 implementation.
"""

# Route Formatting import
try:
    # Try V2 first (primary)
    from langswarm.core.v2.utils.subutilities.formatting import Formatting
except ImportError:
    # Fall back to V1
    from langswarm.v1.core.utils.subutilities.formatting import Formatting

__all__ = ['Formatting']


"""
Workflow Functions - V2/V1 Compatibility Shim

Routes workflow functions import to V2 or V1 implementation.
"""

# Route workflow functions import
try:
    # Try V2 first (primary)
    from langswarm.core.v2.utils.workflows.functions import *
except ImportError:
    # Fall back to V1
    from langswarm.v1.core.utils.workflows.functions import *


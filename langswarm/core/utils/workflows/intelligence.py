"""
WorkflowIntelligence - V2/V1 Compatibility Shim

Routes WorkflowIntelligence import to V2 or V1 implementation.
"""

# Route WorkflowIntelligence import
try:
    # Try V2 first (primary)
    from langswarm.core.v2.utils.workflows.intelligence import WorkflowIntelligence
except ImportError:
    # Fall back to V1
    from langswarm.v1.core.utils.workflows.intelligence import WorkflowIntelligence

__all__ = ['WorkflowIntelligence']


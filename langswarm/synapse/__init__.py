"""
Synapse Compatibility Layer

Re-exports Synapse components from V1 for use by V2 tools.
"""

try:
    from langswarm.v1.synapse import *
except ImportError:
    pass


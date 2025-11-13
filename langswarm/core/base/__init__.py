"""
V1 Backward Compatibility - Base Module

Re-exports V1 base classes (GlobalLogger, LLM) for backward compatibility.
Many docs and user code import from langswarm.core.base.
"""

# Re-export all V1 base module components
try:
    from langswarm.v1.core.base import *
    from langswarm.v1.core.base.log import GlobalLogger
    from langswarm.v1.core.base.bot import LLM
    
    __all__ = ['GlobalLogger', 'LLM']
except ImportError:
    # V1 not available - graceful fallback
    GlobalLogger = None
    LLM = None
    __all__ = []


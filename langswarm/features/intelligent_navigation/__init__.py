"""
LangSwarm Intelligent Workflow Navigation

This module provides AI-driven workflow step selection, allowing agents to
dynamically choose the next workflow step based on context and conditions.

Features:
- Agent-driven step selection
- Navigation decision tracking
- Conditional workflow routing
- Analytics and optimization
- Bring-your-own-LLM compatible

Author: LangSwarm Team
Version: 0.1.0
"""

from .navigator import WorkflowNavigator, NavigationTool
from .tracker import NavigationTracker, NavigationAnalytics
from .config import NavigationConfig, NavigationStep
from .exceptions import NavigationError, InvalidStepError, NoAvailableStepsError

__version__ = "0.1.0"
__all__ = [
    "WorkflowNavigator",
    "NavigationTool", 
    "NavigationTracker",
    "NavigationAnalytics",
    "NavigationConfig",
    "NavigationStep",
    "NavigationError",
    "InvalidStepError",
    "NoAvailableStepsError"
] 
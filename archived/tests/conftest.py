"""
Global pytest configuration for LangSwarm tests
Ensures proper test isolation by cleaning up global state between tests
"""

import pytest
import os
import gc
from unittest.mock import patch


@pytest.fixture(autouse=True)
def test_isolation():
    """Automatically ensure test isolation by cleaning up global state"""
    # Store original environment state
    original_env = os.environ.copy()
    
    yield  # Run the test
    
    # Cleanup after test
    try:
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(original_env)
        
        # Clean up global logger state
        try:
            from langswarm.core.base.log import GlobalLogger
            GlobalLogger._instance = None
            GlobalLogger._langsmith_tracer = None
        except (ImportError, AttributeError):
            pass
        
        # Clean up environment detector cache
        try:
            from langswarm.core.detection import EnvironmentDetector
            if hasattr(EnvironmentDetector, '_cached_environment'):
                EnvironmentDetector._cached_environment = None
        except (ImportError, AttributeError):
            pass
        
        # Clean up any session state
        try:
            from langswarm.core.session.manager import SessionManager
            # Reset any singleton instances
            if hasattr(SessionManager, '_instances'):
                SessionManager._instances.clear()
        except (ImportError, AttributeError):
            pass
        
        # Force garbage collection to clean up lingering references
        gc.collect()
        
    except Exception:
        # Don't let cleanup failures break tests
        pass


@pytest.fixture(autouse=True)
def reset_patches():
    """Ensure all patches are properly cleaned up"""
    yield
    # Stop any lingering patches
    patch.stopall() 
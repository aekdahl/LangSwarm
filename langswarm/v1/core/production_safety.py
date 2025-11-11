"""
Production Safety Module for LangSwarm

This module provides critical fixes for circular reference issues that cause
RecursionError in production container environments.
"""

import os
import gc
import sys
import logging
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)

class ProductionSafetyManager:
    """
    Production-safe wrapper for LangSwarm initialization and operation.
    
    Provides protection against circular reference issues that cause
    RecursionError in container environments.
    """
    
    def __init__(self):
        self.is_production = self._detect_production_environment()
        self.original_recursion_limit = sys.getrecursionlimit()
        
        if self.is_production:
            self._apply_production_optimizations()
    
    def _detect_production_environment(self) -> bool:
        """Detect if running in a production container environment"""
        production_indicators = [
            'CLOUD_RUN_SERVICE',
            'K_SERVICE', 
            'KUBERNETES_SERVICE_HOST',
            'CONTAINER_ID',
            'DOCKER_CONTAINER'
        ]
        
        return any(os.getenv(var) for var in production_indicators)
    
    def _apply_production_optimizations(self):
        """Apply production-specific optimizations"""
        logger.info("🐳 Production environment detected - applying safety optimizations")
        
        # Conservative recursion limit for containers
        sys.setrecursionlimit(min(self.original_recursion_limit, 1500))
        
        # Aggressive garbage collection in memory-constrained environments
        gc.set_threshold(100, 10, 10)
        
        # Reduce verbosity of libraries that trigger object introspection
        logging.getLogger('pydantic').setLevel(logging.ERROR)
        logging.getLogger('google.cloud').setLevel(logging.WARNING)
        
        # Set optimization flags
        os.environ['PYTHONOPTIMIZE'] = '1'
        
        logger.info(f"✅ Production optimizations applied (recursion_limit={sys.getrecursionlimit()})")
    
    def safe_workflow_executor_creation(self, workflows, agents, tools=None, max_retries=3):
        """
        Create WorkflowExecutor with production safety measures.
        
        This method implements retry logic and graceful degradation to handle
        circular reference issues in production environments.
        """
        from langswarm.v1.core.config import WorkflowExecutor
        
        logger.info("🔄 Creating WorkflowExecutor with production safety measures")
        
        for attempt in range(max_retries):
            try:
                # Force garbage collection before attempt
                gc.collect()
                
                if tools:
                    logger.info(f"🔧 Attempt {attempt + 1}: Creating WorkflowExecutor with {len(tools)} tools")
                    executor = WorkflowExecutor(workflows, agents, tools=tools)
                    
                    # Verify tools are properly registered
                    if hasattr(executor, 'tools') and executor.tools:
                        logger.info(f"✅ WorkflowExecutor created successfully with {len(executor.tools)} tools")
                        return executor
                    else:
                        logger.warning("⚠️ Tools parameter accepted but no tools registered")
                else:
                    logger.info(f"🔧 Attempt {attempt + 1}: Creating WorkflowExecutor without tools")
                    executor = WorkflowExecutor(workflows, agents)
                    logger.info("✅ WorkflowExecutor created successfully without tools")
                    return executor
                    
            except RecursionError as e:
                logger.warning(f"🔄 Attempt {attempt + 1}: RecursionError occurred - {str(e)[:100]}...")
                
                if attempt < max_retries - 1:
                    # Exponential backoff with cleanup
                    wait_time = 0.2 * (2 ** attempt)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
                    # Aggressive cleanup
                    gc.collect()
                    
                    # Try without tools on final attempt
                    if attempt == max_retries - 2 and tools:
                        logger.warning("🔄 Final attempt will be without tools (graceful degradation)")
                        tools = None
                else:
                    logger.error("❌ All attempts failed - could not create WorkflowExecutor")
                    raise
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error during WorkflowExecutor creation: {e}")
                raise
        
        # Should not reach here
        raise RuntimeError("Failed to create WorkflowExecutor after all attempts")
    
    def cleanup(self):
        """Restore original settings"""
        if self.is_production:
            sys.setrecursionlimit(self.original_recursion_limit)
            logger.info("🔄 Production optimizations reverted")

# Global production safety manager instance
_safety_manager: Optional[ProductionSafetyManager] = None

def get_production_safety_manager() -> ProductionSafetyManager:
    """Get or create the global production safety manager"""
    global _safety_manager
    if _safety_manager is None:
        _safety_manager = ProductionSafetyManager()
    return _safety_manager

# NOTE: The safe_workflow_executor_creation function was removed because
# WorkflowExecutor now handles all safety measures automatically.
# No separate "safe" method is needed.

def optimize_for_production():
    """Apply production optimizations immediately"""
    manager = get_production_safety_manager()
    # Manager already applies optimizations on creation
    return manager

# Auto-apply optimizations when module is imported in production
if any(os.getenv(var) for var in ['CLOUD_RUN_SERVICE', 'K_SERVICE', 'KUBERNETES_SERVICE_HOST']):
    get_production_safety_manager()

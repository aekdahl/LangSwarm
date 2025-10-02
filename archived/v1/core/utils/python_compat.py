#!/usr/bin/env python3
"""
Python 3.11+ Compatibility Utilities
===================================

This module provides compatibility utilities for Python 3.11 and 3.12,
ensuring LangSwarm works across different Python versions.

Key fixes:
- AsyncIO event loop management
- Async context manager patterns
- OpenAI client compatibility
- Import system differences
"""

import sys
import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, Coroutine, Optional, Union
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Python version detection
PYTHON_VERSION = sys.version_info
IS_PYTHON_311_PLUS = PYTHON_VERSION >= (3, 11)
IS_PYTHON_312_PLUS = PYTHON_VERSION >= (3, 12)

logger.info(f"Python version detected: {PYTHON_VERSION}")
if IS_PYTHON_311_PLUS:
    logger.info("Using Python 3.11+ compatibility mode")


class AsyncContextManager:
    """
    Python 3.11+ compatible async context manager for OpenAI clients.
    
    Handles the OpenAI client lifecycle changes in newer Python versions.
    """
    
    def __init__(self, client_factory: Callable):
        self.client_factory = client_factory
        self.client = None
    
    async def __aenter__(self):
        self.client = self.client_factory()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client and hasattr(self.client, 'close'):
            try:
                await self.client.close()
            except Exception as e:
                logger.warning(f"Error closing async client: {e}")
        elif self.client and hasattr(self.client, 'aclose'):
            try:
                await self.client.aclose()
            except Exception as e:
                logger.warning(f"Error closing async client with aclose: {e}")


class EventLoopManager:
    """
    Python 3.11+ compatible event loop management.
    
    Handles the stricter event loop requirements in newer Python versions.
    """
    
    @staticmethod
    def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
        """
        Get or create an event loop in a Python 3.11+ compatible way.
        """
        try:
            # Try to get the running loop first (3.11+ preferred)
            if IS_PYTHON_311_PLUS:
                return asyncio.get_running_loop()
            else:
                return asyncio.get_event_loop()
        except RuntimeError:
            # No running loop, create a new one
            if IS_PYTHON_311_PLUS:
                # In 3.11+, be more explicit about loop creation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
            else:
                return asyncio.new_event_loop()
    
    @staticmethod
    def run_async_in_sync_context(coro: Coroutine) -> Any:
        """
        Run an async coroutine in a sync context, compatible with Python 3.11+.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        try:
            # Check if we're already in an async context
            try:
                asyncio.get_running_loop()
                # We're in an async context - use thread pool
                logger.debug("Running async coroutine in thread pool (async context detected)")
                
                def _run_in_thread():
                    # Create new loop in thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                
                # Use thread pool for execution
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_run_in_thread)
                    return future.result(timeout=300)  # 5 minute timeout
                    
            except RuntimeError:
                # No running loop - safe to use asyncio.run
                logger.debug("Running async coroutine with asyncio.run")
                if IS_PYTHON_311_PLUS:
                    # Python 3.11+ prefer asyncio.Runner for better resource management
                    try:
                        with asyncio.Runner() as runner:
                            return runner.run(coro)
                    except AttributeError:
                        # Fallback for older 3.11 versions
                        return asyncio.run(coro)
                else:
                    return asyncio.run(coro)
                    
        except Exception as e:
            logger.error(f"Failed to run async coroutine: {e}")
            raise


class OpenAIClientFactory:
    """
    Python 3.11+ compatible OpenAI client factory.
    
    Handles the client creation and lifecycle changes in newer versions.
    """
    
    @staticmethod
    def create_sync_client(api_key: str, **kwargs):
        """Create a synchronous OpenAI client."""
        import openai
        return openai.OpenAI(api_key=api_key, **kwargs)
    
    @staticmethod
    def create_async_client(api_key: str, **kwargs):
        """Create an asynchronous OpenAI client with proper context management."""
        import openai
        return openai.AsyncOpenAI(api_key=api_key, **kwargs)
    
    @staticmethod
    def get_async_context_manager(api_key: str, **kwargs):
        """Get an async context manager for OpenAI client."""
        return AsyncContextManager(
            lambda: OpenAIClientFactory.create_async_client(api_key, **kwargs)
        )


def async_to_sync(func: Callable) -> Callable:
    """
    Decorator to convert async function to sync, compatible with Python 3.11+.
    
    This handles the stricter async requirements in newer Python versions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return EventLoopManager.run_async_in_sync_context(coro)
    
    return wrapper


def safe_gather(*coroutines, return_exceptions: bool = True):
    """
    Python 3.11+ compatible asyncio.gather with better error handling.
    
    Args:
        *coroutines: Coroutines to gather
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results or exceptions
    """
    async def _safe_gather():
        try:
            if IS_PYTHON_311_PLUS:
                # Python 3.11+ has stricter exception handling
                results = await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
                return results
            else:
                # Older Python versions
                return await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
        except Exception as e:
            logger.error(f"asyncio.gather failed: {e}")
            if return_exceptions:
                return [e] * len(coroutines)
            else:
                raise
    
    return _safe_gather()


def get_python_version_info() -> dict:
    """Get detailed Python version information for debugging."""
    return {
        "version": str(PYTHON_VERSION),
        "version_info": PYTHON_VERSION,
        "is_311_plus": IS_PYTHON_311_PLUS,
        "is_312_plus": IS_PYTHON_312_PLUS,
        "implementation": sys.implementation.name,
        "platform": sys.platform,
        "asyncio_version": getattr(asyncio, '__version__', 'unknown')
    }


# Export compatibility utilities
__all__ = [
    'AsyncContextManager',
    'EventLoopManager', 
    'OpenAIClientFactory',
    'async_to_sync',
    'safe_gather',
    'get_python_version_info',
    'IS_PYTHON_311_PLUS',
    'IS_PYTHON_312_PLUS'
]

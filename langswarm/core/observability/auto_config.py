"""
Automatic configuration for Langfuse observability.
"""
import os
import logging
from langswarm.core.utils.optional_imports import optional_import

logger = logging.getLogger(__name__)

def auto_configure_langfuse():
    """
    Automatically configure LangFuse observability if environment variables are set.
    
    Checks for:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    
    If credentials are found, registers LangFuse callbacks with LiteLLM.
    This function is safe to call even if litellm or langfuse are not installed.
    """
    # Check credentials first to avoid unnecessary imports
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    
    if not public_key or not secret_key:
        return

    # Try to import litellm
    litellm = optional_import("litellm")
    if not litellm:
        return

    try:
        # Verify langfuse is installed
        import langfuse
        
        # Initialize callback lists if needed
        if not isinstance(litellm.success_callback, list):
            litellm.success_callback = []
        if not isinstance(litellm.failure_callback, list):
            litellm.failure_callback = []
        
        # Register LangFuse
        if "langfuse" not in litellm.success_callback:
            litellm.success_callback.append("langfuse")
            logger.debug("Registered Langfuse success callback")
            
        if "langfuse" not in litellm.failure_callback:
            litellm.failure_callback.append("langfuse")
            logger.debug("Registered Langfuse failure callback")
            
        # Optional: Set host if provided
        host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL")
        if host:
            os.environ["LANGFUSE_HOST"] = host
            
        logger.info(f"✅ LangFuse observability automatically enabled for LiteLLM")
            
    except ImportError:
        logger.debug("LangFuse credentials present but 'langfuse' package not installed")
    except Exception as e:
        logger.warning(f"Failed to auto-configure LangFuse: {e}")

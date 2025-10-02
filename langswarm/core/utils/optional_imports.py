"""
Optional Import Utilities for LangSwarm

Provides a centralized system for handling optional dependencies with helpful error messages.
This allows LangSwarm to have a minimal core installation while supporting rich integrations.
"""

import importlib
from typing import Any, Optional, Dict, Set
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class OptionalImportError(ImportError):
    """Custom error for missing optional dependencies with installation guidance."""
    
    def __init__(self, package_name: str, extra_name: Optional[str] = None, feature_name: Optional[str] = None):
        self.package_name = package_name
        self.extra_name = extra_name
        self.feature_name = feature_name
        
        # Create helpful error message
        feature_context = f" for {feature_name}" if feature_name else ""
        
        # Always recommend direct package installation first
        install_cmd = f"pip install {package_name}"
        
        # Build the error message
        message = (
            f"❌ Package '{package_name}' is required{feature_context} but not installed.\n\n"
            f"📦 To use this feature, install the required package:\n"
            f"   {install_cmd}\n"
        )
        
        # Add alternative for full installation
        if extra_name:
            message += (
                f"\n💡 Or install all {extra_name} dependencies:\n"
                f"   pip install langswarm[full]\n"
            )
        
        # Add documentation link if available
        doc_links = {
            'openai': 'https://docs.langswarm.ai/providers/openai',
            'anthropic': 'https://docs.langswarm.ai/providers/anthropic',
            'google.generativeai': 'https://docs.langswarm.ai/providers/google',
            'redis': 'https://docs.langswarm.ai/memory/redis',
            'chromadb': 'https://docs.langswarm.ai/memory/chromadb',
            'fastapi': 'https://docs.langswarm.ai/web-api',
            'discord': 'https://docs.langswarm.ai/platforms/discord',
        }
        
        if package_name in doc_links:
            message += f"\n📚 See setup guide: {doc_links[package_name]}"
        
        super().__init__(message)


class OptionalImportManager:
    """Manages optional imports with caching and helpful error messages."""
    
    def __init__(self):
        self._import_cache: Dict[str, Any] = {}
        self._failed_imports: Set[str] = set()
        
        # Define dependency groups and their purposes
        self.dependency_groups = {
            # Core AI/ML providers
            'openai': {
                'packages': ['openai'],
                'extra': None,  # No extra group needed - install directly
                'description': 'OpenAI API integration (GPT-4, GPT-3.5-turbo)'
            },
            'anthropic': {
                'packages': ['anthropic'],
                'extra': 'providers',
                'description': 'Anthropic Claude API integration'
            },
            'google': {
                'packages': ['google.generativeai'],
                'extra': 'providers',
                'description': 'Google Gemini API integration'
            },
            'cohere': {
                'packages': ['cohere'],
                'extra': 'providers',
                'description': 'Cohere API integration'
            },
            'mistral': {
                'packages': ['mistralai'],
                'extra': 'providers', 
                'description': 'Mistral AI API integration'
            },
            
            # Memory backends
            'redis': {
                'packages': ['redis', 'aioredis'],
                'extra': 'memory',
                'description': 'Redis memory backend'
            },
            'chromadb': {
                'packages': ['chromadb'],
                'extra': 'memory',
                'description': 'ChromaDB vector store'
            },
            'qdrant': {
                'packages': ['qdrant_client'],
                'extra': 'memory',
                'description': 'Qdrant vector store'
            },
            'pinecone': {
                'packages': ['pinecone'],
                'extra': 'memory',
                'description': 'Pinecone vector store'
            },
            'postgres': {
                'packages': ['psycopg2', 'asyncpg'],
                'extra': 'memory',
                'description': 'PostgreSQL memory backend'
            },
            
            # Cloud integrations
            'bigquery': {
                'packages': ['google.cloud.bigquery', 'google.cloud.bigquery_storage'],
                'extra': 'cloud',
                'description': 'Google BigQuery integration'
            },
            'pubsub': {
                'packages': ['google.cloud.pubsub'],
                'extra': 'cloud', 
                'description': 'Google Pub/Sub messaging'
            },
            'aws': {
                'packages': ['boto3'],
                'extra': 'cloud',
                'description': 'AWS services integration'
            },
            
            # Communication platforms
            'discord': {
                'packages': ['discord'],
                'extra': 'platforms',
                'description': 'Discord bot integration'
            },
            'telegram': {
                'packages': ['telegram'],
                'extra': 'platforms',
                'description': 'Telegram bot integration'
            },
            'slack': {
                'packages': ['slack_bolt'],
                'extra': 'platforms',
                'description': 'Slack app integration'
            },
            'twilio': {
                'packages': ['twilio'],
                'extra': 'platforms',
                'description': 'Twilio communication services'
            },
            
            # Web frameworks
            'fastapi': {
                'packages': ['fastapi', 'uvicorn'],
                'extra': 'web',
                'description': 'FastAPI web framework'
            },
            'flask': {
                'packages': ['flask'],
                'extra': 'web',
                'description': 'Flask web framework'
            },
            
            # ML/AI frameworks
            'langchain': {
                'packages': ['langchain', 'langchain_community', 'langchain_openai'],
                'extra': 'frameworks',
                'description': 'LangChain framework integration'
            },
            'llamaindex': {
                'packages': ['llama_index'],
                'extra': 'frameworks',
                'description': 'LlamaIndex framework integration'
            },
            'transformers': {
                'packages': ['transformers'],
                'extra': 'ml',
                'description': 'Hugging Face Transformers'
            },
            
            # Multimodal
            'vision': {
                'packages': ['PIL', 'cv2'],
                'extra': 'multimodal',
                'description': 'Image processing capabilities'
            },
            'audio': {
                'packages': ['speech_recognition', 'pydub'],
                'extra': 'multimodal', 
                'description': 'Audio processing capabilities'
            },
            
            # Development tools
            'jupyter': {
                'packages': ['ipython', 'ipywidgets'],
                'extra': 'dev',
                'description': 'Jupyter notebook integration'
            }
        }
    
    def try_import(self, package_name: str, feature_name: Optional[str] = None) -> Any:
        """
        Try to import a package, returning None if not available.
        
        Args:
            package_name: The package to import (e.g., 'openai', 'redis')
            feature_name: Human-readable feature name for error messages
            
        Returns:
            The imported module or None if not available
        """
        if package_name in self._import_cache:
            return self._import_cache[package_name]
        
        if package_name in self._failed_imports:
            return None
        
        try:
            module = importlib.import_module(package_name)
            self._import_cache[package_name] = module
            logger.debug(f"Successfully imported optional dependency: {package_name}")
            return module
        except ImportError:
            self._failed_imports.add(package_name)
            logger.debug(f"Optional dependency not available: {package_name}")
            return None
    
    def require_import(self, package_name: str, feature_name: Optional[str] = None) -> Any:
        """
        Import a package, raising OptionalImportError if not available.
        
        Args:
            package_name: The package to import
            feature_name: Human-readable feature name for error messages
            
        Returns:
            The imported module
            
        Raises:
            OptionalImportError: If the package is not available
        """
        module = self.try_import(package_name, feature_name)
        if module is None:
            # Find the dependency group for better error messages
            extra_name = None
            for group_name, group_info in self.dependency_groups.items():
                if package_name in group_info['packages']:
                    extra_name = group_info['extra']
                    break
            
            raise OptionalImportError(package_name, extra_name, feature_name)
        
        return module
    
    def is_available(self, package_name: str) -> bool:
        """Check if a package is available without importing it."""
        if package_name in self._import_cache:
            return True
        if package_name in self._failed_imports:
            return False
        
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            self._failed_imports.add(package_name)
            return False
    
    def get_available_features(self) -> Dict[str, bool]:
        """Get a mapping of feature groups to their availability."""
        features = {}
        for group_name, group_info in self.dependency_groups.items():
            # Check if all packages in the group are available
            available = all(
                self.is_available(pkg) for pkg in group_info['packages']
            )
            features[group_name] = available
        return features
    
    def get_missing_dependencies_summary(self) -> str:
        """Get a summary of missing optional dependencies."""
        features = self.get_available_features()
        missing = [name for name, available in features.items() if not available]
        
        if not missing:
            return "✅ All optional dependencies are available!"
        
        summary = f"📦 Optional dependencies status ({len(missing)} missing):\n\n"
        
        for group_name in missing:
            group_info = self.dependency_groups[group_name]
            summary += f"❌ {group_name}: {group_info['description']}\n"
            
            # Recommend direct package installation
            packages = group_info['packages']
            if len(packages) == 1:
                summary += f"   Install with: pip install {packages[0]}\n\n"
            else:
                summary += f"   Install with: pip install {' '.join(packages)}\n\n"
        
        summary += "\n💡 Or install everything at once: pip install langswarm[full]"
        return summary


# Global instance
optional_imports = OptionalImportManager()


def requires(*packages):
    """
    Decorator to mark functions/classes that require optional dependencies.
    
    Usage:
        @requires('openai', 'redis')
        def my_function():
            # Function that needs openai and redis
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for package in packages:
                optional_imports.require_import(package, func.__name__)
            return func(*args, **kwargs)
        
        wrapper._required_packages = packages
        return wrapper
    return decorator


def optional_import(package_name: str, feature_name: Optional[str] = None):
    """
    Helper function for optional imports in modules.
    
    Usage:
        redis = optional_import('redis', 'Redis memory backend')
        if redis:
            # Use redis
        else:
            # Fallback behavior
    """
    return optional_imports.try_import(package_name, feature_name)


def require_package(package_name: str, feature_name: Optional[str] = None):
    """
    Helper function to require a package with helpful error message.
    
    Usage:
        openai = require_package('openai', 'OpenAI provider')
    """
    return optional_imports.require_import(package_name, feature_name)
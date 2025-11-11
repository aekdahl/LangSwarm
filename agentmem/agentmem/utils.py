"""
Utility functions for AgentMem

Handles optional dependencies and provides helper functions.
"""

from typing import Any, Optional, List, Dict


class OptionalImport:
    """Handle optional dependencies gracefully"""
    
    def __init__(self):
        self._cache: Dict[str, bool] = {}
    
    def is_available(self, package_name: str) -> bool:
        """Check if a package is available for import"""
        if package_name not in self._cache:
            try:
                __import__(package_name)
                self._cache[package_name] = True
            except ImportError:
                self._cache[package_name] = False
        return self._cache[package_name]
    
    def require(self, package_name: str, feature_name: str = None) -> bool:
        """
        Check if package is available, raise helpful error if not
        
        Args:
            package_name: Python package name to check
            feature_name: Human-friendly feature name for error messages
            
        Returns:
            True if available
            
        Raises:
            ImportError: If package is not available with helpful message
        """
        if not self.is_available(package_name):
            feature = feature_name or package_name
            raise ImportError(
                f"Package '{package_name}' is required for {feature}.\n"
                f"Install it with: pip install {package_name}"
            )
        return True


# Global instance
optional_imports = OptionalImport()


def get_package_version(package_name: str) -> Optional[str]:
    """Get the version of an installed package"""
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except Exception:
        return None


def check_redis_available() -> bool:
    """Check if Redis dependencies are available"""
    return optional_imports.is_available("redis")


def check_vector_available(backend: str) -> bool:
    """Check if vector store backend dependencies are available"""
    backend_packages = {
        "chromadb": "chromadb",
        "qdrant": "qdrant_client",
        "pinecone": "pinecone",
    }
    
    if backend not in backend_packages:
        return False
    
    return optional_imports.is_available(backend_packages[backend])


def suggest_install(packages: List[str], feature: str) -> str:
    """Generate installation suggestion message"""
    if len(packages) == 1:
        return f"Install {feature} support: pip install {packages[0]}"
    else:
        packages_str = " ".join(packages)
        return f"Install {feature} support: pip install {packages_str}"




"""
Enhanced Provider Registry with Optional Dependencies

Automatically discovers and registers available providers based on installed dependencies.
Provides helpful error messages when trying to use unavailable providers.
"""

from typing import Dict, Type, List, Optional
import logging
from .interfaces import IAgentProvider, ProviderType
from langswarm.core.utils.optional_imports import optional_imports
from langswarm.core.errors import ConfigurationError, ErrorContext

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for agent providers with optional dependency support."""
    
    def __init__(self):
        self._providers: Dict[str, Type[IAgentProvider]] = {}
        self._provider_requirements: Dict[str, List[str]] = {}
        self._discover_providers()
    
    def _discover_providers(self):
        """Discover and register available providers based on installed dependencies."""
        
        # Define provider mappings with their requirements
        provider_mappings = {
            'openai': {
                'class_path': 'langswarm.core.agents.providers.openai.OpenAIProvider',
                'requirements': ['openai'],
                'description': 'OpenAI GPT models (GPT-4o, GPT-4, GPT-3.5-turbo)'
            },
            'anthropic': {
                'class_path': 'langswarm.core.agents.providers.anthropic.AnthropicProvider',
                'requirements': ['anthropic'],
                'description': 'Anthropic Claude models'
            },
            'google': {
                'class_path': 'langswarm.core.agents.providers.gemini.GeminiProvider',
                'requirements': ['google.generativeai'],
                'description': 'Google Gemini models'
            },
            'cohere': {
                'class_path': 'langswarm.core.agents.providers.cohere.CohereProvider',
                'requirements': ['cohere'],
                'description': 'Cohere language models'
            },
            'mistral': {
                'class_path': 'langswarm.core.agents.providers.mistral.MistralProvider',
                'requirements': ['mistralai'],
                'description': 'Mistral AI models'
            },
            'huggingface': {
                'class_path': 'langswarm.core.agents.providers.huggingface.HuggingFaceProvider',
                'requirements': ['transformers'],
                'description': 'Hugging Face Transformers models'
            },
            'local': {
                'class_path': 'langswarm.core.agents.providers.local.LocalProvider',
                'requirements': [],  # No external dependencies
                'description': 'Local model inference'
            }
        }
        
        # Register available providers
        for provider_name, config in provider_mappings.items():
            self._provider_requirements[provider_name] = config['requirements']
            
            # Check if all requirements are met
            requirements_met = all(
                optional_imports.is_available(req) for req in config['requirements']
            )
            
            if requirements_met:
                try:
                    # Import the provider class
                    module_path, class_name = config['class_path'].rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    provider_class = getattr(module, class_name)
                    
                    self._providers[provider_name] = provider_class
                    logger.debug(f"Registered provider: {provider_name}")
                except Exception as e:
                    logger.warning(f"Failed to register provider {provider_name}: {e}")
            else:
                missing_deps = [
                    req for req in config['requirements']
                    if not optional_imports.is_available(req)
                ]
                logger.debug(f"Provider {provider_name} not available (missing: {missing_deps})")
    
    def get_provider(self, provider_name: str) -> Type[IAgentProvider]:
        """
        Get a provider class by name.
        
        Args:
            provider_name: Name of the provider (e.g., 'openai', 'anthropic')
            
        Returns:
            Provider class
            
        Raises:
            ConfigurationError: If provider is not available
        """
        if provider_name in self._providers:
            return self._providers[provider_name]
        
        # Provider not available - give helpful error message
        if provider_name in self._provider_requirements:
            requirements = self._provider_requirements[provider_name]
            missing_deps = [
                req for req in requirements
                if not optional_imports.is_available(req)
            ]
            
            if missing_deps:
                # Find the appropriate extra for installation
                extra_suggestions = []
                for dep in missing_deps:
                    for group_name, group_info in optional_imports.dependency_groups.items():
                        if dep in group_info['packages']:
                            extra_suggestions.append(group_info['extra'])
                            break
                
                unique_extras = list(set(extra_suggestions))
                install_suggestion = f"pip install langswarm[{','.join(unique_extras)}]"
                
                raise ConfigurationError(
                    f"Provider '{provider_name}' requires missing dependencies: {missing_deps}",
                    context=ErrorContext(
                        component="ProviderRegistry",
                        operation="get_provider",
                        metadata={
                            "provider": provider_name,
                            "missing_dependencies": missing_deps
                        }
                    ),
                    suggestion=(
                        f"Install the required dependencies:\n{install_suggestion}\n\n"
                        f"Or install all providers: pip install langswarm[providers]"
                    )
                )
        
        # Unknown provider
        available_providers = list(self._providers.keys())
        raise ConfigurationError(
            f"Unknown provider: '{provider_name}'",
            context=ErrorContext(
                component="ProviderRegistry",
                operation="get_provider",
                metadata={
                    "provider": provider_name,
                    "available_providers": available_providers
                }
            ),
            suggestion=(
                f"Available providers: {', '.join(available_providers)}\n\n"
                f"For more providers, install additional dependencies:\n"
                f"pip install langswarm[providers]"
            )
        )
    
    def list_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())
    
    def list_all_providers(self) -> Dict[str, Dict]:
        """Get information about all providers (available and unavailable)."""
        result = {}
        
        for provider_name, requirements in self._provider_requirements.items():
            available = provider_name in self._providers
            missing_deps = []
            
            if not available:
                missing_deps = [
                    req for req in requirements
                    if not optional_imports.is_available(req)
                ]
            
            result[provider_name] = {
                'available': available,
                'requirements': requirements,
                'missing_dependencies': missing_deps
            }
        
        return result
    
    def get_provider_status_summary(self) -> str:
        """Get a formatted summary of provider availability."""
        all_providers = self.list_all_providers()
        available = [name for name, info in all_providers.items() if info['available']]
        unavailable = [name for name, info in all_providers.items() if not info['available']]
        
        summary = f"📊 Provider Status Summary:\n\n"
        summary += f"✅ Available ({len(available)}): {', '.join(available) if available else 'None'}\n"
        
        if unavailable:
            summary += f"❌ Unavailable ({len(unavailable)}):\n"
            for provider_name in unavailable:
                info = all_providers[provider_name]
                missing = ', '.join(info['missing_dependencies'])
                summary += f"   • {provider_name}: missing {missing}\n"
            
            summary += f"\nInstall all providers: pip install langswarm[providers]"
        
        return summary


# Global provider registry instance
provider_registry = ProviderRegistry()


def get_provider(provider_name: str) -> Type[IAgentProvider]:
    """Convenience function to get a provider."""
    return provider_registry.get_provider(provider_name)


def list_available_providers() -> List[str]:
    """Convenience function to list available providers."""
    return provider_registry.list_available_providers()


def get_provider_status() -> str:
    """Convenience function to get provider status."""
    return provider_registry.get_provider_status_summary()
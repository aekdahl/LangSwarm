"""
Base agent creation with helpful dependency errors.
"""

from typing import Optional, Dict, Any
from langswarm.core.utils.optional_imports import optional_imports, OptionalImportError


def create_agent(provider: str, model: str, **kwargs) -> Any:
    """
    Create an agent with the specified provider and model.
    
    Provides helpful error messages if the provider's package is not installed.
    """
    provider = provider.lower()
    
    # Map providers to their implementations
    provider_map = {
        'openai': ('openai', 'OpenAI GPT models'),
        'anthropic': ('anthropic', 'Anthropic Claude models'),
        'google': ('google.generativeai', 'Google Gemini models'),
        'cohere': ('cohere', 'Cohere models'),
        'mistral': ('mistralai', 'Mistral AI models'),
    }
    
    if provider not in provider_map:
        available = list(provider_map.keys())
        raise ValueError(
            f"Unknown provider: '{provider}'\n"
            f"Available providers: {', '.join(available)}"
        )
    
    package_name, feature_desc = provider_map[provider]
    
    # Try to import the provider package
    try:
        provider_module = optional_imports.require_import(package_name, feature_desc)
    except OptionalImportError as e:
        # Enhance the error message
        error_msg = str(e)
        error_msg += f"\n\n🔧 Quick fix for {provider} provider:\n"
        error_msg += f"   pip install {package_name}\n"
        error_msg += f"   export {provider.upper()}_API_KEY='your-api-key'"
        raise OptionalImportError(package_name, None, feature_desc) from None
    
    # Here we would create the actual agent
    # This is just a demo to show the error handling
    return f"Agent created with {provider} provider and {model} model"
"""
LangSwarm V2 Agent Providers

Native implementations for each LLM provider that replace the complex
AgentWrapper system with clean, provider-specific implementations.

Each provider implements the IAgentProvider interface and provides:
- Native API integration
- Provider-specific optimizations
- Streaming and function calling support
- Error handling and retry logic
- Token usage tracking
"""

# Provider implementations
try:
    from .openai import OpenAIProvider, OpenAIAgent
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .anthropic import AnthropicProvider, AnthropicAgent
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from .gemini import GeminiProvider, GeminiAgent
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from .cohere import CohereProvider, CohereAgent
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

try:
    from .mistral import MistralProvider, MistralAgent
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

try:
    from .huggingface import HuggingFaceProvider, HuggingFaceAgent
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

try:
    from .local import LocalProvider, LocalAgent
    LOCAL_AVAILABLE = True
except ImportError:
    LOCAL_AVAILABLE = False

__all__ = []

if OPENAI_AVAILABLE:
    __all__.extend(['OpenAIProvider', 'OpenAIAgent'])

if ANTHROPIC_AVAILABLE:
    __all__.extend(['AnthropicProvider', 'AnthropicAgent'])

if GEMINI_AVAILABLE:
    __all__.extend(['GeminiProvider', 'GeminiAgent'])

if COHERE_AVAILABLE:
    __all__.extend(['CohereProvider', 'CohereAgent'])

if MISTRAL_AVAILABLE:
    __all__.extend(['MistralProvider', 'MistralAgent'])

if HUGGINGFACE_AVAILABLE:
    __all__.extend(['HuggingFaceProvider', 'HuggingFaceAgent'])

if LOCAL_AVAILABLE:
    __all__.extend(['LocalProvider', 'LocalAgent'])

"""
Centralized Provider Configuration (DEPRECATED)

This file is deprecated and will be removed in a future version.
Cost tracking and model support are now handled dynamically by LiteLLM.

Pricing is per 1M tokens (divide by 1000 to get per 1K tokens).

Last updated: November 2024
Source: https://openai.com/api/pricing/
"""
import warnings
warnings.warn(
    "The 'langswarm.core.agents.providers.config' module is deprecated. "
    "Model costs and validation are now handled by LiteLLM.",
    DeprecationWarning,
    stacklevel=2
)

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    input_price: float  # Price per 1M tokens
    output_price: float  # Price per 1M tokens
    cached_input_price: float = 0.0  # Price per 1M cached input tokens
    context_window: int = 128000  # Default context window
    supports_vision: bool = False
    supports_tools: bool = True
    supports_streaming: bool = True
    deprecated: bool = False
    notes: str = ""


# =============================================================================
# OPENAI MODELS
# =============================================================================
# Pricing from: https://openai.com/api/pricing/

OPENAI_MODELS: Dict[str, ModelInfo] = {
    # ==========================================================================
    # GPT-5 Series (Flagship - Latest)
    # ==========================================================================
    "gpt-5.1": ModelInfo(
        name="gpt-5.1",
        input_price=1.25,
        output_price=10.0,
        cached_input_price=0.125,
        context_window=256000,
        supports_vision=True,
        notes="Flagship model for coding and agentic tasks"
    ),
    "gpt-5-mini": ModelInfo(
        name="gpt-5-mini",
        input_price=0.25,
        output_price=2.0,
        cached_input_price=0.025,
        context_window=128000,
        supports_vision=True,
        notes="Faster, cost-effective GPT-5 for well-defined tasks"
    ),
    "gpt-5-nano": ModelInfo(
        name="gpt-5-nano",
        input_price=0.05,
        output_price=0.4,
        cached_input_price=0.005,
        context_window=128000,
        supports_vision=True,
        notes="Fastest/cheapest GPT-5, ideal for summarization/classification"
    ),
    "gpt-5-pro": ModelInfo(
        name="gpt-5-pro",
        input_price=15.0,
        output_price=120.0,
        context_window=256000,
        supports_vision=True,
        notes="Most intelligent and precise model"
    ),
    
    # ==========================================================================
    # GPT-4.1 Series (Fine-tuning optimized)
    # ==========================================================================
    "gpt-4.1": ModelInfo(
        name="gpt-4.1",
        input_price=3.0,
        output_price=12.0,
        cached_input_price=0.75,
        context_window=128000,
        supports_vision=True,
        notes="Fine-tuning optimized"
    ),
    "gpt-4.1-mini": ModelInfo(
        name="gpt-4.1-mini",
        input_price=0.8,
        output_price=3.2,
        cached_input_price=0.2,
        context_window=128000,
        supports_vision=True,
        notes="Fine-tuning optimized mini"
    ),
    "gpt-4.1-nano": ModelInfo(
        name="gpt-4.1-nano",
        input_price=0.2,
        output_price=0.8,
        cached_input_price=0.05,
        context_window=128000,
        supports_vision=True,
        notes="Fine-tuning optimized nano"
    ),
    
    # ==========================================================================
    # O4 Reasoning Models
    # ==========================================================================
    "o4-mini": ModelInfo(
        name="o4-mini",
        input_price=4.0,
        output_price=16.0,
        cached_input_price=1.0,
        context_window=200000,
        supports_vision=False,
        supports_tools=True,
        notes="Fine-tunable reasoning model"
    ),
    
    # ==========================================================================
    # GPT-4o family (previous flagship)
    # ==========================================================================
    "gpt-4o": ModelInfo(
        name="gpt-4o",
        input_price=2.5,
        output_price=10.0,
        cached_input_price=1.25,
        context_window=128000,
        supports_vision=True,
        notes="Previous flagship multimodal model"
    ),
    "gpt-4o-2024-11-20": ModelInfo(
        name="gpt-4o-2024-11-20",
        input_price=2.5,
        output_price=10.0,
        cached_input_price=1.25,
        context_window=128000,
        supports_vision=True,
    ),
    "gpt-4o-2024-08-06": ModelInfo(
        name="gpt-4o-2024-08-06",
        input_price=2.5,
        output_price=10.0,
        cached_input_price=1.25,
        context_window=128000,
        supports_vision=True,
    ),
    "gpt-4o-2024-05-13": ModelInfo(
        name="gpt-4o-2024-05-13",
        input_price=5.0,
        output_price=15.0,
        context_window=128000,
        supports_vision=True,
    ),
    "chatgpt-4o-latest": ModelInfo(
        name="chatgpt-4o-latest",
        input_price=5.0,
        output_price=15.0,
        context_window=128000,
        supports_vision=True,
    ),
    
    # GPT-4o mini (cost-effective)
    "gpt-4o-mini": ModelInfo(
        name="gpt-4o-mini",
        input_price=0.15,
        output_price=0.6,
        cached_input_price=0.075,
        context_window=128000,
        supports_vision=True,
        notes="Cost-effective for most tasks"
    ),
    "gpt-4o-mini-2024-07-18": ModelInfo(
        name="gpt-4o-mini-2024-07-18",
        input_price=0.15,
        output_price=0.6,
        cached_input_price=0.075,
        context_window=128000,
        supports_vision=True,
    ),
    
    # ==========================================================================
    # O1 reasoning models
    # ==========================================================================
    "o1": ModelInfo(
        name="o1",
        input_price=15.0,
        output_price=60.0,
        cached_input_price=7.5,
        context_window=200000,
        supports_vision=False,
        supports_tools=False,
        notes="Advanced reasoning model"
    ),
    "o1-2024-12-17": ModelInfo(
        name="o1-2024-12-17",
        input_price=15.0,
        output_price=60.0,
        cached_input_price=7.5,
        context_window=200000,
        supports_vision=False,
        supports_tools=False,
    ),
    "o1-preview": ModelInfo(
        name="o1-preview",
        input_price=15.0,
        output_price=60.0,
        context_window=128000,
        supports_vision=False,
        supports_tools=False,
    ),
    "o1-preview-2024-09-12": ModelInfo(
        name="o1-preview-2024-09-12",
        input_price=15.0,
        output_price=60.0,
        context_window=128000,
        supports_vision=False,
        supports_tools=False,
    ),
    "o1-mini": ModelInfo(
        name="o1-mini",
        input_price=3.0,
        output_price=12.0,
        cached_input_price=1.5,
        context_window=128000,
        supports_vision=False,
        supports_tools=False,
        notes="Fast reasoning model"
    ),
    "o1-mini-2024-09-12": ModelInfo(
        name="o1-mini-2024-09-12",
        input_price=3.0,
        output_price=12.0,
        cached_input_price=1.5,
        context_window=128000,
        supports_vision=False,
        supports_tools=False,
    ),
    
    # ==========================================================================
    # Realtime API Models
    # ==========================================================================
    "gpt-realtime": ModelInfo(
        name="gpt-realtime",
        input_price=4.0,
        output_price=16.0,
        cached_input_price=0.4,
        context_window=128000,
        supports_vision=False,
        notes="Low-latency multimodal (text)"
    ),
    "gpt-realtime-mini": ModelInfo(
        name="gpt-realtime-mini",
        input_price=0.6,
        output_price=2.4,
        cached_input_price=0.06,
        context_window=128000,
        supports_vision=False,
        notes="Low-latency multimodal mini (text)"
    ),
    
    # ==========================================================================
    # GPT-4 Turbo (legacy)
    # ==========================================================================
    "gpt-4-turbo": ModelInfo(
        name="gpt-4-turbo",
        input_price=10.0,
        output_price=30.0,
        context_window=128000,
        supports_vision=True,
        deprecated=True,
    ),
    "gpt-4-turbo-2024-04-09": ModelInfo(
        name="gpt-4-turbo-2024-04-09",
        input_price=10.0,
        output_price=30.0,
        context_window=128000,
        supports_vision=True,
        deprecated=True,
    ),
    "gpt-4-turbo-preview": ModelInfo(
        name="gpt-4-turbo-preview",
        input_price=10.0,
        output_price=30.0,
        context_window=128000,
        supports_vision=True,
        deprecated=True,
    ),
    
    # GPT-4 base (legacy)
    "gpt-4": ModelInfo(
        name="gpt-4",
        input_price=30.0,
        output_price=60.0,
        context_window=8192,
        supports_vision=False,
        deprecated=True,
    ),
    "gpt-4-0613": ModelInfo(
        name="gpt-4-0613",
        input_price=30.0,
        output_price=60.0,
        context_window=8192,
        supports_vision=False,
        deprecated=True,
    ),
    
    # GPT-3.5 Turbo (legacy)
    "gpt-3.5-turbo": ModelInfo(
        name="gpt-3.5-turbo",
        input_price=0.5,
        output_price=1.5,
        context_window=16385,
        supports_vision=False,
        deprecated=True,
    ),
    "gpt-3.5-turbo-0125": ModelInfo(
        name="gpt-3.5-turbo-0125",
        input_price=0.5,
        output_price=1.5,
        context_window=16385,
        supports_vision=False,
        deprecated=True,
    ),
    "gpt-3.5-turbo-1106": ModelInfo(
        name="gpt-3.5-turbo-1106",
        input_price=1.0,
        output_price=2.0,
        context_window=16385,
        supports_vision=False,
        deprecated=True,
    ),
}


# =============================================================================
# ANTHROPIC MODELS
# =============================================================================
# Pricing from: https://www.anthropic.com/pricing
# Prices per 1M tokens

ANTHROPIC_MODELS: Dict[str, ModelInfo] = {
    # ==========================================================================
    # Claude 4.5 Series (Latest - Most Advanced)
    # ==========================================================================
    "claude-opus-4-5-20250514": ModelInfo(
        name="claude-opus-4-5-20250514",
        input_price=5.0,
        output_price=25.0,
        cached_input_price=0.50,
        context_window=200000,
        supports_vision=True,
        notes="Claude Opus 4.5 - most intelligent model"
    ),
    "claude-opus-4.5": ModelInfo(
        name="claude-opus-4.5",
        input_price=5.0,
        output_price=25.0,
        cached_input_price=0.50,
        context_window=200000,
        supports_vision=True,
        notes="Claude Opus 4.5 alias"
    ),
    
    # ==========================================================================
    # Claude 4 Series
    # ==========================================================================
    "claude-sonnet-4-20250514": ModelInfo(
        name="claude-sonnet-4-20250514",
        input_price=3.0,
        output_price=15.0,
        cached_input_price=0.30,
        context_window=200000,
        supports_vision=True,
        notes="Claude Sonnet 4 - balanced performance"
    ),
    "claude-sonnet-4": ModelInfo(
        name="claude-sonnet-4",
        input_price=3.0,
        output_price=15.0,
        cached_input_price=0.30,
        context_window=200000,
        supports_vision=True,
        notes="Claude Sonnet 4 alias"
    ),
    "claude-opus-4-20250514": ModelInfo(
        name="claude-opus-4-20250514",
        input_price=15.0,
        output_price=75.0,
        cached_input_price=1.50,
        context_window=200000,
        supports_vision=True,
        notes="Claude Opus 4 - extended thinking"
    ),
    "claude-opus-4": ModelInfo(
        name="claude-opus-4",
        input_price=15.0,
        output_price=75.0,
        cached_input_price=1.50,
        context_window=200000,
        supports_vision=True,
        notes="Claude Opus 4 alias"
    ),
    
    # ==========================================================================
    # Claude 3.7 Series
    # ==========================================================================
    "claude-3-7-sonnet-20250219": ModelInfo(
        name="claude-3-7-sonnet-20250219",
        input_price=3.0,
        output_price=15.0,
        cached_input_price=0.30,
        context_window=200000,
        supports_vision=True,
        notes="Claude 3.7 Sonnet"
    ),
    
    # ==========================================================================
    # Claude 3.5 Series
    # ==========================================================================
    "claude-3-5-sonnet-20241022": ModelInfo(
        name="claude-3-5-sonnet-20241022",
        input_price=3.0,
        output_price=15.0,
        cached_input_price=0.30,
        context_window=200000,
        supports_vision=True,
        notes="Claude 3.5 Sonnet v2"
    ),
    "claude-3-5-sonnet-20240620": ModelInfo(
        name="claude-3-5-sonnet-20240620",
        input_price=3.0,
        output_price=15.0,
        context_window=200000,
        supports_vision=True,
    ),
    "claude-3-5-sonnet-latest": ModelInfo(
        name="claude-3-5-sonnet-latest",
        input_price=3.0,
        output_price=15.0,
        cached_input_price=0.30,
        context_window=200000,
        supports_vision=True,
    ),
    "claude-3-5-haiku-20241022": ModelInfo(
        name="claude-3-5-haiku-20241022",
        input_price=0.80,
        output_price=4.0,
        cached_input_price=0.08,
        context_window=200000,
        supports_vision=True,
        notes="Fast & affordable"
    ),
    "claude-3-5-haiku-latest": ModelInfo(
        name="claude-3-5-haiku-latest",
        input_price=0.80,
        output_price=4.0,
        cached_input_price=0.08,
        context_window=200000,
        supports_vision=True,
    ),
    
    # ==========================================================================
    # Claude 3 Series
    # ==========================================================================
    "claude-3-opus-20240229": ModelInfo(
        name="claude-3-opus-20240229",
        input_price=15.0,
        output_price=75.0,
        cached_input_price=1.50,
        context_window=200000,
        supports_vision=True,
        notes="Most capable Claude 3"
    ),
    "claude-3-opus-latest": ModelInfo(
        name="claude-3-opus-latest",
        input_price=15.0,
        output_price=75.0,
        cached_input_price=1.50,
        context_window=200000,
        supports_vision=True,
    ),
    "claude-3-sonnet-20240229": ModelInfo(
        name="claude-3-sonnet-20240229",
        input_price=3.0,
        output_price=15.0,
        context_window=200000,
        supports_vision=True,
    ),
    "claude-3-haiku-20240307": ModelInfo(
        name="claude-3-haiku-20240307",
        input_price=0.25,
        output_price=1.25,
        cached_input_price=0.03,
        context_window=200000,
        supports_vision=True,
    ),
    
    # ==========================================================================
    # Legacy models (deprecated)
    # ==========================================================================
    "claude-2.1": ModelInfo(
        name="claude-2.1",
        input_price=8.0,
        output_price=24.0,
        context_window=200000,
        supports_vision=False,
        deprecated=True,
    ),
    "claude-2.0": ModelInfo(
        name="claude-2.0",
        input_price=8.0,
        output_price=24.0,
        context_window=100000,
        supports_vision=False,
        deprecated=True,
    ),
    "claude-instant-1.2": ModelInfo(
        name="claude-instant-1.2",
        input_price=0.80,
        output_price=2.40,
        context_window=100000,
        supports_vision=False,
        deprecated=True,
    ),
}


# =============================================================================
# GOOGLE GEMINI MODELS
# =============================================================================
# Pricing from: https://ai.google.dev/gemini-api/docs/pricing
# Prices per 1M tokens

GEMINI_MODELS: Dict[str, ModelInfo] = {
    # ==========================================================================
    # Gemini 3 Series (Latest - Most Advanced)
    # ==========================================================================
    "gemini-3-pro-preview": ModelInfo(
        name="gemini-3-pro-preview",
        input_price=2.0,  # $4.0 for prompts > 200k tokens
        output_price=12.0,  # $18.0 for prompts > 200k tokens (includes thinking)
        cached_input_price=0.20,
        context_window=1000000,
        supports_vision=True,
        notes="Best model for multimodal understanding, agentic and vibe-coding"
    ),
    "gemini-3-pro-image-preview": ModelInfo(
        name="gemini-3-pro-image-preview",
        input_price=2.0,
        output_price=12.0,  # Text output; image output is $120/1M tokens
        cached_input_price=0.20,
        context_window=1000000,
        supports_vision=True,
        notes="Native image generation model"
    ),
    
    # ==========================================================================
    # Gemini 2.5 Series
    # ==========================================================================
    "gemini-2.5-pro": ModelInfo(
        name="gemini-2.5-pro",
        input_price=1.25,  # $2.50 for prompts > 200k tokens
        output_price=10.0,  # $15.0 for prompts > 200k tokens
        cached_input_price=0.3125,
        context_window=1000000,
        supports_vision=True,
        notes="State-of-the-art multipurpose, excels at coding and reasoning"
    ),
    "gemini-2.5-pro-preview-05-06": ModelInfo(
        name="gemini-2.5-pro-preview-05-06",
        input_price=1.25,
        output_price=10.0,
        cached_input_price=0.3125,
        context_window=1000000,
        supports_vision=True,
    ),
    "gemini-2.5-flash": ModelInfo(
        name="gemini-2.5-flash",
        input_price=0.15,  # $0.30 for prompts > 200k tokens
        output_price=0.60,  # $1.50 for prompts > 200k tokens (thinking: $3.50)
        cached_input_price=0.0375,
        context_window=1000000,
        supports_vision=True,
        notes="Best price-performance, adaptive thinking"
    ),
    "gemini-2.5-flash-preview-05-20": ModelInfo(
        name="gemini-2.5-flash-preview-05-20",
        input_price=0.15,
        output_price=0.60,
        cached_input_price=0.0375,
        context_window=1000000,
        supports_vision=True,
    ),
    "gemini-2.5-flash-lite-preview-06-17": ModelInfo(
        name="gemini-2.5-flash-lite-preview-06-17",
        input_price=0.075,
        output_price=0.30,
        cached_input_price=0.01875,
        context_window=1000000,
        supports_vision=True,
        notes="Cost-effective, high-volume tasks"
    ),
    "gemini-2.5-computer-use-preview-10-2025": ModelInfo(
        name="gemini-2.5-computer-use-preview-10-2025",
        input_price=1.25,
        output_price=10.0,
        context_window=1000000,
        supports_vision=True,
        notes="Browser control agents, task automation"
    ),
    
    # ==========================================================================
    # Gemini 2.0 Series
    # ==========================================================================
    "gemini-2.0-flash": ModelInfo(
        name="gemini-2.0-flash",
        input_price=0.10,
        output_price=0.40,
        cached_input_price=0.025,
        context_window=1000000,
        supports_vision=True,
        notes="Workhorse model, multimodal Live API"
    ),
    "gemini-2.0-flash-exp": ModelInfo(
        name="gemini-2.0-flash-exp",
        input_price=0.10,
        output_price=0.40,
        context_window=1000000,
        supports_vision=True,
        notes="Experimental Gemini 2.0"
    ),
    "gemini-2.0-flash-lite": ModelInfo(
        name="gemini-2.0-flash-lite",
        input_price=0.075,
        output_price=0.30,
        cached_input_price=0.01875,
        context_window=1000000,
        supports_vision=True,
        notes="Cost efficiency, high frequency tasks"
    ),
    "gemini-2.0-flash-thinking-exp-1219": ModelInfo(
        name="gemini-2.0-flash-thinking-exp-1219",
        input_price=0.10,
        output_price=0.40,
        context_window=1000000,
        supports_vision=True,
        notes="Experimental reasoning model"
    ),
    
    # ==========================================================================
    # Gemini 1.5 Series
    # ==========================================================================
    "gemini-1.5-pro": ModelInfo(
        name="gemini-1.5-pro",
        input_price=1.25,
        output_price=5.0,
        cached_input_price=0.3125,
        context_window=2000000,
        supports_vision=True,
        notes="Gemini 1.5 Pro"
    ),
    "gemini-1.5-pro-latest": ModelInfo(
        name="gemini-1.5-pro-latest",
        input_price=1.25,
        output_price=5.0,
        cached_input_price=0.3125,
        context_window=2000000,
        supports_vision=True,
    ),
    "gemini-1.5-pro-002": ModelInfo(
        name="gemini-1.5-pro-002",
        input_price=1.25,
        output_price=5.0,
        cached_input_price=0.3125,
        context_window=2000000,
        supports_vision=True,
    ),
    "gemini-1.5-flash": ModelInfo(
        name="gemini-1.5-flash",
        input_price=0.075,
        output_price=0.30,
        cached_input_price=0.01875,
        context_window=1000000,
        supports_vision=True,
        notes="Fast and efficient"
    ),
    "gemini-1.5-flash-latest": ModelInfo(
        name="gemini-1.5-flash-latest",
        input_price=0.075,
        output_price=0.30,
        cached_input_price=0.01875,
        context_window=1000000,
        supports_vision=True,
    ),
    "gemini-1.5-flash-002": ModelInfo(
        name="gemini-1.5-flash-002",
        input_price=0.075,
        output_price=0.30,
        cached_input_price=0.01875,
        context_window=1000000,
        supports_vision=True,
    ),
    "gemini-1.5-flash-8b": ModelInfo(
        name="gemini-1.5-flash-8b",
        input_price=0.0375,
        output_price=0.15,
        cached_input_price=0.01,
        context_window=1000000,
        supports_vision=True,
        notes="Smallest/fastest Flash"
    ),
    
    # ==========================================================================
    # Gemini 1.0 (legacy)
    # ==========================================================================
    "gemini-pro": ModelInfo(
        name="gemini-pro",
        input_price=0.50,
        output_price=1.50,
        context_window=32000,
        supports_vision=False,
        deprecated=True,
    ),
    "gemini-pro-vision": ModelInfo(
        name="gemini-pro-vision",
        input_price=0.50,
        output_price=1.50,
        context_window=32000,
        supports_vision=True,
        deprecated=True,
    ),
    
    # ==========================================================================
    # Experimental
    # ==========================================================================
    "gemini-exp-1206": ModelInfo(
        name="gemini-exp-1206",
        input_price=1.25,
        output_price=5.0,
        context_window=2000000,
        supports_vision=True,
        notes="Experimental"
    ),
    "learnlm-1.5-pro-experimental": ModelInfo(
        name="learnlm-1.5-pro-experimental",
        input_price=1.25,
        output_price=5.0,
        context_window=2000000,
        supports_vision=True,
        notes="Learning-focused experimental"
    ),
}


# =============================================================================
# MISTRAL MODELS
# =============================================================================
# Pricing from: https://mistral.ai/technology/#pricing
# Prices per 1M tokens

MISTRAL_MODELS: Dict[str, ModelInfo] = {
    # Premier models
    "mistral-large-latest": ModelInfo(
        name="mistral-large-latest",
        input_price=2.0,
        output_price=6.0,
        context_window=128000,
        supports_vision=False,
        notes="Most capable Mistral"
    ),
    "mistral-large-2411": ModelInfo(
        name="mistral-large-2411",
        input_price=2.0,
        output_price=6.0,
        context_window=128000,
        supports_vision=False,
    ),
    "mistral-large-2407": ModelInfo(
        name="mistral-large-2407",
        input_price=2.0,
        output_price=6.0,
        context_window=128000,
        supports_vision=False,
    ),
    
    # Efficient models
    "mistral-small-latest": ModelInfo(
        name="mistral-small-latest",
        input_price=0.2,
        output_price=0.6,
        context_window=128000,
        supports_vision=False,
        notes="Cost-effective"
    ),
    "mistral-small-2409": ModelInfo(
        name="mistral-small-2409",
        input_price=0.2,
        output_price=0.6,
        context_window=128000,
        supports_vision=False,
    ),
    
    # Coding specialist
    "codestral-latest": ModelInfo(
        name="codestral-latest",
        input_price=0.2,
        output_price=0.6,
        context_window=32000,
        supports_vision=False,
        notes="Optimized for code"
    ),
    "codestral-2405": ModelInfo(
        name="codestral-2405",
        input_price=0.2,
        output_price=0.6,
        context_window=32000,
        supports_vision=False,
    ),
    
    # Free/Open models
    "open-mistral-nemo": ModelInfo(
        name="open-mistral-nemo",
        input_price=0.15,
        output_price=0.15,
        context_window=128000,
        supports_vision=False,
        notes="Open-weight model"
    ),
    "open-mistral-nemo-2407": ModelInfo(
        name="open-mistral-nemo-2407",
        input_price=0.15,
        output_price=0.15,
        context_window=128000,
        supports_vision=False,
    ),
    "mistral-nemo-latest": ModelInfo(
        name="mistral-nemo-latest",
        input_price=0.15,
        output_price=0.15,
        context_window=128000,
        supports_vision=False,
    ),
    
    # Multimodal
    "pixtral-large-latest": ModelInfo(
        name="pixtral-large-latest",
        input_price=2.0,
        output_price=6.0,
        context_window=128000,
        supports_vision=True,
        notes="Vision-capable"
    ),
    "pixtral-12b-2409": ModelInfo(
        name="pixtral-12b-2409",
        input_price=0.15,
        output_price=0.15,
        context_window=128000,
        supports_vision=True,
    ),
    
    # Legacy
    "open-mistral-7b": ModelInfo(
        name="open-mistral-7b",
        input_price=0.25,
        output_price=0.25,
        context_window=32000,
        supports_vision=False,
        deprecated=True,
    ),
    "open-mixtral-8x7b": ModelInfo(
        name="open-mixtral-8x7b",
        input_price=0.7,
        output_price=0.7,
        context_window=32000,
        supports_vision=False,
        deprecated=True,
    ),
    "open-mixtral-8x22b": ModelInfo(
        name="open-mixtral-8x22b",
        input_price=2.0,
        output_price=6.0,
        context_window=64000,
        supports_vision=False,
    ),
}


# =============================================================================
# COHERE MODELS
# =============================================================================
# Pricing from: https://cohere.com/pricing
# Prices per 1M tokens

COHERE_MODELS: Dict[str, ModelInfo] = {
    # Command R+ (most capable)
    "command-r-plus": ModelInfo(
        name="command-r-plus",
        input_price=2.5,
        output_price=10.0,
        context_window=128000,
        supports_vision=False,
        notes="Most capable Cohere model"
    ),
    "command-r-plus-08-2024": ModelInfo(
        name="command-r-plus-08-2024",
        input_price=2.5,
        output_price=10.0,
        context_window=128000,
        supports_vision=False,
    ),
    
    # Command R (balanced)
    "command-r": ModelInfo(
        name="command-r",
        input_price=0.15,
        output_price=0.6,
        context_window=128000,
        supports_vision=False,
        notes="Best value for RAG"
    ),
    "command-r-08-2024": ModelInfo(
        name="command-r-08-2024",
        input_price=0.15,
        output_price=0.6,
        context_window=128000,
        supports_vision=False,
    ),
    
    # Legacy Command
    "command": ModelInfo(
        name="command",
        input_price=1.0,
        output_price=2.0,
        context_window=4096,
        supports_vision=False,
        deprecated=True,
    ),
    "command-nightly": ModelInfo(
        name="command-nightly",
        input_price=1.0,
        output_price=2.0,
        context_window=4096,
        supports_vision=False,
        deprecated=True,
    ),
    "command-light": ModelInfo(
        name="command-light",
        input_price=0.3,
        output_price=0.6,
        context_window=4096,
        supports_vision=False,
        deprecated=True,
    ),
    "command-light-nightly": ModelInfo(
        name="command-light-nightly",
        input_price=0.3,
        output_price=0.6,
        context_window=4096,
        supports_vision=False,
        deprecated=True,
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_model_info(provider: str, model: str) -> ModelInfo:
    """Get model info for a specific provider and model"""
    provider_models = {
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "gemini": GEMINI_MODELS,
        "google": GEMINI_MODELS,
        "mistral": MISTRAL_MODELS,
        "cohere": COHERE_MODELS,
    }
    
    models = provider_models.get(provider.lower(), {})
    return models.get(model)


def get_supported_models(provider: str) -> List[str]:
    """Get list of supported models for a provider"""
    provider_models = {
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "gemini": GEMINI_MODELS,
        "google": GEMINI_MODELS,
        "mistral": MISTRAL_MODELS,
        "cohere": COHERE_MODELS,
    }
    
    models = provider_models.get(provider.lower(), {})
    return [m for m, info in models.items() if not info.deprecated]


def estimate_cost(
    provider: str, 
    model: str, 
    input_tokens: int, 
    output_tokens: int,
    cached_input_tokens: int = 0
) -> float:
    """
    Estimate cost for API usage.
    
    Prices are per 1M tokens, so we divide token counts by 1,000,000.
    """
    info = get_model_info(provider, model)
    if not info:
        return 0.0
    
    # Calculate costs (prices are per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * info.input_price
    output_cost = (output_tokens / 1_000_000) * info.output_price
    cached_cost = (cached_input_tokens / 1_000_000) * info.cached_input_price
    
    return input_cost + output_cost + cached_cost


def get_all_models() -> Dict[str, Dict[str, ModelInfo]]:
    """Get all models organized by provider"""
    return {
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "gemini": GEMINI_MODELS,
        "mistral": MISTRAL_MODELS,
        "cohere": COHERE_MODELS,
    }


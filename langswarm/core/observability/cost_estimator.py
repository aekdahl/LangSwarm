"""
Centralized Cost Estimator for LangSwarm Models
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelPricing:
    input_cost_per_1k: float
    output_cost_per_1k: float

class CostEstimator:
    """
    Estimates costs for various LLM providers based on token usage.
    Pricing data is centralized here to allow for easy updates.
    """
    
    # Pricing rates (USD per 1K tokens)
    # OpenAi pricing updated Nov 2024
    _RATES: Dict[str, ModelPricing] = {
        # --- OpenAI ---
        # GPT-4o
        "gpt-4o": ModelPricing(0.0025, 0.01),
        "gpt-4o-2024-05-13": ModelPricing(0.005, 0.015),
        "gpt-4o-2024-08-06": ModelPricing(0.0025, 0.01),
        "chatgpt-4o-latest": ModelPricing(0.005, 0.015),
        
        # GPT-4o Mini
        "gpt-4o-mini": ModelPricing(0.00015, 0.0006),
        "gpt-4o-mini-2024-07-18": ModelPricing(0.00015, 0.0006),
        
        # O1 (Reasoning)
        "o1": ModelPricing(0.015, 0.06),
        "o1-preview": ModelPricing(0.015, 0.06),
        "o1-mini": ModelPricing(0.003, 0.012),
        
        # GPT-4 Turbo
        "gpt-4-turbo": ModelPricing(0.01, 0.03),
        "gpt-4-turbo-preview": ModelPricing(0.01, 0.03),
        
        # GPT-3.5
        "gpt-3.5-turbo": ModelPricing(0.0005, 0.0015),
        "gpt-3.5-turbo-0125": ModelPricing(0.0005, 0.0015),
        
        # --- Anthropic ---
        "claude-3-5-sonnet-20240620": ModelPricing(0.003, 0.015),
        "claude-3-opus-20240229": ModelPricing(0.015, 0.075),
        "claude-3-sonnet-20240229": ModelPricing(0.003, 0.015),
        "claude-3-haiku-20240307": ModelPricing(0.00025, 0.00125),
    }

    @classmethod
    def estimate_cost(
        cls, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """
        Calculate estimated cost in USD.
        
        Args:
            model: Model identifier (e.g., 'gpt-4o')
            input_tokens: Number of prompt/input tokens
            output_tokens: Number of completion/output tokens
            
        Returns:
            Estimated cost in USD (float)
        """
        if not model:
            return 0.0
            
        rate = cls._RATES.get(model)
        
        # Fallback for versioned models (e.g., gpt-4-0613 -> gpt-4)
        if not rate:
            # Try finding base model name
            for key in cls._RATES:
                if model.startswith(key):
                    rate = cls._RATES[key]
                    break
        
        if not rate:
            return 0.0
            
        input_cost = (input_tokens / 1000.0) * rate.input_cost_per_1k
        output_cost = (output_tokens / 1000.0) * rate.output_cost_per_1k
        
        return input_cost + output_cost

    @classmethod
    def get_pricing(cls, model: str) -> Optional[ModelPricing]:
        """Get pricing details for a model"""
        return cls._RATES.get(model)

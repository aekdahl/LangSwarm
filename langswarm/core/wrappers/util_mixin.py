import re
import json
from ..utils.utilities import Utils

class UtilMixin:
    def __init__(self):
        self.utils = Utils()
        
    @property
    def MODEL_REGISTRY(self):
        return {
            "gpt-4o": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-2024-08-06": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "chatgpt-4o-latest": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-mini": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-mini-2024-07-18": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "o1": {"limit": 200000, "ppm": 0, "ppm_out": 0},
            "o1-2024-12-17": {"limit": 200000, "ppm": 0, "ppm_out": 0},
            "o1-mini": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "o1-mini-2024-09-12": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "o1-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "o1-preview-2024-09-12": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-realtime-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-realtime-preview-2024-12-17": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-mini-realtime-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-mini-realtime-preview-2024-12-17": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-audio-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4o-audio-preview-2024-12-17": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4-turbo": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4-turbo-2024-04-09": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4-turbo-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4-0125-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4-1106-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "gpt-4": {"limit": 8192, "ppm": 0, "ppm_out": 0},
            "gpt-4-0613": {"limit": 8192, "ppm": 0, "ppm_out": 0},
            "gpt-4-0314": {"limit": 8192, "ppm": 0, "ppm_out": 0},
            "gpt-3.5-turbo-0125": {"limit": 16385, "ppm": 0, "ppm_out": 0},
            "gpt-3.5-turbo": {"limit": 16385, "ppm": 0, "ppm_out": 0},
            "gpt-3.5-turbo-1106": {"limit": 16385, "ppm": 0, "ppm_out": 0},
            "gpt-3.5-turbo-instruct": {"limit": 16385, "ppm": 0, "ppm_out": 0},
            "babbage-002": {"limit": 16384, "ppm": 0, "ppm_out": 0},
            "davinci-002": {"limit": 16384, "ppm": 0, "ppm_out": 0},
            "claude-3-5-sonnet-20241022": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "claude-3-5-sonnet-latest": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "claude-3-5-sonnet-v2@20241022": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "claude-3-5-haiku-20241022": {"limit": 200000, "ppm": 0.8, "ppm_out": 0},
            "claude-3-5-haiku-latest": {"limit": 200000, "ppm": 0.8, "ppm_out": 0},
            "anthropic.claude-3-5-haiku-20241022-v1:0": {"limit": 200000, "ppm": 0.8, "ppm_out": 0},
            "claude-3-5-haiku@20241022": {"limit": 200000, "ppm": 0.8, "ppm_out": 0},
            "claude-3-opus-20240229": {"limit": 200000, "ppm": 15, "ppm_out": 0},
            "claude-3-opus-latest": {"limit": 200000, "ppm": 15, "ppm_out": 0},
            "anthropic.claude-3-opus-20240229-v1:0": {"limit": 200000, "ppm": 15, "ppm_out": 0},
            "claude-3-opus@20240229": {"limit": 200000, "ppm": 15, "ppm_out": 0},
            "claude-3-sonnet-20240229": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "anthropic.claude-3-sonnet-20240229-v1:0": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "claude-3-sonnet@20240229": {"limit": 200000, "ppm": 3, "ppm_out": 0},
            "claude-3-haiku-20240307": {"limit": 200000, "ppm": 0.25, "ppm_out": 0},
            "anthropic.claude-3-haiku-20240307-v1:0": {"limit": 200000, "ppm": 0.25, "ppm_out": 0},
            "claude-3-haiku@20240307": {"limit": 200000, "ppm": 0.25, "ppm_out": 0},
            "gemini-1.5-flash": {"limit": 1000000, "ppm": 0.15, "ppm_out": 0},
            "gemini-1.5-flash-8b": {"limit": 1000000, "ppm": 0.075, "ppm_out": 0},
            "gemini-1.5-pro": {"limit": 2000000, "ppm": 2.5, "ppm_out": 0},
            "gemini-1.0-pro": {"limit": 120000, "ppm": 0.5, "ppm_out": 0},
            "mistral-large-latest": {"limit": 128000, "ppm": 2, "ppm_out": 0},
            "pixtral-large-latest": {"limit": 128000, "ppm": 2, "ppm_out": 0},
            "mistral-small-latest": {"limit": 32000, "ppm": 0.2, "ppm_out": 0},
            "codestral-latest": {"limit": 32000, "ppm": 0.3, "ppm_out": 0},
            "ministral-8b-latest": {"limit": 128000, "ppm": 0.1, "ppm_out": 0},
            "ministral-3b-latest": {"limit": 128000, "ppm": 0.04, "ppm_out": 0},
            "command-r": {"limit": 128000, "ppm": 0.15, "ppm_out": 0},
            "command-r-08-2024": {"limit": 128000, "ppm": 0.15, "ppm_out": 0},
            "command-r-03-2024": {"limit": 128000, "ppm": 0.15, "ppm_out": 0},
            "command-r7b": {"limit": 128000, "ppm": 0.0375, "ppm_out": 0},
            "command-r7b-12-2024": {"limit": 128000, "ppm": 0.0375, "ppm_out": 0},
            "command-r-plus": {"limit": 128000, "ppm": 2.5, "ppm_out": 0},
            "command-r-plus-08-2024": {"limit": 128000, "ppm": 2.5, "ppm_out": 0},
            "command-r-plus-04-2024": {"limit": 128000, "ppm": 2.5, "ppm_out": 0},
            "llama-3.3": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "llama-3.2": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "llama-3.1": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "llama-3": {"limit": 8000, "ppm": 0, "ppm_out": 0},
            "llama-2": {"limit": 4000, "ppm": 0, "ppm_out": 0},
            "Llama": {"limit": 128000, "ppm": 0, "ppm_out": 0},
            "biogpt": {"limit": 200000, "ppm": 0, "ppm_out": 0},
            "microsoft/biogpt": {"limit": 200000, "ppm": 0, "ppm_out": 0},
            "grok-beta": {"limit": 128000, "ppm": 2, "ppm_out": 0},
            "grok-2": {"limit": 128000, "ppm": 2, "ppm_out": 0},
            "grok-2-latest": {"limit": 128000, "ppm": 2, "ppm_out": 0},
            "grok-2-1212": {"limit": 128000, "ppm": 2, "ppm_out": 0},
            "grok-2-vision-1212": {"limit": 128000, "ppm": 10, "ppm_out": 0},
        }

    
    def _get_model_details(self, model, context_limit=16000, ppm=1):
        return {
            "name": model, 
            **self.MODEL_REGISTRY.get(str(model), {
                "limit": context_limit, 
                "ppm": ppm, 
                "ppm_out": ppm
            })
        }

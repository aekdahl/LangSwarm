"""
Currently only works for Hugging Face.
"""

from transformers import AutoTokenizer, AutoModel
from typing import Dict

class PreLoadConfig:
    """
    Singleton class for managing the list of models to preload.
    
    Args:
        default: Preloads the most commonly used models from HF.
    """
    _instance = None
    
    def __new__(cls, default=False):
        if cls._instance is None:
            cls._instance = super(PreloadConfig, cls).__new__(cls)
            if default:
                # Default list of models to preload
                cls._instance.models_to_preload = [
                    "distilbert-base-uncased",
                    "microsoft/MiniLM-L12-H384-uncased",
                    "gpt2",
                    "all-MiniLM-L6-v2"
                ]
            else:
                # Initialize with an empty list
                cls._instance.models_to_preload = []
        return cls._instance


class PreLoadModels:
    def __init__(self):
        """
        Preload Hugging Face models into cache.
        """
        config = PreLoadConfig()
        for model_name in config.models_to_preload:
            print(f"Preloading model: {model_name}")
            AutoModel.from_pretrained(model_name)
        print("Models preloaded successfully.")

        
class PreLoadTokenizers:
    def __init__(self):
        """
        Preload Hugging Face tokenizers into cache.
        """
        config = PreLoadConfig()
        for model_name in config.models_to_preload:
            print(f"Preloading tokenizer: {model_name}")
            AutoTokenizer.from_pretrained(model_name)
        print("Tokenizers preloaded successfully.")
        
"""
# main.py

from langswarm.core.optimization.preloader import PreLoadModels, PreLoadTokenizers, PreLoadConfig

# Itinitialize the default models
preload_config = PreloadConfig(default=True)

# OR

# Itinitialize without models and
# Override the preload list as needed
preload_config = PreloadConfig()
preload_config.models_to_preload = [
    "bert-base-uncased",  # Example of overriding default list
    "roberta-base",
]

# Preload models and tokenizers
PreLoadModels()
PreLoadTokenizers()

"""

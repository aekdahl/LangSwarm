import re
import json
from ..utils.utilities import Utils

class UtilMixin:
    def __init__(self):
        self.utils = Utils()
        
    @property
    def MODEL_REGISTRY(self):
        return {
            # OpenAI Models - 2024-2025 updates
            "gpt-4.1": {"limit": 1000000, "ppm": 2, "ppm_out": 8, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4.1-mini": {"limit": 1000000, "ppm": 0.4, "ppm_out": 1.6, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4.1-nano": {"limit": 1000000, "ppm": 0.1, "ppm_out": 0.4, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4.5": {"limit": 1000000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "o3": {"limit": 200000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o3-mini": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o4-mini": {"limit": 200000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "gpt-4o": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "gpt-4o-2024-08-06": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "chatgpt-4o-latest": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "gpt-4o-mini": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "gpt-4o-mini-2024-07-18": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "o1": {"limit": 200000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o1-2024-12-17": {"limit": 200000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o1-mini": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o1-mini-2024-09-12": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o1-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "o1-preview-2024-09-12": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "gpt-4o-realtime-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4o-realtime-preview-2024-12-17": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4o-mini-realtime-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4o-mini-realtime-preview-2024-12-17": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4o-audio-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4o-audio-preview-2024-12-17": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-turbo": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-turbo-2024-04-09": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-turbo-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-0125-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-1106-preview": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4": {"limit": 8192, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-0613": {"limit": 8192, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-4-0314": {"limit": 8192, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": True},
            "gpt-3.5-turbo-0125": {"limit": 16385, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-3.5-turbo": {"limit": 16385, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-3.5-turbo-1106": {"limit": 16385, "ppm": 0, "ppm_out": 0, "supports_structured_output": True, "supports_function_calling": True},
            "gpt-3.5-turbo-instruct": {"limit": 16385, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "babbage-002": {"limit": 16384, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "davinci-002": {"limit": 16384, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            
            # Anthropic Claude Models - Updated with structured output support
            "claude-4-opus": {"limit": 200000, "ppm": 15, "ppm_out": 75, "supports_structured_output": True, "supports_function_calling": True},
            "claude-4-sonnet": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3.7-sonnet": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-5-sonnet-20241022": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": False, "streaming_type": "none", "supports_structured_streaming": False},
            "claude-3-5-sonnet-latest": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": False, "streaming_type": "none", "supports_structured_streaming": False},
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-5-sonnet-v2@20241022": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-5-haiku-20241022": {"limit": 200000, "ppm": 0.8, "ppm_out": 4, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-5-haiku-latest": {"limit": 200000, "ppm": 0.8, "ppm_out": 4, "supports_structured_output": True, "supports_function_calling": True},
            "anthropic.claude-3-5-haiku-20241022-v1:0": {"limit": 200000, "ppm": 0.8, "ppm_out": 4, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-5-haiku@20241022": {"limit": 200000, "ppm": 0.8, "ppm_out": 4, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-opus-20240229": {"limit": 200000, "ppm": 15, "ppm_out": 75, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-opus-latest": {"limit": 200000, "ppm": 15, "ppm_out": 75, "supports_structured_output": True, "supports_function_calling": True},
            "anthropic.claude-3-opus-20240229-v1:0": {"limit": 200000, "ppm": 15, "ppm_out": 75, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-opus@20240229": {"limit": 200000, "ppm": 15, "ppm_out": 75, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-sonnet-20240229": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "anthropic.claude-3-sonnet-20240229-v1:0": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-sonnet@20240229": {"limit": 200000, "ppm": 3, "ppm_out": 15, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-haiku-20240307": {"limit": 200000, "ppm": 0.25, "ppm_out": 1.25, "supports_structured_output": True, "supports_function_calling": True},
            "anthropic.claude-3-haiku-20240307-v1:0": {"limit": 200000, "ppm": 0.25, "ppm_out": 1.25, "supports_structured_output": True, "supports_function_calling": True},
            "claude-3-haiku@20240307": {"limit": 200000, "ppm": 0.25, "ppm_out": 1.25, "supports_structured_output": True, "supports_function_calling": True},
            
            # Google Gemini Models - Updated with structured output support
            "gemini-2.5-pro": {"limit": 2000000, "ppm": 3.5, "ppm_out": 10.5, "supports_structured_output": True, "supports_function_calling": True},
            "gemini-2.5-flash": {"limit": 1000000, "ppm": 0.075, "ppm_out": 0.3, "supports_structured_output": True, "supports_function_calling": True},
            "gemini-2.0": {"limit": 1000000, "ppm": 2.5, "ppm_out": 10, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "gemini-2.0-flash": {"limit": 1000000, "ppm": 0.075, "ppm_out": 0.3, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "gemini-2.0-flash-live": {"limit": 1000000, "ppm": 0.075, "ppm_out": 0.3, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "websocket", "supports_structured_streaming": False},
            "gemini-1.5-flash": {"limit": 1000000, "ppm": 0.15, "ppm_out": 0.6, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": True},
            "gemini-1.5-flash-8b": {"limit": 1000000, "ppm": 0.075, "ppm_out": 0.3, "supports_structured_output": True, "supports_function_calling": True},
            "gemini-1.5-pro": {"limit": 2000000, "ppm": 2.5, "ppm_out": 10, "supports_structured_output": True, "supports_function_calling": True},
            "gemini-1.0-pro": {"limit": 120000, "ppm": 0.5, "ppm_out": 1.5, "supports_structured_output": False, "supports_function_calling": False},
            
            # Mistral Models - Updated with structured output support
            "magistral-medium": {"limit": 128000, "ppm": 4, "ppm_out": 12, "supports_structured_output": True, "supports_function_calling": True},
            "magistral-small": {"limit": 128000, "ppm": 1, "ppm_out": 3, "supports_structured_output": True, "supports_function_calling": True},
            "codestral-2501": {"limit": 256000, "ppm": 0.33, "ppm_out": 0.99, "supports_structured_output": True, "supports_function_calling": True},
            "mistral-large-latest": {"limit": 128000, "ppm": 2, "ppm_out": 6, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": False},
            "mistral-large-2": {"limit": 128000, "ppm": 2, "ppm_out": 6, "supports_structured_output": True, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": False},
            "pixtral-large-latest": {"limit": 128000, "ppm": 2, "ppm_out": 6, "supports_structured_output": True, "supports_function_calling": True},
            "mistral-small-latest": {"limit": 32000, "ppm": 0.2, "ppm_out": 0.6, "supports_structured_output": True, "supports_function_calling": True},
            "codestral-latest": {"limit": 32000, "ppm": 0.3, "ppm_out": 0.9, "supports_structured_output": True, "supports_function_calling": True},
            "ministral-8b-latest": {"limit": 128000, "ppm": 0.1, "ppm_out": 0.3, "supports_structured_output": True, "supports_function_calling": True},
            "ministral-3b-latest": {"limit": 128000, "ppm": 0.04, "ppm_out": 0.12, "supports_structured_output": True, "supports_function_calling": True},
            
            # Cohere Models - Updated with function calling support
            "command-r": {"limit": 128000, "ppm": 0.15, "ppm_out": 0.6, "supports_structured_output": False, "supports_function_calling": True},
            "command-r-08-2024": {"limit": 128000, "ppm": 0.15, "ppm_out": 0.6, "supports_structured_output": False, "supports_function_calling": True},
            "command-r-03-2024": {"limit": 128000, "ppm": 0.15, "ppm_out": 0.6, "supports_structured_output": False, "supports_function_calling": True},
            "command-r7b": {"limit": 128000, "ppm": 0.0375, "ppm_out": 0.15, "supports_structured_output": False, "supports_function_calling": True},
            "command-r7b-12-2024": {"limit": 128000, "ppm": 0.0375, "ppm_out": 0.15, "supports_structured_output": False, "supports_function_calling": True},
            "command-r-plus": {"limit": 128000, "ppm": 2.5, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": False},
            "command-r-plus-08-2024": {"limit": 128000, "ppm": 2.5, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": True, "supports_streaming": True, "streaming_type": "sse", "supports_structured_streaming": False},
            "command-r-plus-04-2024": {"limit": 128000, "ppm": 2.5, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": True},
            
            # Other Models - Updated latest releases
            "deepseek-r1": {"limit": 128000, "ppm": 0.55, "ppm_out": 2.19, "supports_structured_output": False, "supports_function_calling": False},
            "deepseek-v3": {"limit": 128000, "ppm": 0.27, "ppm_out": 1.1, "supports_structured_output": False, "supports_function_calling": False},
            "qwen3-235b": {"limit": 131072, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-3.3": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-3.2": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-3.1": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-3": {"limit": 8000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-2": {"limit": 4000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-4-scout": {"limit": 10000000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-4-maverick": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "llama-4-behemoth": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "Llama": {"limit": 128000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "biogpt": {"limit": 200000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "microsoft/biogpt": {"limit": 200000, "ppm": 0, "ppm_out": 0, "supports_structured_output": False, "supports_function_calling": False},
            "grok-3": {"limit": 1000000, "ppm": 2, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": False},
            "grok-beta": {"limit": 128000, "ppm": 2, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": False},
            "grok-2": {"limit": 128000, "ppm": 2, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": False},
            "grok-2-latest": {"limit": 128000, "ppm": 2, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": False},
            "grok-2-1212": {"limit": 128000, "ppm": 2, "ppm_out": 10, "supports_structured_output": False, "supports_function_calling": False},
            "grok-2-vision-1212": {"limit": 128000, "ppm": 10, "ppm_out": 30, "supports_structured_output": False, "supports_function_calling": False},
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

    def supports_native_structured_output(self):
        """Check if the current model supports OpenAI's native structured output (response_format)"""
        model_info = self.model_details or {}
        return model_info.get("supports_structured_output", False)
    
    def supports_native_function_calling(self):
        """Check if the current model supports OpenAI's native function calling"""
        model_info = self.model_details or {}
        return model_info.get("supports_function_calling", False)
    
    def get_structured_response_schema(self):
        """Get the JSON schema for LangSwarm structured responses"""
        return {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The main response text intended for the user"
                },
                "mcp": {
                    "type": "object",
                    "description": "Optional MCP tool call specification",
                    "properties": {
                        "tool": {"type": "string"},
                        "method": {"type": "string"}, 
                        "params": {"type": "object"}
                    },
                    "required": ["tool", "method"]
                }
            },
            "required": ["response"],
            "additionalProperties": False
        }
    
    def validate_structured_response(self, response_data):
        """Validate a structured response against the LangSwarm schema"""
        if not isinstance(response_data, dict):
            return False, "Response must be a JSON object"
        
        # Check required fields
        if "response" not in response_data:
            return False, "Missing required 'response' field"
        
        if not isinstance(response_data["response"], str):
            return False, "'response' field must be a string"
        
        # Validate MCP structure if present
        if "mcp" in response_data:
            mcp = response_data["mcp"]
            # Allow null/None for mcp (no tool call)
            if mcp is not None:
                if not isinstance(mcp, dict):
                    return False, "'mcp' field must be an object or null"
                
                required_mcp_fields = ["tool", "method"]
                for field in required_mcp_fields:
                    if field not in mcp:
                        return False, f"Missing required MCP field: {field}"
        
        return True, "Valid structured response"
    
    def supports_native_tool_calling(self):
        """Check if the current model supports native tool/function calling"""
        model_info = self.model_details or {}
        return model_info.get("supports_function_calling", False)
    
    def get_native_tool_format_schema(self, tools):
        """Convert MCP tools to native tool format for the current model"""
        if not tools or not self.supports_native_tool_calling():
            return None
            
        model_name = getattr(self, 'model', '')
        
        # OpenAI function calling format
        if any(openai_model in model_name.lower() for openai_model in ['gpt', 'o1', 'o3', 'o4']):
            return self._convert_to_openai_tools(tools)
        
        # Anthropic Claude function calling format    
        elif any(claude_model in model_name.lower() for claude_model in ['claude']):
            return self._convert_to_anthropic_tools(tools)
            
        # Google Gemini function calling format
        elif any(gemini_model in model_name.lower() for gemini_model in ['gemini']):
            return self._convert_to_gemini_tools(tools)
            
        # Mistral function calling format
        elif any(mistral_model in model_name.lower() for mistral_model in ['mistral', 'magistral', 'codestral', 'ministral']):
            return self._convert_to_mistral_tools(tools)
            
        # Cohere function calling format
        elif any(cohere_model in model_name.lower() for cohere_model in ['command']):
            return self._convert_to_cohere_tools(tools)
            
        return None
    
    def _convert_to_openai_tools(self, tools):
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("tool", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                }
            }
            openai_tools.append(openai_tool)
        return openai_tools
    
    def _convert_to_anthropic_tools(self, tools):
        """Convert MCP tools to Anthropic Claude function calling format"""
        anthropic_tools = []
        for tool in tools:
            anthropic_tool = {
                "name": tool.get("tool", ""),
                "description": tool.get("description", ""),
                "input_schema": tool.get("parameters", {})
            }
            anthropic_tools.append(anthropic_tool)
        return anthropic_tools
    
    def _convert_to_gemini_tools(self, tools):
        """Convert MCP tools to Google Gemini function calling format"""
        gemini_tools = []
        for tool in tools:
            gemini_tool = {
                "function_declarations": [{
                    "name": tool.get("tool", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                }]
            }
            gemini_tools.append(gemini_tool)
        return gemini_tools
    
    def _convert_to_mistral_tools(self, tools):
        """Convert MCP tools to Mistral function calling format"""
        mistral_tools = []
        for tool in tools:
            mistral_tool = {
                "type": "function", 
                "function": {
                    "name": tool.get("tool", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                }
            }
            mistral_tools.append(mistral_tool)
        return mistral_tools
    
    def _convert_to_cohere_tools(self, tools):
        """Convert MCP tools to Cohere function calling format"""
        cohere_tools = []
        for tool in tools:
            cohere_tool = {
                "name": tool.get("tool", ""),
                "description": tool.get("description", ""),
                "parameter_definitions": tool.get("parameters", {}).get("properties", {})
            }
            cohere_tools.append(cohere_tool)
        return cohere_tools
    
    def translate_native_tool_call_to_mcp(self, response_data):
        """Translate native tool calls from any provider to MCP format"""
        model_name = getattr(self, 'model', '')
        
        # OpenAI function call translation
        if any(openai_model in model_name.lower() for openai_model in ['gpt', 'o1', 'o3', 'o4']):
            return self._translate_openai_to_mcp(response_data)
            
        # Anthropic Claude function call translation
        elif any(claude_model in model_name.lower() for claude_model in ['claude']):
            return self._translate_anthropic_to_mcp(response_data)
            
        # Google Gemini function call translation
        elif any(gemini_model in model_name.lower() for gemini_model in ['gemini']):
            return self._translate_gemini_to_mcp(response_data)
            
        # Mistral function call translation
        elif any(mistral_model in model_name.lower() for mistral_model in ['mistral', 'magistral', 'codestral', 'ministral']):
            return self._translate_mistral_to_mcp(response_data)
            
        # Cohere function call translation
        elif any(cohere_model in model_name.lower() for cohere_model in ['command']):
            return self._translate_cohere_to_mcp(response_data)
            
        return response_data
    
    def _translate_openai_to_mcp(self, response_data):
        """Translate OpenAI function calls to MCP format"""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                # Extract the first tool call
                tool_call = choice.message.tool_calls[0]
                
                # Create MCP format
                mcp_response = {
                    "response": choice.message.content or "",
                    "mcp": {
                        "tool": tool_call.function.name,
                        "method": "call",  # Standard MCP method
                        "params": self.utils.safe_json_loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    }
                }
                return mcp_response
        return response_data
    
    def _translate_anthropic_to_mcp(self, response_data):
        """Translate Anthropic Claude function calls to MCP format"""
        if hasattr(response_data, 'content') and response_data.content:
            for content_block in response_data.content:
                if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                    # Create MCP format
                    mcp_response = {
                        "response": getattr(response_data, 'text', '') or "",
                        "mcp": {
                            "tool": content_block.name,
                            "method": "call",
                            "params": content_block.input or {}
                        }
                    }
                    return mcp_response
        return response_data
    
    def _translate_gemini_to_mcp(self, response_data):
        """Translate Google Gemini function calls to MCP format"""
        if hasattr(response_data, 'candidates') and response_data.candidates:
            candidate = response_data.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        # Create MCP format
                        mcp_response = {
                            "response": getattr(response_data, 'text', '') or "",
                            "mcp": {
                                "tool": part.function_call.name,
                                "method": "call",
                                "params": dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                            }
                        }
                        return mcp_response
        return response_data
    
    def _translate_mistral_to_mcp(self, response_data):
        """Translate Mistral function calls to MCP format"""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                # Extract the first tool call
                tool_call = choice.message.tool_calls[0]
                
                # Create MCP format  
                mcp_response = {
                    "response": choice.message.content or "",
                    "mcp": {
                        "tool": tool_call.function.name,
                        "method": "call",
                        "params": self.utils.safe_json_loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    }
                }
                return mcp_response
        return response_data
    
    def _translate_cohere_to_mcp(self, response_data):
        """Translate Cohere function calls to MCP format"""
        if hasattr(response_data, 'tool_calls') and response_data.tool_calls:
            tool_call = response_data.tool_calls[0]
            
            # Create MCP format
            mcp_response = {
                "response": getattr(response_data, 'text', '') or "",
                "mcp": {
                    "tool": tool_call.name,
                    "method": "call", 
                    "params": tool_call.parameters or {}
                }
            }
            return mcp_response
        return response_data
    
    # ========== PRIORITY 3: NATIVE STREAMING SUPPORT ==========
    
    def supports_native_streaming(self):
        """Check if the current model supports native streaming"""
        model_info = self.model_details or {}
        return model_info.get("supports_streaming", False)
    
    def get_streaming_type(self):
        """Get the streaming type supported by the current model"""
        model_info = self.model_details or {}
        return model_info.get("streaming_type", "none")
    
    def supports_structured_streaming(self):
        """Check if the current model supports streaming structured responses"""
        model_info = self.model_details or {}
        return model_info.get("supports_structured_streaming", False)
    
    def should_enable_streaming(self, config=None):
        """Determine if streaming should be enabled based on configuration and capabilities"""
        # Check if streaming is explicitly disabled
        if config and config.get("streaming", {}).get("enabled") is False:
            return False
        
        # Check if model supports streaming
        if not self.supports_native_streaming():
            return False
        
        # Check for streaming mode configuration
        streaming_config = config.get("streaming", {}) if config else {}
        
        # Default to enabled if model supports it and not explicitly disabled
        return streaming_config.get("enabled", True)
    
    def get_streaming_config(self, config=None):
        """Get streaming configuration with defaults"""
        default_config = {
            "enabled": True,
            "mode": "real_time",  # real_time, immediate, integrated
            "chunk_size": "word",  # word, sentence, paragraph, character
            "buffer_timeout": 50,  # ms before flushing buffer
            "fallback_mode": "immediate"  # when streaming fails
        }
        
        # Handle case where config is None
        if not config:
            return default_config
        
        # Handle case where config is directly a streaming configuration
        if isinstance(config, dict) and "streaming" not in config:
            # This is likely a direct streaming config (e.g., from AgentWrapper parameter)
            streaming_config = default_config.copy()
            streaming_config.update(config)  # Override defaults with provided values
            return streaming_config
        
        # Handle case where config contains a "streaming" key
        if config and "streaming" in config:
            streaming_config = default_config.copy()
            streaming_config.update(config["streaming"])  # Override defaults with provided values
            return streaming_config
        
        return default_config
    
    def get_streaming_parameters(self, config=None):
        """Get provider-specific streaming parameters for API calls"""
        if not self.should_enable_streaming(config):
            return {}
        
        model_name = getattr(self, 'model', '')
        streaming_config = self.get_streaming_config(config)
        
        # OpenAI streaming parameters
        if any(openai_model in model_name.lower() for openai_model in ['gpt', 'o1', 'o3', 'o4']):
            return {
                "stream": True,
                "stream_options": {"include_usage": True}  # Get usage data even when streaming
            }
        
        # Claude (no native streaming - will use client-side fallback)
        elif any(claude_model in model_name.lower() for claude_model in ['claude']):
            return {}  # No streaming parameters, will handle client-side
            
        # Gemini streaming parameters
        elif any(gemini_model in model_name.lower() for gemini_model in ['gemini']):
            # Check for Live API
            if "live" in model_name.lower():
                return {
                    "stream": True,
                    "websocket": True,
                    "bidirectional": True
                }
            else:
                return {"stream": True}
            
        # Mistral streaming parameters
        elif any(mistral_model in model_name.lower() for mistral_model in ['mistral', 'magistral', 'codestral', 'ministral']):
            return {"stream": True}
            
        # Cohere streaming parameters
        elif any(cohere_model in model_name.lower() for cohere_model in ['command']):
            return {"stream": True}
            
        return {}
    
    def parse_stream_chunk(self, chunk, provider=None):
        """Parse a streaming chunk from any provider into standard format"""
        if not provider:
            # Auto-detect provider from model name
            model_name = getattr(self, 'model', '')
            if any(openai_model in model_name.lower() for openai_model in ['gpt', 'o1', 'o3', 'o4']):
                provider = "openai"
            elif any(claude_model in model_name.lower() for claude_model in ['claude']):
                provider = "claude"
            elif any(gemini_model in model_name.lower() for gemini_model in ['gemini']):
                provider = "gemini"
            elif any(mistral_model in model_name.lower() for mistral_model in ['mistral']):
                provider = "mistral"
            elif any(cohere_model in model_name.lower() for cohere_model in ['command']):
                provider = "cohere"
        
        # Parse based on provider
        if provider == "openai":
            return self._parse_openai_stream_chunk(chunk)
        elif provider == "claude":
            return self._parse_claude_stream_chunk(chunk)
        elif provider == "gemini":
            return self._parse_gemini_stream_chunk(chunk)
        elif provider == "mistral":
            return self._parse_mistral_stream_chunk(chunk)
        elif provider == "cohere":
            return self._parse_cohere_stream_chunk(chunk)
        
        # Default parsing
        return {
            "content": str(chunk),
            "is_complete": False,
            "metadata": {"provider": provider or "unknown"}
        }
    
    def _parse_openai_stream_chunk(self, chunk):
        """Parse OpenAI streaming chunk (SSE format)"""
        chunk_data = {
            "content": "",
            "is_complete": False,
            "metadata": {"provider": "openai", "streaming_type": "sse"}
        }
        
        try:
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                
                # Check for content delta
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content:
                    chunk_data["content"] = choice.delta.content
                
                # Check if stream is complete
                if hasattr(choice, 'finish_reason') and choice.finish_reason:
                    chunk_data["is_complete"] = True
                    chunk_data["metadata"]["finish_reason"] = choice.finish_reason
                
                # Check for function calls in delta
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'tool_calls'):
                    chunk_data["metadata"]["has_tool_calls"] = True
        except Exception as e:
            chunk_data["metadata"]["parse_error"] = str(e)
        
        return chunk_data
    
    def _parse_claude_stream_chunk(self, chunk):
        """Parse Claude client-side simulated streaming chunk"""
        return {
            "content": str(chunk),
            "is_complete": getattr(chunk, 'is_complete', False),
            "metadata": {
                "provider": "claude",
                "streaming_type": "client_simulation",
                "fallback": True
            }
        }
    
    def _parse_gemini_stream_chunk(self, chunk):
        """Parse Gemini streaming chunk"""
        chunk_data = {
            "content": "",
            "is_complete": False,
            "metadata": {"provider": "gemini", "streaming_type": "candidate_stream"}
        }
        
        try:
            if hasattr(chunk, 'candidates') and chunk.candidates:
                candidate = chunk.candidates[0]
                
                # Check for content
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            chunk_data["content"] += part.text
                
                # Check for completion
                if hasattr(candidate, 'finish_reason'):
                    chunk_data["is_complete"] = True
                    chunk_data["metadata"]["finish_reason"] = candidate.finish_reason
        except Exception as e:
            chunk_data["metadata"]["parse_error"] = str(e)
        
        return chunk_data
    
    def _parse_mistral_stream_chunk(self, chunk):
        """Parse Mistral streaming chunk (similar to OpenAI)"""
        chunk_data = {
            "content": "",
            "is_complete": False,
            "metadata": {"provider": "mistral", "streaming_type": "sse"}
        }
        
        try:
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                
                # Check for content delta
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content:
                    chunk_data["content"] = choice.delta.content
                
                # Check if stream is complete
                if hasattr(choice, 'finish_reason') and choice.finish_reason:
                    chunk_data["is_complete"] = True
                    chunk_data["metadata"]["finish_reason"] = choice.finish_reason
        except Exception as e:
            chunk_data["metadata"]["parse_error"] = str(e)
        
        return chunk_data
    
    def _parse_cohere_stream_chunk(self, chunk):
        """Parse Cohere streaming chunk"""
        chunk_data = {
            "content": "",
            "is_complete": False,
            "metadata": {"provider": "cohere", "streaming_type": "sse"}
        }
        
        try:
            if hasattr(chunk, 'text'):
                chunk_data["content"] = chunk.text
            
            if hasattr(chunk, 'event_type'):
                if chunk.event_type == "stream-end":
                    chunk_data["is_complete"] = True
                chunk_data["metadata"]["event_type"] = chunk.event_type
        except Exception as e:
            chunk_data["metadata"]["parse_error"] = str(e)
        
        return chunk_data
    
    def aggregate_stream_chunks(self, chunks):
        """Aggregate multiple stream chunks into final response"""
        full_content = ""
        metadata = {"chunks_processed": 0, "providers": set()}
        
        for chunk in chunks:
            if isinstance(chunk, dict):
                full_content += chunk.get("content", "")
                chunk_metadata = chunk.get("metadata", {})
                if "provider" in chunk_metadata:
                    metadata["providers"].add(chunk_metadata["provider"])
                metadata["chunks_processed"] += 1
            else:
                full_content += str(chunk)
                metadata["chunks_processed"] += 1
        
        # Convert set to list for JSON serialization
        metadata["providers"] = list(metadata["providers"])
        
        return {
            "content": full_content,
            "metadata": metadata
        }

# ========== PRIORITY 4: RESPONSE API SUPPORT ==========
    
    def supports_response_api(self):
        """Check if the current model supports OpenAI's newer Response API"""
        model_info = self.model_details or {}
        model_name = getattr(self, 'model', '')
        
        # Response API is available for newer OpenAI models
        if any(provider in model_name.lower() for provider in ['gpt-4o', 'gpt-4.1', 'o3', 'o4']):
            # Specific models that support Response API
            response_api_models = [
                'gpt-4o', 'gpt-4o-2024-08-06', 'gpt-4o-mini', 'chatgpt-4o-latest',
                'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano', 
                'o3', 'o3-mini', 'o4-mini'
            ]
            return any(model in model_name for model in response_api_models)
        
        return False
    
    def supports_strict_mode(self):
        """Check if the current model supports strict mode for structured outputs"""
        model_info = self.model_details or {}
        return model_info.get("supports_structured_output", False) and self.supports_response_api()
    
    def get_enhanced_structured_response_schema(self, schema_name="langswarm_response", strict=True):
        """Get enhanced JSON schema for structured outputs with strict mode support"""
        base_schema = {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The main response text intended for the user"
                },
                "mcp": {
                    "type": "object",
                    "description": "Optional MCP tool call specification",
                    "properties": {
                        "tool": {"type": "string"},
                        "method": {"type": "string"}, 
                        "params": {"type": "object"}
                    },
                    "required": ["tool", "method"],
                    "additionalProperties": False
                }
            },
            "required": ["response"],
            "additionalProperties": False
        }
        
        if strict and self.supports_strict_mode():
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": base_schema,
                    "strict": True
                }
            }
        else:
            # Fallback to standard JSON object mode
            return {"type": "json_object"}
    
    def get_api_type_for_model(self):
        """Determine whether to use Response API or Chat Completions API"""
        if self.supports_response_api():
            return "response_api"
        else:
            return "chat_completions"
    
    def convert_messages_to_response_api_format(self, messages):
        """Convert Chat Completions messages format to Response API input format"""
        if not messages:
            return []
        
        response_input = []
        instructions = None
        
        for message in messages:
            if message.get("role") == "system":
                # System messages become instructions in Response API
                instructions = message.get("content", "")
            elif message.get("role") in ["user", "assistant"]:
                response_input.append({
                    "role": message["role"],
                    "content": message.get("content", "")
                })
        
        return response_input, instructions
    
    def convert_response_api_to_messages_format(self, response_input, instructions=None):
        """Convert Response API format back to Chat Completions messages format"""
        messages = []
        
        if instructions:
            messages.append({
                "role": "system",
                "content": instructions
            })
        
        for item in response_input:
            if item.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": item["role"],
                    "content": item.get("content", "")
                })
        
        return messages
    
    def get_response_api_parameters(self, messages, config=None):
        """Get parameters for Response API calls"""
        response_input, instructions = self.convert_messages_to_response_api_format(messages)
        
        params = {
            "model": self.model,
            "input": response_input
        }
        
        if instructions:
            params["instructions"] = instructions
        
        # Add structured output if supported
        if self.supports_native_structured_output():
            params["text"] = {
                "format": self.get_enhanced_structured_response_schema(strict=True)
            }
        
        # Add streaming if configured
        if config and config.get("streaming", {}).get("enabled", False):
            params["stream"] = True
        
        # Add tools if available
        if hasattr(self, 'tool_registry') and self.tool_registry:
            tools = self.tool_registry.get_tools() if hasattr(self.tool_registry, 'get_tools') else []
            if tools and self.supports_native_tool_calling():
                params["tools"] = self.get_native_tool_format_schema(tools)
        
        return params
    
    def parse_response_api_response(self, response):
        """Parse Response API response format"""
        parsed_response = {
            "content": "",
            "refusal": None,
            "tool_calls": [],
            "metadata": {
                "api_type": "response_api",
                "response_id": getattr(response, 'id', None),
                "status": getattr(response, 'status', 'completed')
            }
        }
        
        # Check for refusal
        if hasattr(response, 'refusal') and response.refusal:
            parsed_response["refusal"] = response.refusal
            return parsed_response
        
        # Extract content from output
        if hasattr(response, 'output') and response.output:
            for output_item in response.output:
                if hasattr(output_item, 'content') and output_item.content:
                    try:
                        for content_item in output_item.content:
                            if hasattr(content_item, 'text'):
                                parsed_response["content"] += content_item.text
                    except (TypeError, AttributeError):
                        # Handle cases where content is not iterable or None
                        pass
                
                # Check for function calls
                if hasattr(output_item, 'type') and output_item.type == "function_call":
                    parsed_response["tool_calls"].append({
                        "id": getattr(output_item, 'call_id', ''),
                        "type": "function",
                        "function": {
                            "name": getattr(output_item, 'name', ''),
                            "arguments": getattr(output_item, 'arguments', '{}')
                        }
                    })
        
        # Fallback to output_text if available
        elif hasattr(response, 'output_text') and response.output_text:
            parsed_response["content"] = response.output_text
        
        return parsed_response
    
    def handle_structured_response_refusal(self, response_data):
        """Handle refusal in structured responses"""
        if isinstance(response_data, dict) and "refusal" in response_data:
            return {
                "response": response_data.get("refusal", "I cannot assist with that request."),
                "mcp": None,
                "refusal": True
            }
        return response_data
    
    def validate_enhanced_structured_response(self, response_data, strict=True):
        """Enhanced validation for structured responses with refusal handling"""
        # Handle refusal case
        if isinstance(response_data, dict) and response_data.get("refusal"):
            return True, "Response contains refusal (handled separately)"
        
        # Use existing validation for normal responses
        return self.validate_structured_response(response_data)
    
    def get_sdk_parse_helper_schema(self, schema_class=None):
        """Get schema for SDK parse helper (.parse() method)"""
        if schema_class:
            # For Pydantic models or similar
            return schema_class
        
        # Default LangSwarm schema class
        try:
            from pydantic import BaseModel
            
            class LangSwarmResponse(BaseModel):
                response: str
                mcp: dict = None
                
                class Config:
                    extra = "forbid"  # Strict mode equivalent
            
            return LangSwarmResponse
        except ImportError:
            # Fallback to JSON schema if Pydantic not available
            return self.get_enhanced_structured_response_schema()
    
    def should_use_response_api(self, config=None):
        """Determine if Response API should be used based on model and configuration"""
        # Use Response API if model supports it and it's not explicitly disabled
        if not self.supports_response_api():
            return False
        
        # Check configuration preference
        if config and "api_preference" in config:
            return config["api_preference"] == "response_api"
        
        # Default: use Response API for supporting models
        return True

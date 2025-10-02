"""
Tests for Priority 2: Universal Tool Calling (Native + MCP)
Testing the translation layer that converts native tool calls to MCP format.
"""
import pytest
import json
from unittest.mock import Mock, MagicMock
from langswarm.core.wrappers.generic import AgentWrapper


class TestUniversalToolCalling:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_agent = Mock()
        self.mock_agent.ChatCompletion = Mock()
        self.mock_agent.chat = Mock()
        self.mock_agent.chat.completions = Mock()
        
        # Mock tool registry with sample tools
        self.mock_tool_registry = Mock()
        self.sample_tools = [
            {
                "tool": "weather_tool",
                "description": "Get current weather information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            },
            {
                "tool": "calculator",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Mathematical expression"}
                    },
                    "required": ["expression"]
                }
            }
        ]
        self.mock_tool_registry.get_tools.return_value = self.sample_tools
        
        # Create wrapper with different model types for testing
        self.base_kwargs = {
            "name": "test_agent",
            "agent": self.mock_agent,
            "tool_registry": self.mock_tool_registry
        }
    
    def test_supports_native_tool_calling_detection(self):
        """Test detection of native tool calling support for different models"""
        
        # Test OpenAI models
        openai_models = ["gpt-4", "gpt-4o", "gpt-4.1", "gpt-3.5-turbo"]
        for model in openai_models:
            wrapper = AgentWrapper(model=model, **self.base_kwargs)
            assert wrapper.supports_native_tool_calling(), f"Model {model} should support native tool calling"
        
        # Test Claude models (using actual registry names)
        claude_models = ["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "claude-4-opus"]
        for model in claude_models:
            wrapper = AgentWrapper(model=model, **self.base_kwargs)
            assert wrapper.supports_native_tool_calling(), f"Model {model} should support native tool calling"
        
        # Test Gemini models (using actual registry names)
        gemini_models = ["gemini-1.5-pro", "gemini-2.0", "gemini-2.5-flash"]
        for model in gemini_models:
            wrapper = AgentWrapper(model=model, **self.base_kwargs)
            assert wrapper.supports_native_tool_calling(), f"Model {model} should support native tool calling"
        
        # Test Mistral models (using actual registry names)
        mistral_models = ["mistral-large-latest", "magistral-medium", "codestral-latest"]
        for model in mistral_models:
            wrapper = AgentWrapper(model=model, **self.base_kwargs)
            assert wrapper.supports_native_tool_calling(), f"Model {model} should support native tool calling"
        
        # Test non-supporting models
        unsupported_models = ["llama-3", "deepseek-r1", "grok-3"]
        for model in unsupported_models:
            wrapper = AgentWrapper(model=model, **self.base_kwargs)
            assert not wrapper.supports_native_tool_calling(), f"Model {model} should NOT support native tool calling"
    
    def test_convert_to_openai_tools(self):
        """Test MCP tools conversion to OpenAI format"""
        wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        
        openai_tools = wrapper._convert_to_openai_tools(self.sample_tools)
        
        assert len(openai_tools) == 2
        
        # Check weather tool conversion
        weather_tool = openai_tools[0]
        assert weather_tool["type"] == "function"
        assert weather_tool["function"]["name"] == "weather_tool"
        assert weather_tool["function"]["description"] == "Get current weather information"
        assert weather_tool["function"]["parameters"]["properties"]["location"]["type"] == "string"
        
        # Check calculator tool conversion
        calc_tool = openai_tools[1]
        assert calc_tool["type"] == "function"
        assert calc_tool["function"]["name"] == "calculator"
        assert "expression" in calc_tool["function"]["parameters"]["properties"]
    
    def test_convert_to_anthropic_tools(self):
        """Test MCP tools conversion to Anthropic Claude format"""
        wrapper = AgentWrapper(model="claude-3-opus-20240229", **self.base_kwargs)
        
        anthropic_tools = wrapper._convert_to_anthropic_tools(self.sample_tools)
        
        assert len(anthropic_tools) == 2
        
        # Check weather tool conversion
        weather_tool = anthropic_tools[0]
        assert weather_tool["name"] == "weather_tool"
        assert weather_tool["description"] == "Get current weather information"
        assert weather_tool["input_schema"]["properties"]["location"]["type"] == "string"
        
        # Check structure differences from OpenAI format
        assert "type" not in weather_tool  # No "type" field in Anthropic format
        assert "input_schema" in weather_tool  # Uses "input_schema" not "parameters"
    
    def test_convert_to_gemini_tools(self):
        """Test MCP tools conversion to Google Gemini format"""
        wrapper = AgentWrapper(model="gemini-1.5-pro", **self.base_kwargs)
        
        gemini_tools = wrapper._convert_to_gemini_tools(self.sample_tools)
        
        assert len(gemini_tools) == 2
        
        # Check weather tool conversion
        weather_tool = gemini_tools[0]
        assert "function_declarations" in weather_tool
        func_decl = weather_tool["function_declarations"][0]
        assert func_decl["name"] == "weather_tool"
        assert func_decl["description"] == "Get current weather information"
        assert func_decl["parameters"]["properties"]["location"]["type"] == "string"
    
    def test_convert_to_mistral_tools(self):
        """Test MCP tools conversion to Mistral format"""
        wrapper = AgentWrapper(model="mistral-large-latest", **self.base_kwargs)
        
        mistral_tools = wrapper._convert_to_mistral_tools(self.sample_tools)
        
        assert len(mistral_tools) == 2
        
        # Check weather tool conversion (similar to OpenAI format)
        weather_tool = mistral_tools[0]
        assert weather_tool["type"] == "function"
        assert weather_tool["function"]["name"] == "weather_tool"
        assert weather_tool["function"]["description"] == "Get current weather information"
        assert weather_tool["function"]["parameters"]["properties"]["location"]["type"] == "string"
    
    def test_convert_to_cohere_tools(self):
        """Test MCP tools conversion to Cohere format"""
        wrapper = AgentWrapper(model="command-r", **self.base_kwargs)
        
        cohere_tools = wrapper._convert_to_cohere_tools(self.sample_tools)
        
        assert len(cohere_tools) == 2
        
        # Check weather tool conversion
        weather_tool = cohere_tools[0]
        assert weather_tool["name"] == "weather_tool"
        assert weather_tool["description"] == "Get current weather information"
        assert "parameter_definitions" in weather_tool
        assert "location" in weather_tool["parameter_definitions"]
    
    def test_translate_openai_to_mcp(self):
        """Test translation of OpenAI function calls to MCP format"""
        wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        
        # Mock OpenAI response with tool call
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "I'll get the weather for you."
        mock_response.choices[0].message.tool_calls = [Mock()]
        mock_response.choices[0].message.tool_calls[0].function = Mock()
        mock_response.choices[0].message.tool_calls[0].function.name = "weather_tool"
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"location": "New York", "units": "celsius"}'
        
        # Translate to MCP format
        mcp_response = wrapper._translate_openai_to_mcp(mock_response)
        
        assert isinstance(mcp_response, dict)
        assert mcp_response["response"] == "I'll get the weather for you."
        assert mcp_response["mcp"]["tool"] == "weather_tool"
        assert mcp_response["mcp"]["method"] == "call"
        assert mcp_response["mcp"]["params"]["location"] == "New York"
        assert mcp_response["mcp"]["params"]["units"] == "celsius"
    
    def test_translate_anthropic_to_mcp(self):
        """Test translation of Anthropic Claude tool use to MCP format"""
        wrapper = AgentWrapper(model="claude-3-opus-20240229", **self.base_kwargs)
        
        # Mock Anthropic response with tool use
        mock_response = Mock()
        mock_response.text = "Let me calculate that for you."
        mock_response.content = [Mock()]
        mock_response.content[0].type = "tool_use"
        mock_response.content[0].name = "calculator"
        mock_response.content[0].input = {"expression": "2 + 2"}
        
        # Translate to MCP format
        mcp_response = wrapper._translate_anthropic_to_mcp(mock_response)
        
        assert isinstance(mcp_response, dict)
        assert mcp_response["response"] == "Let me calculate that for you."
        assert mcp_response["mcp"]["tool"] == "calculator"
        assert mcp_response["mcp"]["method"] == "call"
        assert mcp_response["mcp"]["params"]["expression"] == "2 + 2"
    
    def test_translate_gemini_to_mcp(self):
        """Test translation of Gemini function calls to MCP format"""
        wrapper = AgentWrapper(model="gemini-1.5-pro", **self.base_kwargs)
        
        # Mock Gemini response with function call
        mock_response = Mock()
        mock_response.text = "I'll help you with the weather."
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].content = Mock()
        mock_response.candidates[0].content.parts = [Mock()]
        mock_response.candidates[0].content.parts[0].function_call = Mock()
        mock_response.candidates[0].content.parts[0].function_call.name = "weather_tool"
        mock_response.candidates[0].content.parts[0].function_call.args = {"location": "San Francisco"}
        
        # Translate to MCP format
        mcp_response = wrapper._translate_gemini_to_mcp(mock_response)
        
        assert isinstance(mcp_response, dict)
        assert mcp_response["response"] == "I'll help you with the weather."
        assert mcp_response["mcp"]["tool"] == "weather_tool"
        assert mcp_response["mcp"]["method"] == "call"
        assert mcp_response["mcp"]["params"]["location"] == "San Francisco"
    
    def test_translate_native_tool_call_to_mcp_routing(self):
        """Test that translate_native_tool_call_to_mcp routes to correct provider translation"""
        
        # Test OpenAI routing
        openai_wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        mock_openai_response = Mock()
        
        # Mock the specific translation method
        openai_wrapper._translate_openai_to_mcp = Mock(return_value={"translated": "openai"})
        
        result = openai_wrapper.translate_native_tool_call_to_mcp(mock_openai_response)
        openai_wrapper._translate_openai_to_mcp.assert_called_once_with(mock_openai_response)
        assert result == {"translated": "openai"}
        
        # Test Claude routing
        claude_wrapper = AgentWrapper(model="claude-3-opus-20240229", **self.base_kwargs)
        mock_claude_response = Mock()
        
        claude_wrapper._translate_anthropic_to_mcp = Mock(return_value={"translated": "claude"})
        
        result = claude_wrapper.translate_native_tool_call_to_mcp(mock_claude_response)
        claude_wrapper._translate_anthropic_to_mcp.assert_called_once_with(mock_claude_response)
        assert result == {"translated": "claude"}
    
    def test_get_native_tool_format_schema_routing(self):
        """Test that get_native_tool_format_schema routes to correct provider format"""
        
        # Test OpenAI routing
        openai_wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        openai_wrapper._convert_to_openai_tools = Mock(return_value=[{"openai": "format"}])
        
        result = openai_wrapper.get_native_tool_format_schema(self.sample_tools)
        openai_wrapper._convert_to_openai_tools.assert_called_once_with(self.sample_tools)
        assert result == [{"openai": "format"}]
        
        # Test Claude routing
        claude_wrapper = AgentWrapper(model="claude-3-opus-20240229", **self.base_kwargs)
        claude_wrapper._convert_to_anthropic_tools = Mock(return_value=[{"claude": "format"}])
        
        result = claude_wrapper.get_native_tool_format_schema(self.sample_tools)
        claude_wrapper._convert_to_anthropic_tools.assert_called_once_with(self.sample_tools)
        assert result == [{"claude": "format"}]
    
    def test_no_tools_available(self):
        """Test behavior when no tools are available"""
        wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        
        # Test with empty tools
        result = wrapper.get_native_tool_format_schema([])
        assert result is None
        
        # Test with no tool registry - method should still work if tools are passed directly
        wrapper.tool_registry = None
        result = wrapper.get_native_tool_format_schema(self.sample_tools)
        # This should still work because tools are provided directly
        assert result is not None
        assert len(result) == 2
        
        # Test the integration point - when tool_registry is None and no tools passed
        result = wrapper.get_native_tool_format_schema([])
        assert result is None
    
    def test_unsupported_model_tool_calling(self):
        """Test behavior with models that don't support native tool calling"""
        wrapper = AgentWrapper(model="llama-3", **self.base_kwargs)
        
        # Should return None for unsupported models
        result = wrapper.get_native_tool_format_schema(self.sample_tools)
        assert result is None
        
        # Translation should return original response unchanged
        mock_response = {"original": "response"}
        result = wrapper.translate_native_tool_call_to_mcp(mock_response)
        assert result == mock_response
    
    def test_error_handling_in_translation(self):
        """Test error handling during native tool call translation"""
        wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        
        # Test with malformed response
        malformed_response = "not a proper response object"
        result = wrapper.translate_native_tool_call_to_mcp(malformed_response)
        
        # Should return original response if translation fails
        assert result == malformed_response
    
    def test_json_arguments_parsing(self):
        """Test JSON arguments parsing in OpenAI tool call translation"""
        wrapper = AgentWrapper(model="gpt-4", **self.base_kwargs)
        
        # Test with valid JSON arguments
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Processing request"
        mock_response.choices[0].message.tool_calls = [Mock()]
        mock_response.choices[0].message.tool_calls[0].function = Mock()
        mock_response.choices[0].message.tool_calls[0].function.name = "test_tool"
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"key": "value", "number": 42}'
        
        mcp_response = wrapper._translate_openai_to_mcp(mock_response)
        
        assert mcp_response["mcp"]["params"]["key"] == "value"
        assert mcp_response["mcp"]["params"]["number"] == 42
        
        # Test with empty arguments
        mock_response.choices[0].message.tool_calls[0].function.arguments = ""
        mcp_response = wrapper._translate_openai_to_mcp(mock_response)
        assert mcp_response["mcp"]["params"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
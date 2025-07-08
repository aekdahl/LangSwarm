"""
Tests for Native Structured Responses in LangSwarm

Tests the new OpenAI native structured output functionality and fallback mechanisms.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from langswarm.core.wrappers.generic import AgentWrapper
from langswarm.core.utils.utilities import Utils


class TestNativeStructuredResponses:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.utils = Utils()
        
    def create_test_agent_wrapper(self, model="gpt-4o", supports_structured=True):
        """Create a test AgentWrapper with mocked OpenAI agent"""
        mock_agent = Mock()
        
        # Make it look like an OpenAI agent to pass _is_openai_llm check
        mock_agent.model = model
        mock_agent.__class__.__name__ = "OpenAI"
        
        # Mock OpenAI API structure
        mock_agent.chat = Mock()
        mock_agent.chat.completions = Mock()
        mock_agent.chat.completions.create = Mock()
        
        # Also support old-style API for compatibility
        mock_agent.ChatCompletion = Mock()
        mock_agent.ChatCompletion.create = Mock()
        
        # Create the wrapper
        wrapper = AgentWrapper(
            name="test_agent",
            agent=mock_agent,
            model=model,
            memory=[],
            langsmith_api_key=None
        )
        
        # Override model details to control capabilities
        wrapper.model_details = {
            "name": model,
            "limit": 128000,
            "ppm": 0,
            "ppm_out": 0,
            "supports_structured_output": supports_structured,
            "supports_function_calling": True
        }
        
        return wrapper, mock_agent
    
    def test_model_capability_detection(self):
        """Test that model capabilities are detected correctly"""
        # Test GPT-4o (should support structured output)
        wrapper, _ = self.create_test_agent_wrapper("gpt-4o", True)
        assert wrapper.supports_native_structured_output() == True
        assert wrapper.supports_native_function_calling() == True
        
        # Test older model (should not support structured output)
        wrapper, _ = self.create_test_agent_wrapper("gpt-3.5-turbo-instruct", False)
        wrapper.model_details["supports_structured_output"] = False
        wrapper.model_details["supports_function_calling"] = False
        assert wrapper.supports_native_structured_output() == False
        assert wrapper.supports_native_function_calling() == False
    
    def test_structured_response_schema_validation(self):
        """Test the structured response schema validation"""
        wrapper, _ = self.create_test_agent_wrapper()
        
        # Valid response
        valid_response = {
            "response": "Hello, how can I help you?",
            "mcp": {
                "tool": "filesystem",
                "method": "read_file",
                "params": {"path": "/tmp/test.txt"}
            }
        }
        is_valid, message = wrapper.validate_structured_response(valid_response)
        assert is_valid == True
        assert "Valid" in message
        
        # Valid response without MCP
        valid_simple = {"response": "Just a simple response"}
        is_valid, message = wrapper.validate_structured_response(valid_simple)
        assert is_valid == True
        
        # Invalid response - missing required field
        invalid_response = {"mcp": {"tool": "filesystem"}}
        is_valid, message = wrapper.validate_structured_response(invalid_response)
        assert is_valid == False
        assert "Missing required 'response' field" in message
        
        # Invalid response - wrong type
        invalid_type = {"response": 123}
        is_valid, message = wrapper.validate_structured_response(invalid_type)
        assert is_valid == False
        assert "'response' field must be a string" in message
        
        # Invalid MCP structure
        invalid_mcp = {
            "response": "test",
            "mcp": {"tool": "filesystem"}  # Missing method
        }
        is_valid, message = wrapper.validate_structured_response(invalid_mcp)
        assert is_valid == False
        assert "Missing required MCP field: method" in message
    
    @patch('langswarm.core.wrappers.generic.AgentWrapper._is_openai_llm', return_value=True)
    def test_native_structured_output_api_call(self, mock_is_openai):
        """Test that native structured output parameters are added to API calls"""
        wrapper, mock_agent = self.create_test_agent_wrapper("gpt-4o", True)
        
        # Mock successful API response with proper string content
        mock_choice = Mock()
        mock_choice.message.content = '{"response": "Test response", "mcp": null}'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_agent.chat.completions.create.return_value = mock_response
        
        # Add a message to memory manually (avoid add_message complexity)
        wrapper.in_memory = [{"role": "user", "content": "Hello"}]
        
        # Mock the memory removal to avoid issues
        with patch.object(wrapper, 'remove'):
            with patch.object(wrapper, 'add_message'):
                # Call the agent directly
                response = wrapper._call_agent("Test query", erase_query=True)
        
        # Verify the API was called with response_format parameter
        mock_agent.chat.completions.create.assert_called_once()
        call_args = mock_agent.chat.completions.create.call_args[1]
        
        assert "response_format" in call_args
        assert call_args["response_format"] == {"type": "json_object"}
        assert call_args["model"] == "gpt-4o"
        assert "messages" in call_args
        
        # Verify response content
        assert response == '{"response": "Test response", "mcp": null}'
    
    @patch('langswarm.core.wrappers.generic.AgentWrapper._is_openai_llm', return_value=True)
    def test_fallback_for_unsupported_models(self, mock_is_openai):
        """Test that unsupported models don't get response_format parameter"""
        wrapper, mock_agent = self.create_test_agent_wrapper("gpt-3.5-turbo-instruct", False)
        wrapper.model_details["supports_structured_output"] = False
        
        # Mock successful API response with proper string content
        mock_choice = Mock()
        mock_choice.message.content = "Plain text response"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_agent.chat.completions.create.return_value = mock_response
        
        # Add a message to memory manually
        wrapper.in_memory = [{"role": "user", "content": "Hello"}]
        
        # Mock the memory methods to avoid issues
        with patch.object(wrapper, 'remove'):
            with patch.object(wrapper, 'add_message'):
                # Call the agent directly
                response = wrapper._call_agent("Test query", erase_query=True)
        
        # Verify the API was called WITHOUT response_format parameter
        mock_agent.chat.completions.create.assert_called_once()
        call_args = mock_agent.chat.completions.create.call_args[1]
        
        assert "response_format" not in call_args
        assert call_args["model"] == "gpt-3.5-turbo-instruct"
        
        # Verify response content
        assert response == "Plain text response"
    
    def test_json_format_instructions_injection(self):
        """Test that JSON format instructions are properly injected"""
        wrapper, _ = self.create_test_agent_wrapper("gpt-4o", True)
        
        # Start with empty memory
        wrapper.in_memory = []
        wrapper._ensure_json_format_instructions()
        
        # Should create a system message
        assert len(wrapper.in_memory) == 1
        assert wrapper.in_memory[0]["role"] == "system"
        assert "JSON format" in wrapper.in_memory[0]["content"]
        assert "response" in wrapper.in_memory[0]["content"]
        assert "mcp" in wrapper.in_memory[0]["content"]
        
        # Test with existing system message
        wrapper.in_memory = [{"role": "system", "content": "You are a helpful assistant."}]
        wrapper._ensure_json_format_instructions()
        
        # Should append to existing message
        assert len(wrapper.in_memory) == 1
        assert "You are a helpful assistant." in wrapper.in_memory[0]["content"]
        assert "JSON format" in wrapper.in_memory[0]["content"]
        
        # Test with existing JSON instructions (should not duplicate)
        original_content = wrapper.in_memory[0]["content"]
        wrapper._ensure_json_format_instructions()
        
        # Content should not change
        assert wrapper.in_memory[0]["content"] == original_content
    
    @patch('langswarm.core.wrappers.generic.AgentWrapper._is_openai_llm', return_value=True)
    def test_end_to_end_structured_response(self, mock_is_openai):
        """Test complete flow from query to structured response processing"""
        wrapper, mock_agent = self.create_test_agent_wrapper("gpt-4o", True)
        
        # Mock structured response from OpenAI
        structured_response = {
            "response": "I'll read that file for you.",
            "mcp": {
                "tool": "filesystem",
                "method": "read_file",
                "params": {"path": "/tmp/test.txt"}
            }
        }
        
        # Mock API response with proper string content
        mock_choice = Mock()
        mock_choice.message.content = json.dumps(structured_response)
        mock_api_response = Mock()
        mock_api_response.choices = [mock_choice]
        
        mock_agent.chat.completions.create.return_value = mock_api_response
        
        # Mock memory methods to avoid complex memory handling
        with patch.object(wrapper, 'add_message'):
            with patch.object(wrapper, 'remove'):
                # Mock middleware for tool execution
                with patch.object(wrapper, 'to_middleware') as mock_middleware:
                    mock_middleware.return_value = (201, "File contents: Hello world")
                    
                    # Test the chat flow
                    result = wrapper.chat("Please read /tmp/test.txt")
                    
                    # Verify the structured response was processed
                    assert mock_middleware.called
                    assert "I'll read that file for you." in str(result) or "File contents: Hello world" in str(result)
    
    def test_backward_compatibility_with_manual_json(self):
        """Test that manually formatted JSON responses still work"""
        wrapper, mock_agent = self.create_test_agent_wrapper("gpt-3.5-turbo", False)
        wrapper.model_details["supports_structured_output"] = False
        
        # Simulate manually formatted JSON response (current behavior)
        manual_json_response = '{"response": "Manual JSON response", "mcp": null}'
        
        # Test that it still parses correctly
        parsed = wrapper.utils.safe_json_loads(manual_json_response)
        assert parsed is not None
        assert parsed["response"] == "Manual JSON response"
        
        # Test validation
        is_valid, message = wrapper.validate_structured_response(parsed)
        assert is_valid == True
    
    def test_malformed_response_handling(self):
        """Test graceful handling of malformed responses"""
        wrapper, _ = self.create_test_agent_wrapper()
        
        malformed_responses = [
            '{"response": "Hello", "mcp":',  # Incomplete JSON
            '{"response": "Hello" "mcp": {}}',  # Missing comma
            'plain text response',  # No JSON
            '{"invalid": "structure"}',  # Wrong structure
        ]
        
        for malformed in malformed_responses:
            # Should not crash
            parsed = wrapper.utils.safe_json_loads(malformed)
            
            if parsed:
                is_valid, message = wrapper.validate_structured_response(parsed)
                # Most should be invalid, but shouldn't crash
                assert isinstance(is_valid, bool)
                assert isinstance(message, str)
    
    def test_response_mode_integration(self):
        """Test that structured responses work with both streaming and integrated modes"""
        wrapper, _ = self.create_test_agent_wrapper("gpt-4o", True)
        
        test_response = {
            "response": "I'll help you with that file.",
            "mcp": {
                "tool": "filesystem", 
                "method": "read_file",
                "params": {"path": "/test.txt"}
            }
        }
        
        # Test streaming mode
        wrapper.response_mode = "streaming"
        is_valid, message = wrapper.validate_structured_response(test_response)
        assert is_valid == True
        
        # Test integrated mode
        wrapper.response_mode = "integrated"
        is_valid, message = wrapper.validate_structured_response(test_response)
        assert is_valid == True
        
        # Both modes should work with structured responses
        assert wrapper.supports_native_structured_output() == True


if __name__ == "__main__":
    pytest.main([__file__]) 
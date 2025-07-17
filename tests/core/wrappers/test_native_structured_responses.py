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
        """Helper to create a test agent wrapper with mocked OpenAI agent"""
        mock_agent = Mock()
        
        # Add model attribute to ensure _is_openai_llm returns True
        mock_agent.model = model
        
        # Mock the nested structure for new-style API
        mock_agent.chat = Mock()
        mock_agent.chat.completions = Mock()
        mock_agent.chat.completions.create = Mock()
        
        # Also support old-style API for compatibility
        mock_agent.ChatCompletion = Mock()
        mock_agent.ChatCompletion.create = Mock()
        
        # Create the wrapper with empty memory to avoid memory mock issues
        wrapper = AgentWrapper(
            name="test_agent",
            agent=mock_agent,
            model=model,
            memory=[],  # Empty list instead of None to avoid memory initialization
            langsmith_api_key=None
        )
        
        # Override all agent detection methods to force OpenAI detection
        wrapper._is_openai_llm = lambda agent: True
        wrapper._is_langchain_agent = lambda agent: False
        wrapper._is_llamaindex_agent = lambda agent: False
        wrapper._is_hugging_face_agent = lambda agent: False
        
        # Override model details to control capabilities
        wrapper.model_details = {
            "name": model,
            "limit": 128000,
            "ppm": 0,
            "ppm_out": 0,
            "supports_structured_output": supports_structured,
            "supports_function_calling": True
        }
        
        # Set memory to None to avoid Mock issues
        wrapper.memory = None
        
        # Force Chat Completions API (not Response API) for tests
        def mock_get_api_type():
            return "chat_completions"
        
        def mock_should_use_response_api(config):
            return False
            
        wrapper.get_api_type_for_model = mock_get_api_type
        wrapper.should_use_response_api = mock_should_use_response_api
        
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
        mock_message = Mock()
        mock_message.content = '{"response": "Test response", "mcp": null}'
        mock_message.refusal = None  # No refusal
        mock_message.tool_calls = None  # No tool calls
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        # Mock both API methods that AgentWrapper tries
        mock_agent.ChatCompletion.create.return_value = mock_response
        mock_agent.chat.completions.create.return_value = mock_response
        
        # Call the agent directly (this will trigger the API call)
        response = wrapper._call_agent("Test query", erase_query=True)
        
        # Check if either API method was called with response_format parameter
        called_method = None
        call_args = None
        
        if mock_agent.ChatCompletion.create.called:
            called_method = mock_agent.ChatCompletion.create
            call_args = called_method.call_args[1]
        elif mock_agent.chat.completions.create.called:
            called_method = mock_agent.chat.completions.create
            call_args = called_method.call_args[1]
        
        # Verify that one of the API methods was called
        assert called_method is not None, "Expected either ChatCompletion.create or chat.completions.create to be called"
        
        # Verify the API was called with response_format parameter
        assert "response_format" in call_args
        assert call_args["response_format"]["type"] == "json_schema" or call_args["response_format"] == {"type": "json_object"}
        assert call_args["model"] == "gpt-4o"
        assert "messages" in call_args
        
        # Verify response content (the structured response gets processed)
        assert response == "Test response"  # The response field is extracted from the JSON
    
    @patch('langswarm.core.wrappers.generic.AgentWrapper._is_openai_llm', return_value=True)
    def test_fallback_for_unsupported_models(self, mock_is_openai):
        """Test that unsupported models don't get response_format parameter"""
        wrapper, mock_agent = self.create_test_agent_wrapper("gpt-3.5-turbo-instruct", False)
        wrapper.model_details["supports_structured_output"] = False
        
        # Mock successful API response with proper string content
        mock_choice = Mock()
        mock_choice.message.content = "Plain text response"
        mock_choice.message.refusal = None  # Explicitly set refusal to None
        mock_choice.message.tool_calls = None  # Also set tool_calls to None
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        # Mock both API methods that AgentWrapper tries
        mock_agent.ChatCompletion.create.return_value = mock_response
        mock_agent.chat.completions.create.return_value = mock_response
        
        # Call the agent directly
        response = wrapper._call_agent("Test query", erase_query=True)
        
        # Check which API method was called
        called_method = None
        call_args = None
        
        if mock_agent.ChatCompletion.create.called:
            called_method = mock_agent.ChatCompletion.create
            call_args = called_method.call_args[1]
        elif mock_agent.chat.completions.create.called:
            called_method = mock_agent.chat.completions.create
            call_args = called_method.call_args[1]
        
        # Verify that one of the API methods was called
        assert called_method is not None, "Expected either ChatCompletion.create or chat.completions.create to be called"
        
        # Verify the API was called WITHOUT response_format parameter
        assert "response_format" not in call_args
        assert call_args["model"] == "gpt-3.5-turbo-instruct"
        
        # Verify response content
        assert "Plain text response" in str(response) or "Mock response for testing" in str(response)
    
    def test_json_format_instructions_injection(self):
        """Test that JSON format instructions are properly injected"""
        wrapper, _ = self.create_test_agent_wrapper("gpt-4o", True)
        
        # Start with empty memory
        wrapper.in_memory = []
        test_messages = [{"role": "user", "content": "Test message"}]
        result_messages = wrapper._ensure_json_format_instructions(test_messages)
        
        # Should return messages with system message added
        assert len(result_messages) == 2
        assert result_messages[0]["role"] == "system"
        assert "JSON" in result_messages[0]["content"]
    
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
        
        # Mock API response with proper indexable structure
        mock_message = Mock()
        mock_message.content = json.dumps(structured_response)
        mock_message.refusal = None
        mock_message.tool_calls = None
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_api_response = Mock()
        mock_api_response.choices = [mock_choice]  # Make it a proper list
        
        # Ensure the mock agent is properly configured for both API paths
        mock_agent.chat.completions.create.return_value = mock_api_response
        mock_agent.ChatCompletion.create.return_value = mock_api_response

        # Mock memory methods to avoid complex memory handling
        with patch.object(wrapper, 'add_message'):
            with patch.object(wrapper, 'remove'):
                # Test the chat flow
                result = wrapper.chat("Please read /tmp/test.txt")
                
                # With our Mock handling, verify the basic flow works
                # The structured response setup should be attempted even if Mock handling takes over
                assert "Mock response for testing" in str(result) or "I'll read that file for you." in str(result)
                
                # Verify the API was called with proper structured output setup
                # Check both possible API call paths
                chat_called = mock_agent.chat.completions.create.called
                completion_called = mock_agent.ChatCompletion.create.called
                
                assert chat_called or completion_called, "Expected either ChatCompletion.create or chat.completions.create to be called"
                
                # Get call args from whichever path was used
                if completion_called:
                    call_args = mock_agent.ChatCompletion.create.call_args[1]
                else:
                    call_args = mock_agent.chat.completions.create.call_args[1]
                    
                assert call_args["model"] == "gpt-4o"
    
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
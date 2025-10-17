"""
Integration tests for LangSwarm examples.

Tests that all examples in examples/simple/ work correctly
and demonstrate the expected functionality.
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
import importlib.util

# Add examples directory to path for imports
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples" / "simple"
sys.path.insert(0, str(EXAMPLES_DIR))


class TestSimpleExamples:
    """Test all simple examples work correctly."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        # Mock API keys for all providers
        self.env_patches = [
            patch.dict(os.environ, {
                'OPENAI_API_KEY': 'test-openai-key',
                'ANTHROPIC_API_KEY': 'test-anthropic-key',
                'GOOGLE_API_KEY': 'test-google-key',
                'COHERE_API_KEY': 'test-cohere-key',
                'MISTRAL_API_KEY': 'test-mistral-key'
            })
        ]
        
        for env_patch in self.env_patches:
            env_patch.start()
    
    def teardown_method(self):
        """Clean up after each test."""
        for env_patch in self.env_patches:
            env_patch.stop()
    
    def load_example_module(self, example_name: str):
        """Load an example as a Python module."""
        example_path = EXAMPLES_DIR / f"{example_name}.py"
        
        if not example_path.exists():
            pytest.skip(f"Example {example_name}.py not found")
        
        spec = importlib.util.spec_from_file_location(example_name, example_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    @pytest.mark.asyncio
    async def test_01_basic_chat(self):
        """Test basic chat example works."""
        module = self.load_example_module("01_basic_chat")
        
        # Mock the OpenAI client
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Python is awesome!"))]
            mock_response.usage = Mock(total_tokens=15)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            # Run the example
            await module.main()
            
            # Verify the API was called
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_02_memory_chat(self):
        """Test memory-enabled chat example."""
        module = self.load_example_module("02_memory_chat")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            # Multiple responses for conversation
            responses = [
                Mock(choices=[Mock(message=Mock(content="Hi Alice!"))], usage=Mock(total_tokens=10)),
                Mock(choices=[Mock(message=Mock(content="Your name is Alice!"))], usage=Mock(total_tokens=12))
            ]
            
            mock_client.chat.completions.create = AsyncMock(side_effect=responses)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            # Should have made 2 API calls
            assert mock_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_03_different_providers(self):
        """Test multiple provider example."""
        module = self.load_example_module("03_different_providers")
        
        # Mock all provider clients
        with patch('openai.AsyncOpenAI') as mock_openai, \
             patch('anthropic.AsyncAnthropic') as mock_anthropic, \
             patch('google.generativeai.GenerativeModel') as mock_google:
            
            # OpenAI mock
            mock_openai_client = Mock()
            mock_openai_client.chat.completions.create = AsyncMock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content="OpenAI response"))],
                    usage=Mock(total_tokens=10)
                )
            )
            mock_openai.return_value = mock_openai_client
            
            # Anthropic mock
            mock_anthropic_client = Mock()
            mock_anthropic_client.messages.create = AsyncMock(
                return_value=Mock(
                    content=[Mock(text="Anthropic response")],
                    usage=Mock(input_tokens=5, output_tokens=5)
                )
            )
            mock_anthropic.return_value = mock_anthropic_client
            
            await module.main()
            
            # Both providers should be called
            mock_openai_client.chat.completions.create.assert_called()
            mock_anthropic_client.messages.create.assert_called()
    
    @pytest.mark.asyncio  
    async def test_04_tools_example(self):
        """Test tools integration example."""
        module = self.load_example_module("04_tools_example")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            # Mock tool calling response
            mock_response = Mock()
            mock_response.choices = [Mock(
                message=Mock(
                    content="I can help with file operations!",
                    tool_calls=[
                        Mock(
                            id="call_123",
                            function=Mock(name="filesystem_read", arguments='{"path": "/test"}')
                        )
                    ]
                )
            )]
            mock_response.usage = Mock(total_tokens=20)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            mock_client.chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_05_streaming(self):
        """Test streaming response example."""
        module = self.load_example_module("05_streaming")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            # Mock streaming response
            async def mock_stream():
                chunks = [
                    Mock(choices=[Mock(delta=Mock(content="Hello"))]),
                    Mock(choices=[Mock(delta=Mock(content=" there"))]),
                    Mock(choices=[Mock(delta=Mock(content="!"))]),
                ]
                for chunk in chunks:
                    yield chunk
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
            mock_openai.return_value = mock_client
            
            await module.main()
            
            mock_client.chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_06_multi_agent(self):
        """Test multi-agent workflow example."""
        module = self.load_example_module("06_multi_agent")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            # Multiple responses for different agents
            responses = [
                Mock(choices=[Mock(message=Mock(content="Analysis complete"))], usage=Mock(total_tokens=15)),
                Mock(choices=[Mock(message=Mock(content="Summary ready"))], usage=Mock(total_tokens=12)),
                Mock(choices=[Mock(message=Mock(content="Review finished"))], usage=Mock(total_tokens=10))
            ]
            
            mock_client.chat.completions.create = AsyncMock(side_effect=responses)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            # Should call multiple agents
            assert mock_client.chat.completions.create.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_07_workflows(self):
        """Test workflow example."""
        module = self.load_example_module("07_workflows")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Workflow step completed"))]
            mock_response.usage = Mock(total_tokens=20)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            mock_client.chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_08_config_loading(self):
        """Test configuration loading example."""
        module = self.load_example_module("08_config_loading")
        
        # Mock the config file
        mock_config = {
            "version": "2.0",
            "agents": [{"id": "assistant", "model": "gpt-3.5-turbo"}]
        }
        
        with patch('langswarm.load_config', return_value=mock_config) as mock_load, \
             patch('openai.AsyncOpenAI') as mock_openai:
            
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Config loaded!"))]
            mock_response.usage = Mock(total_tokens=10)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            mock_load.assert_called()
    
    @pytest.mark.asyncio
    async def test_09_cost_tracking(self):
        """Test cost tracking example."""
        module = self.load_example_module("09_cost_tracking")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Cost tracking enabled"))]
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            mock_client.chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_10_quick_setup(self):
        """Test quick setup example."""
        module = self.load_example_module("10_quick_setup")
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Quick setup works!"))]
            mock_response.usage = Mock(total_tokens=12)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            await module.main()
            
            mock_client.chat.completions.create.assert_called()


class TestExampleStructure:
    """Test the structure and consistency of examples."""
    
    def test_all_examples_exist(self):
        """Test that all expected examples exist."""
        expected_examples = [
            "01_basic_chat.py",
            "02_memory_chat.py", 
            "03_different_providers.py",
            "04_tools_example.py",
            "05_streaming.py",
            "06_multi_agent.py",
            "07_workflows.py",
            "08_config_loading.py",
            "09_cost_tracking.py",
            "10_quick_setup.py"
        ]
        
        for example in expected_examples:
            example_path = EXAMPLES_DIR / example
            assert example_path.exists(), f"Example {example} is missing"
    
    def test_examples_have_main_function(self):
        """Test that all examples have a main() function."""
        for example_file in EXAMPLES_DIR.glob("*.py"):
            if example_file.name.startswith("test_"):
                continue
                
            content = example_file.read_text()
            assert "async def main()" in content or "def main()" in content, \
                f"Example {example_file.name} missing main() function"
    
    def test_examples_are_runnable(self):
        """Test that all examples have the if __name__ == '__main__' pattern."""
        for example_file in EXAMPLES_DIR.glob("*.py"):
            if example_file.name.startswith("test_"):
                continue
                
            content = example_file.read_text()
            assert 'if __name__ == "__main__"' in content, \
                f"Example {example_file.name} missing main execution block"
    
    def test_examples_import_from_langswarm(self):
        """Test that examples import from langswarm package."""
        for example_file in EXAMPLES_DIR.glob("*.py"):
            if example_file.name.startswith("test_"):
                continue
                
            content = example_file.read_text()
            assert "from langswarm" in content or "import langswarm" in content, \
                f"Example {example_file.name} doesn't import from langswarm"
    
    def test_examples_are_short(self):
        """Test that examples are actually short (10-20 lines of actual code)."""
        for example_file in EXAMPLES_DIR.glob("*.py"):
            if example_file.name.startswith("test_"):
                continue
                
            content = example_file.read_text()
            lines = content.split('\n')
            
            # Count non-empty, non-comment lines
            code_lines = [
                line for line in lines 
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""')
            ]
            
            # Filter out import and if __name__ boilerplate
            actual_code_lines = [
                line for line in code_lines
                if not (line.strip().startswith('import ') or 
                       line.strip().startswith('from ') or
                       line.strip() == 'if __name__ == "__main__":' or
                       line.strip() == 'asyncio.run(main())')
            ]
            
            assert len(actual_code_lines) <= 25, \
                f"Example {example_file.name} has {len(actual_code_lines)} lines, should be ≤25"


class TestExampleDependencies:
    """Test that examples handle dependencies correctly."""
    
    def test_examples_handle_missing_api_keys(self):
        """Test examples fail gracefully when API keys are missing."""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            for example_file in EXAMPLES_DIR.glob("0*.py"):
                if example_file.name.startswith("test_"):
                    continue
                
                # Import the module
                spec = importlib.util.spec_from_file_location(
                    example_file.stem, example_file
                )
                module = importlib.util.module_from_spec(spec)
                
                # Should either raise a helpful error or handle gracefully
                try:
                    spec.loader.exec_module(module)
                    # If it doesn't raise, try running main()
                    if hasattr(module, 'main'):
                        if asyncio.iscoroutinefunction(module.main):
                            with pytest.raises(ValueError, match="API key"):
                                asyncio.run(module.main())
                        else:
                            with pytest.raises(ValueError, match="API key"):
                                module.main()
                except (ValueError, ImportError) as e:
                    # Expected - should mention API key or dependency
                    assert "API key" in str(e) or "install" in str(e).lower()
    
    def test_examples_with_optional_dependencies(self):
        """Test examples that use optional dependencies handle missing deps."""
        # This test would be more relevant for examples using specific tools
        # For now, just ensure imports don't crash completely
        
        for example_file in EXAMPLES_DIR.glob("*.py"):
            if example_file.name.startswith("test_"):
                continue
            
            # Should be able to at least import the file
            spec = importlib.util.spec_from_file_location(
                example_file.stem, example_file
            )
            module = importlib.util.module_from_spec(spec)
            
            # This should not crash with ImportError for basic imports
            try:
                spec.loader.exec_module(module)
            except ImportError as e:
                # If it fails, should be due to optional dependencies
                # and should have a helpful error message
                error_msg = str(e).lower()
                optional_deps = ['redis', 'chromadb', 'qdrant', 'elasticsearch']
                assert any(dep in error_msg for dep in optional_deps), \
                    f"Unexpected import error in {example_file.name}: {e}"
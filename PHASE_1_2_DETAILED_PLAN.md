# 📋 LangSwarm Phase 1 & 2 Detailed Implementation Plan

## 🏗️ Phase 1: Foundation (Week 1)
**Goal**: Ensure reliability and quality of current improvements

### Day 1-2: Testing Infrastructure

#### **Task 1.1: Create Test Structure**
```bash
# Create directory structure
mkdir -p tests/{unit,integration,e2e,fixtures}
touch tests/__init__.py
touch tests/conftest.py  # pytest configuration
```

#### **Task 1.2: Unit Tests for Simple API**
Create `tests/unit/test_simple_api.py`:
```python
import pytest
from langswarm import create_agent, Agent

class TestSimpleAPI:
    def test_create_agent_basic(self):
        """Test basic agent creation"""
        agent = create_agent(model="gpt-3.5-turbo")
        assert isinstance(agent, Agent)
        assert agent.model == "gpt-3.5-turbo"
        assert agent.provider == "openai"
    
    def test_create_agent_with_memory(self):
        """Test agent with memory enabled"""
        agent = create_agent(model="gpt-4", memory=True)
        assert agent.memory_enabled == True
    
    def test_provider_auto_detection(self):
        """Test provider detection from model names"""
        test_cases = [
            ("gpt-3.5-turbo", "openai"),
            ("claude-3-sonnet", "anthropic"),
            ("gemini-pro", "google"),
            ("command", "cohere"),
            ("mistral-tiny", "mistral"),
        ]
        for model, expected_provider in test_cases:
            agent = create_agent(model=model)
            assert agent.provider == expected_provider
    
    def test_system_prompt(self):
        """Test custom system prompt"""
        prompt = "You are a pirate"
        agent = create_agent(model="gpt-3.5-turbo", system_prompt=prompt)
        assert agent.system_prompt == prompt
```

#### **Task 1.3: Integration Tests for Examples**
Create `tests/integration/test_examples.py`:
```python
import os
import subprocess
import pytest
from pathlib import Path

class TestExamples:
    @pytest.fixture
    def examples_dir(self):
        return Path("examples/simple")
    
    def test_all_examples_have_valid_syntax(self, examples_dir):
        """Verify all examples have valid Python syntax"""
        for example in examples_dir.glob("*.py"):
            if example.name == "test_all_examples.py":
                continue
            result = subprocess.run(
                ["python", "-m", "py_compile", str(example)],
                capture_output=True
            )
            assert result.returncode == 0, f"Syntax error in {example.name}"
    
    def test_examples_import_langswarm(self, examples_dir):
        """Verify all examples import from langswarm"""
        for example in examples_dir.glob("*.py"):
            if example.name.startswith("test_"):
                continue
            content = example.read_text()
            assert "from langswarm import" in content or "import langswarm" in content
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), 
                        reason="Requires OPENAI_API_KEY")
    def test_basic_chat_example_runs(self, examples_dir):
        """Test that basic chat example actually runs"""
        # Create a modified version that exits after one interaction
        # Test it runs without errors
```

#### **Task 1.4: Smart Defaults Testing**
Create `tests/unit/test_smart_defaults.py`:
```python
from langswarm.core.config.smart_defaults import SmartDefaults

class TestSmartDefaults:
    def test_minimal_config_expansion(self):
        """Test minimal config gets proper defaults"""
        minimal = {
            "version": "2.0",
            "agents": [{
                "id": "assistant",
                "model": "gpt-3.5-turbo"
            }]
        }
        
        expanded = SmartDefaults.apply_defaults(minimal)
        
        # Check agent defaults applied
        agent = expanded["agents"][0]
        assert agent["provider"] == "openai"
        assert agent["temperature"] == 0.7
        assert "system_prompt" in agent
        
        # Check memory defaults added
        assert "memory" in expanded
        assert expanded["memory"]["backend"] == "sqlite"
```

### Day 3-4: CI/CD Pipeline

#### **Task 1.5: GitHub Actions Setup**
Create `.github/workflows/test.yml`:
```yaml
name: Test Suite
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: |
        pytest tests/unit -v
        pytest tests/integration -v
    
    - name: Test examples structure
      run: |
        cd examples/simple
        python test_all_examples.py
    
    - name: Check imports work
      run: |
        python -c "from langswarm import create_agent; print('✅ Import successful')"
```

#### **Task 1.6: Documentation Tests**
Create `.github/workflows/docs.yml`:
```yaml
name: Documentation Tests
on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Test documentation links
      run: |
        pip install markdown-link-check
        find docs -name "*.md" -exec markdown-link-check {} \;
    
    - name: Test code blocks in docs
      run: |
        # Extract and test Python code blocks from markdown
        python scripts/test_doc_code_blocks.py
```

### Day 5: Type Hints & API Documentation

#### **Task 1.7: Add Type Hints**
Update `langswarm/simple_api.py`:
```python
from typing import Dict, List, Optional, Any, AsyncGenerator, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

class Agent:
    """Simple agent wrapper for LangSwarm.
    
    Args:
        model: AI model name (e.g., "gpt-3.5-turbo")
        provider: AI provider (auto-detected if not specified)
        system_prompt: System instructions for the agent
        memory: Enable conversation memory
        tools: List of tool names to enable
        stream: Enable streaming responses
        track_costs: Track token usage and costs
        **kwargs: Additional provider-specific options
    
    Example:
        >>> agent = Agent(model="gpt-3.5-turbo", memory=True)
        >>> response = await agent.chat("Hello!")
        >>> print(response)
    """
    
    def __init__(
        self,
        model: str,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        memory: bool = False,
        tools: Optional[List[str]] = None,
        stream: bool = False,
        track_costs: bool = False,
        **kwargs: Any
    ) -> None:
        # ... implementation
    
    async def chat(self, message: str) -> str:
        """Send a message and get a response.
        
        Args:
            message: User message to send
            
        Returns:
            Agent's response as a string
            
        Raises:
            ValueError: If API key not set
            ImportError: If required provider not installed
        """
        # ... implementation
```

#### **Task 1.8: Generate API Documentation**
Create `scripts/generate_api_docs.py`:
```python
"""Generate API documentation from type hints and docstrings"""
import inspect
import langswarm

def generate_api_reference():
    # Extract all public functions/classes
    # Generate markdown documentation
    # Save to docs/api-reference/
```

### Day 6-7: Error Handling Coverage

#### **Task 1.9: Comprehensive Error Messages**
Create `langswarm/core/errors/user_friendly.py`:
```python
class RateLimitError(Exception):
    """Rate limit exceeded error with helpful guidance"""
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        message = f"❌ Rate limit exceeded for {provider}"
        
        suggestions = []
        if retry_after:
            suggestions.append(f"Wait {retry_after} seconds before retrying")
        
        suggestions.extend([
            "Use a different API key",
            "Upgrade your plan for higher limits",
            "Add delays between requests",
            "Use a cheaper model (e.g., gpt-3.5-turbo)"
        ])
        
        super().__init__(self._format_error(message, suggestions))

class ContextLengthError(Exception):
    """Context window exceeded with solutions"""
    def __init__(self, tokens: int, limit: int, model: str):
        message = f"❌ Context length exceeded: {tokens} tokens > {limit} limit"
        
        suggestions = [
            f"Use a model with larger context (e.g., {model}-16k)",
            "Start a new conversation to reset context",
            "Summarize the conversation and continue",
            "Use memory backend that supports automatic truncation"
        ]
        
        super().__init__(self._format_error(message, suggestions))
```

#### **Task 1.10: Error Testing**
Create `tests/unit/test_error_messages.py`:
```python
def test_rate_limit_error_message():
    """Test rate limit error provides helpful guidance"""
    error = RateLimitError("openai", retry_after=60)
    assert "Rate limit exceeded" in str(error)
    assert "Wait 60 seconds" in str(error)
    assert "gpt-3.5-turbo" in str(error)
```

---

## 🎨 Phase 2: Polish (Week 2-3)
**Goal**: Enhance developer experience and add productivity tools

### Week 2: Developer Experience

#### **Task 2.1: Debug Mode Implementation**
Update `langswarm/simple_api.py`:
```python
class Agent:
    def __init__(self, ..., debug: bool = False):
        self.debug = debug
        if debug:
            self._setup_debugging()
    
    def _setup_debugging(self):
        """Enable debug logging and tracing"""
        import logging
        logging.basicConfig(level=logging.DEBUG)
        self._debug_logger = logging.getLogger("langswarm.debug")
    
    async def chat(self, message: str) -> str:
        if self.debug:
            self._debug_logger.info(f"📤 User: {message}")
            start_time = time.time()
        
        response = await self._chat_internal(message)
        
        if self.debug:
            elapsed = time.time() - start_time
            self._debug_logger.info(f"📥 Agent: {response[:100]}...")
            self._debug_logger.info(f"⏱️ Response time: {elapsed:.2f}s")
            self._debug_logger.info(f"💰 Tokens used: {self._last_token_count}")
        
        return response
```

#### **Task 2.2: Interactive Examples (Jupyter)**
Create notebook examples:
```bash
mkdir -p examples/notebooks
```

Create `examples/notebooks/01_quick_start_tutorial.ipynb`:
```python
# Cell 1: Installation check
!pip show langswarm || pip install langswarm openai

# Cell 2: Import and setup
from langswarm import create_agent
import os

# Set your API key
os.environ["OPENAI_API_KEY"] = "sk-..."  # Replace with your key

# Cell 3: Create agent
agent = create_agent(model="gpt-3.5-turbo", memory=True)
print("✅ Agent created!")

# Cell 4: Interactive chat
response = await agent.chat("Hello! What can you help me with?")
print(f"Agent: {response}")

# Cell 5: Test memory
response = await agent.chat("What did I just ask you?")
print(f"Agent: {response}")
```

#### **Task 2.3: CLI Validation Tool**
Create `langswarm/cli/validate.py`:
```python
import click
import yaml
from pathlib import Path
from langswarm.core.config import load_config
from langswarm.core.config.smart_defaults import SmartDefaults

@click.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation')
def validate_config(config_file: str, verbose: bool):
    """Validate a LangSwarm configuration file"""
    
    click.echo(f"🔍 Validating {config_file}...")
    
    try:
        # Load and validate
        config = load_config(config_file)
        
        # Check for common issues
        warnings = []
        
        # Check API keys
        for agent in config.get("agents", []):
            provider = agent.get("provider", "openai")
            env_var = f"{provider.upper()}_API_KEY"
            if not os.getenv(env_var):
                warnings.append(f"Missing {env_var} for agent '{agent['id']}'")
        
        # Check deprecated options
        if "version" in config and config["version"] == "1.0":
            warnings.append("Using old version 1.0, consider upgrading to 2.0")
        
        if warnings:
            click.echo("⚠️  Warnings:")
            for warning in warnings:
                click.echo(f"   - {warning}")
        else:
            click.echo("✅ Configuration is valid!")
        
        if verbose:
            click.echo("\n📊 Configuration summary:")
            click.echo(f"   Agents: {len(config.get('agents', []))}")
            click.echo(f"   Workflows: {len(config.get('workflows', []))}")
            click.echo(f"   Tools: {len(config.get('tools', {}))}")
            
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    validate_config()
```

#### **Task 2.4: Cost Estimation Tool**
Create `langswarm/cli/estimate.py`:
```python
@click.command()
@click.option('--model', '-m', default='gpt-3.5-turbo', help='Model to estimate')
@click.option('--messages', '-n', default=100, type=int, help='Number of messages')
@click.option('--avg-length', '-l', default=50, type=int, help='Average message length')
def estimate_costs(model: str, messages: int, avg_length: int):
    """Estimate costs for a conversation"""
    
    # Token estimates
    tokens_per_message = avg_length * 1.3  # Rough estimate
    total_tokens = messages * tokens_per_message * 2  # Input + output
    
    # Pricing (as of 2024)
    pricing = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},  # per 1k tokens
        "gpt-4": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    }
    
    if model not in pricing:
        click.echo(f"❌ Unknown model: {model}")
        return
    
    cost_per_1k = (pricing[model]["input"] + pricing[model]["output"]) / 2
    estimated_cost = (total_tokens / 1000) * cost_per_1k
    
    click.echo(f"💰 Cost Estimation for {model}")
    click.echo(f"   Messages: {messages}")
    click.echo(f"   Avg length: {avg_length} words")
    click.echo(f"   Estimated tokens: {total_tokens:,.0f}")
    click.echo(f"   Estimated cost: ${estimated_cost:.2f}")
    click.echo(f"\n💡 Tips to reduce costs:")
    click.echo(f"   - Use gpt-3.5-turbo instead of gpt-4 (80% cheaper)")
    click.echo(f"   - Enable caching for repeated questions")
    click.echo(f"   - Use shorter system prompts")
```

### Week 3: Advanced Developer Tools

#### **Task 2.5: Development Server with Hot Reload**
Create `langswarm/cli/dev.py`:
```python
import click
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time

class ConfigReloadHandler(FileSystemEventHandler):
    def __init__(self, config_file: str, command: str):
        self.config_file = config_file
        self.command = command
        self.process = None
        self.restart()
    
    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            click.echo(f"🔄 Config changed, reloading...")
            self.restart()
    
    def restart(self):
        if self.process:
            self.process.terminate()
        self.process = subprocess.Popen(self.command, shell=True)

@click.command()
@click.argument('config_file')
@click.option('--command', '-c', default='python app.py', help='Command to run')
def dev_server(config_file: str, command: str):
    """Run development server with hot reload"""
    click.echo(f"👁️ Watching {config_file} for changes...")
    
    handler = ConfigReloadHandler(config_file, command)
    observer = Observer()
    observer.schedule(handler, path='.', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

#### **Task 2.6: Testing Helpers**
Create `langswarm/testing/helpers.py`:
```python
"""Testing utilities for LangSwarm applications"""

class MockAgent:
    """Mock agent for testing without API calls"""
    def __init__(self, responses: List[str]):
        self.responses = iter(responses)
        self.history = []
    
    async def chat(self, message: str) -> str:
        self.history.append(message)
        return next(self.responses, "No more responses")

def mock_agent_fixture(responses: List[str]):
    """Pytest fixture for mock agents"""
    return MockAgent(responses)

# Usage in tests:
# agent = mock_agent_fixture(["Hello!", "I'm a bot"])
# response = await agent.chat("Hi")
# assert response == "Hello!"
```

#### **Task 2.7: Performance Profiling**
Add profiling support:
```python
class Agent:
    def __init__(self, ..., profile: bool = False):
        self.profile = profile
        self._profile_data = []
    
    @contextmanager
    def _profile_section(self, name: str):
        if not self.profile:
            yield
            return
            
        start = time.perf_counter()
        yield
        elapsed = time.perf_counter() - start
        self._profile_data.append({
            "section": name,
            "elapsed": elapsed,
            "timestamp": time.time()
        })
    
    async def chat(self, message: str) -> str:
        with self._profile_section("total"):
            with self._profile_section("prepare"):
                # Message preparation
                
            with self._profile_section("api_call"):
                # API call
                
            with self._profile_section("process_response"):
                # Response processing
        
        return response
    
    def get_profile_report(self) -> Dict[str, Any]:
        """Get performance profiling report"""
        return {
            "sections": self._profile_data,
            "total_time": sum(s["elapsed"] for s in self._profile_data),
            "api_time": sum(s["elapsed"] for s in self._profile_data 
                          if s["section"] == "api_call")
        }
```

#### **Task 2.8: Documentation Videos/Scripts**
Create scripts for video tutorials:

`docs/video_scripts/01_two_minute_quickstart.md`:
```markdown
# 2-Minute Quick Start Video Script

## Scene 1: Installation (0:00-0:30)
```
[Terminal]
$ pip install langswarm openai
[Progress bar...]
✅ Installation complete!

$ export OPENAI_API_KEY='sk-...'
```

## Scene 2: First Agent (0:30-1:00)
```
[VS Code]
# chatbot.py
from langswarm import create_agent
import asyncio

async def main():
    agent = create_agent(model="gpt-3.5-turbo", memory=True)
    response = await agent.chat("Hello!")
    print(response)

asyncio.run(main())
```

## Scene 3: Run It (1:00-1:30)
```
[Terminal]
$ python chatbot.py
AI: Hello! How can I help you today?
```

## Scene 4: Success! (1:30-2:00)
"You just built an AI agent in under 2 minutes! 
Visit docs.langswarm.ai for more examples."
```

---

## 📊 Success Criteria

### Phase 1 Success Metrics:
- ✅ 100% of examples pass automated tests
- ✅ Zero import warnings on startup
- ✅ CI/CD pipeline catches all issues
- ✅ All public APIs have type hints
- ✅ Error messages cover 90% of common issues

### Phase 2 Success Metrics:
- ✅ Debug mode helps identify issues quickly
- ✅ CLI tools reduce setup time by 50%
- ✅ Jupyter notebooks work out-of-the-box
- ✅ Development server saves 10+ minutes per session
- ✅ Cost estimation accurate within 20%

## 📅 Timeline

### Phase 1: Foundation (Week 1)
- **Mon-Tue**: Testing infrastructure
- **Wed-Thu**: CI/CD pipeline  
- **Fri**: Type hints & documentation
- **Weekend**: Error handling coverage

### Phase 2: Polish (Week 2-3)
- **Week 2**: Core developer tools (debug, CLI, notebooks)
- **Week 3**: Advanced tools (hot reload, profiling, videos)

## 🚀 Deliverables

### Phase 1 Deliverables:
1. Comprehensive test suite with >80% coverage
2. GitHub Actions CI/CD pipeline
3. Fully typed public API
4. Enhanced error messages for common issues

### Phase 2 Deliverables:
1. Debug mode for development
2. CLI tools suite (validate, estimate, dev)
3. Interactive Jupyter examples
4. Performance profiling tools
5. Video tutorial scripts

This plan provides concrete, implementable tasks that will significantly improve LangSwarm's reliability and developer experience.
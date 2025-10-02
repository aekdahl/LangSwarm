# 🧪 LangSwarm Testing Strategy

## 🎯 **Overview**
This document provides specific testing guidance for each sub-task in `todo.md` to ensure safe implementation without breaking existing functionality.

## 📋 **General Testing Principles**

### **1. Test-Driven Development**
- Write tests BEFORE implementing features
- Use existing test structure as reference
- Ensure 100% backward compatibility

### **2. Testing Layers**
```
Unit Tests → Integration Tests → Regression Tests → End-to-End Tests
```

### **3. Safety Checks**
- All existing tests must continue passing
- No configuration breaking changes
- Graceful fallbacks for unsupported features

---

## 🔥 **Phase 1: LLM Abstractions Testing**

### **PRIORITY 1: Native Structured Responses**

#### **Sub-task: Implement `response_format={"type": "json_object"}`**
**Test Strategy:**
```python
# tests/core/wrappers/test_native_structured_responses.py

def test_openai_structured_response_format():
    """Test OpenAI models use native structured responses"""
    # Test with OpenAI model that supports structured responses
    agent = create_test_agent(model="gpt-4o", use_native_structured=True)
    response = agent.chat("Hello", response_format={"type": "json_object"})
    
    # Verify response is valid JSON
    assert isinstance(response, dict)
    assert "response" in response
    
def test_fallback_to_manual_parsing():
    """Test fallback for models without native support"""
    # Test with older model or non-OpenAI model
    agent = create_test_agent(model="gpt-3.5-turbo-instruct")
    response = agent.chat("Hello")
    
    # Should still work with manual parsing
    assert response is not None
    
def test_backward_compatibility_structured_responses():
    """Ensure existing JSON parsing still works"""
    # Load existing example configurations
    for config_file in ["example_mcp_config/agents.yaml"]:
        loader = LangSwarmConfigLoader(config_file)
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        # Test that all agents still work
        for agent_id, agent in agents.items():
            response = agent.chat("Test message")
            assert response is not None
```

#### **Sub-task: Replace manual JSON parsing in `generic.py:chat()`**
**Test Strategy:**
```python
def test_json_parsing_replacement():
    """Test new parsing works with existing configs"""
    # Test with current JSON format
    old_response = '{"response": "Hello", "mcp": {"tool": "filesystem", "method": "read_file"}}'
    
    # Test with native structured response
    new_response = {"response": "Hello", "mcp": {"tool": "filesystem", "method": "read_file"}}
    
    # Both should produce same result
    assert parse_response(old_response) == parse_response(new_response)

def test_malformed_json_handling():
    """Test graceful handling of malformed JSON"""
    malformed_responses = [
        '{"response": "Hello", "mcp":',  # Incomplete
        '{"response": "Hello" "mcp": {}}',  # Missing comma
        'plain text response',  # No JSON
    ]
    
    for response in malformed_responses:
        # Should not crash, should handle gracefully
        result = agent.chat(response)
        assert result is not None
```

#### **Sub-task: Add schema validation for structured responses**
**Test Strategy:**
```python
def test_response_schema_validation():
    """Test structured response schema validation"""
    valid_schema = {
        "type": "object",
        "properties": {
            "response": {"type": "string"},
            "mcp": {"type": "object"}
        },
        "required": ["response"]
    }
    
    # Test valid response
    valid_response = {"response": "Hello", "mcp": {"tool": "filesystem"}}
    assert validate_response_schema(valid_response, valid_schema) == True
    
    # Test invalid response
    invalid_response = {"mcp": {"tool": "filesystem"}}  # Missing required "response"
    assert validate_response_schema(invalid_response, valid_schema) == False
```

### **PRIORITY 2: Native Tool/Function Calling**

#### **Sub-task: Implement OpenAI function calling API**
**Test Strategy:**
```python
def test_openai_function_calling():
    """Test native OpenAI function calling"""
    tools = [{
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    }]
    
    agent = create_test_agent(model="gpt-4o", tools=tools)
    response = agent.chat("Read /tmp/test.txt")
    
    # Should detect tool call
    assert response.get("tool_calls") is not None
    
def test_mcp_format_translation():
    """Test translation from native function calls to MCP format"""
    # Native function call format
    native_call = {
        "tool_calls": [{
            "function": {"name": "read_file", "arguments": {"path": "/tmp/test.txt"}}
        }]
    }
    
    # Expected MCP format
    expected_mcp = {
        "mcp": {"tool": "filesystem", "method": "read_file", "params": {"path": "/tmp/test.txt"}}
    }
    
    result = translate_to_mcp_format(native_call)
    assert result == expected_mcp
```

#### **Sub-task: Maintain backward compatibility with existing MCP tools**
**Test Strategy:**
```python
def test_mcp_backward_compatibility():
    """Ensure existing MCP tools continue working"""
    # Test all existing MCP configurations
    test_configs = [
        "example_mcp_config/agents.yaml",
        "langswarm/mcp/tools/filesystem/agents.yaml",
        "langswarm/mcp/tools/mcpgithubtool/agents.yaml"
    ]
    
    for config_path in test_configs:
        if os.path.exists(config_path):
            loader = LangSwarmConfigLoader(config_path)
            workflows, agents, brokers, tools, tools_metadata = loader.load()
            
            # Test that tools still work with old format
            for tool in tools:
                assert tool.id is not None
                assert hasattr(tool, 'type')
```

---

## 🎯 **Phase 2: Simplification Testing**

### **1. Single Configuration File**

#### **Sub-task: Define `langswarm.yaml` schema**
**Test Strategy:**
```python
def test_unified_config_schema():
    """Test unified configuration schema validation"""
    valid_config = {
        "name": "my-assistant",
        "agent": {"model": "gpt-4o-mini", "tools": ["filesystem"]},
        "tools": [{"id": "filesystem", "type": "mcpfilesystem"}]
    }
    
    # Test schema validation
    assert validate_unified_schema(valid_config) == True
    
    # Test with include directive
    config_with_includes = {
        "name": "my-assistant",
        "include": ["tools.yaml", "workflows.yaml"],
        "agent": {"model": "gpt-4o-mini"}
    }
    
    assert validate_unified_schema(config_with_includes) == True

def test_multi_file_vs_single_file():
    """Test that single-file produces same result as multi-file"""
    # Load from 8 separate files
    multi_file_loader = LangSwarmConfigLoader("example_mcp_config/")
    multi_workflows, multi_agents, multi_brokers, multi_tools, multi_metadata = multi_file_loader.load()
    
    # Create equivalent single file and load
    create_equivalent_single_file("test_langswarm.yaml", multi_workflows, multi_agents, multi_tools)
    single_file_loader = LangSwarmConfigLoader()
    single_workflows, single_agents, single_brokers, single_tools, single_metadata = single_file_loader.load_single_config("test_langswarm.yaml")
    
    # Results should be equivalent
    assert len(multi_agents) == len(single_agents)
    assert len(multi_tools) == len(single_tools)
```

#### **Sub-task: Add `load_single_config()` method**
**Test Strategy:**
```python
def test_load_single_config_method():
    """Test new load_single_config method"""
    config_content = """
    name: test-assistant
    agent:
      model: gpt-4o-mini
      tools: [filesystem]
    """
    
    with open("test_config.yaml", "w") as f:
        f.write(config_content)
    
    loader = LangSwarmConfigLoader()
    workflows, agents, brokers, tools, tools_metadata = loader.load_single_config("test_config.yaml")
    
    assert len(agents) > 0
    assert "test-assistant" in str(agents) or len(agents) == 1  # Depending on implementation

def test_auto_detect_config_type():
    """Test auto-detection of single vs multi-file"""
    # Test directory with multiple files
    multi_file_path = "example_mcp_config/"
    loader1 = LangSwarmConfigLoader(multi_file_path)
    
    # Test single file
    single_file_path = "test_langswarm.yaml"
    loader2 = LangSwarmConfigLoader()
    
    # Both should work without specifying method
    result1 = loader1.load()
    result2 = loader2.load_single_config(single_file_path)
    
    assert result1 is not None
    assert result2 is not None
```

#### **Sub-task: Create config migration tool**
**Test Strategy:**
```python
def test_config_migration_tool():
    """Test migration from 8 files to 1 file"""
    # Create test migration
    source_dir = "example_mcp_config/"
    target_file = "migrated_config.yaml"
    
    # Run migration
    migration_tool = ConfigMigrationTool()
    success = migration_tool.migrate(source_dir, target_file)
    
    assert success == True
    assert os.path.exists(target_file)
    
    # Test that migrated config works
    loader = LangSwarmConfigLoader()
    workflows, agents, brokers, tools, tools_metadata = loader.load_single_config(target_file)
    
    # Should have same functionality as original
    assert len(agents) > 0
    assert len(tools) > 0

def test_migration_preserves_functionality():
    """Test that migrated config produces same results"""
    # Test with original config
    original_loader = LangSwarmConfigLoader("example_mcp_config/")
    orig_workflows, orig_agents, orig_brokers, orig_tools, orig_metadata = original_loader.load()
    
    # Migrate and test with new config
    ConfigMigrationTool().migrate("example_mcp_config/", "migrated.yaml")
    migrated_loader = LangSwarmConfigLoader()
    migr_workflows, migr_agents, migr_brokers, migr_tools, migr_metadata = migrated_loader.load_single_config("migrated.yaml")
    
    # Compare key functionality
    assert len(orig_agents) == len(migr_agents)
    assert len(orig_tools) == len(migr_tools)
    
    # Test actual agent responses are same
    if orig_agents and migr_agents:
        orig_agent = list(orig_agents.values())[0]
        migr_agent = list(migr_agents.values())[0]
        
        test_message = "Hello"
        orig_response = orig_agent.chat(test_message)
        migr_response = migr_agent.chat(test_message)
        
        # Responses should be functionally equivalent
        assert type(orig_response) == type(migr_response)
```

### **2. Zero-Config Agents**

#### **Sub-task: Create `generate_system_prompt()` function**
**Test Strategy:**
```python
def test_generate_system_prompt():
    """Test system prompt generation from behavior"""
    config = AgentConfig(
        model="gpt-4o-mini",
        behavior="helpful assistant",
        tools=["filesystem", "calculator"]
    )
    
    prompt = generate_system_prompt(config)
    
    # Should include behavior
    assert "helpful assistant" in prompt
    
    # Should include tool descriptions
    assert "filesystem" in prompt
    assert "calculator" in prompt
    
    # Should include JSON format instructions
    assert "JSON format" in prompt or "json" in prompt.lower()

def test_behavior_presets():
    """Test different behavior presets"""
    presets = ["helpful", "coding", "research", "creative"]
    
    for preset in presets:
        config = AgentConfig(model="gpt-4o-mini", behavior=preset)
        prompt = generate_system_prompt(config)
        
        assert preset in prompt
        assert len(prompt) > 50  # Should be substantial
        
def test_generated_vs_manual_prompts():
    """Test generated prompts work as well as manual ones"""
    # Agent with manual system prompt
    manual_agent = AgentWrapper(
        name="manual",
        agent=create_test_agent(),
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant. Respond in JSON format..."
    )
    
    # Agent with generated prompt
    config = AgentConfig(model="gpt-4o-mini", behavior="helpful assistant")
    auto_prompt = generate_system_prompt(config)
    auto_agent = AgentWrapper(
        name="auto",
        agent=create_test_agent(),
        model="gpt-4o-mini",
        system_prompt=auto_prompt
    )
    
    # Both should work similarly
    test_message = "Hello, how are you?"
    manual_response = manual_agent.chat(test_message)
    auto_response = auto_agent.chat(test_message)
    
    assert manual_response is not None
    assert auto_response is not None
```

#### **Sub-task: Support `behavior:` instead of `system_prompt:`**
**Test Strategy:**
```python
def test_behavior_vs_system_prompt():
    """Test behavior configuration vs manual system prompt"""
    # Test behavior configuration
    behavior_config = {
        "agents": [{
            "id": "behavior_agent",
            "model": "gpt-4o-mini",
            "behavior": "helpful assistant",
            "tools": ["filesystem"]
        }]
    }
    
    # Test manual system prompt (should still work)
    manual_config = {
        "agents": [{
            "id": "manual_agent", 
            "model": "gpt-4o-mini",
            "system_prompt": "You are a helpful assistant...",
            "tools": ["filesystem"]
        }]
    }
    
    # Both should load successfully
    behavior_agent = load_agent_from_config(behavior_config["agents"][0])
    manual_agent = load_agent_from_config(manual_config["agents"][0])
    
    assert behavior_agent is not None
    assert manual_agent is not None
    
    # Both should respond to messages
    test_message = "Help me with a file"
    behavior_response = behavior_agent.chat(test_message)
    manual_response = manual_agent.chat(test_message)
    
    assert behavior_response is not None
    assert manual_response is not None
```

### **3. Smart Tool Auto-Discovery**

#### **Sub-task: Auto-detect environment variables**
**Test Strategy:**
```python
def test_github_token_detection():
    """Test GitHub tool auto-configuration when GITHUB_TOKEN exists"""
    # Mock environment variable
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
        tools = auto_discover_tools(["github"])
        
        github_tool = next((t for t in tools if t.id == "github"), None)
        assert github_tool is not None
        assert github_tool.type == "mcpgithubtool"
        
    # Test without token
    with patch.dict(os.environ, {}, clear=True):
        tools = auto_discover_tools(["github"])
        # Should either skip or provide warning
        if tools:
            github_tool = next((t for t in tools if t.id == "github"), None)
            # Should handle gracefully

def test_cloud_credentials_detection():
    """Test cloud tool auto-configuration"""
    # Mock AWS credentials
    aws_env = {
        'AWS_ACCESS_KEY_ID': 'fake_key',
        'AWS_SECRET_ACCESS_KEY': 'fake_secret'
    }
    
    with patch.dict(os.environ, aws_env):
        tools = auto_discover_tools(["aws"])
        
        if tools:  # If AWS tool is implemented
            aws_tool = next((t for t in tools if "aws" in t.id.lower()), None)
            assert aws_tool is not None

def test_custom_tool_scanning():
    """Test scanning for custom tool files"""
    # Create temporary custom tool file
    os.makedirs("test_tools", exist_ok=True)
    with open("test_tools/my_custom_tool.py", "w") as f:
        f.write("""
class MyCustomTool:
    def __init__(self):
        self.id = "my_custom_tool"
        self.type = "custom"
    
    def run(self, params):
        return "Custom tool response"
""")
    
    # Test custom tool discovery
    tools = auto_discover_tools(["./test_tools/my_custom_tool.py"])
    
    custom_tool = next((t for t in tools if "custom" in str(t)), None)
    # Should find and load custom tool
    
    # Cleanup
    import shutil
    shutil.rmtree("test_tools")
```

#### **Sub-task: Support `tools: [filesystem, github]` syntax**
**Test Strategy:**
```python
def test_simplified_tool_syntax():
    """Test simplified tool configuration syntax"""
    # Simple syntax
    simple_config = {"tools": ["filesystem", "github"]}
    
    # Complex syntax (should still work)
    complex_config = {
        "tools": [{
            "id": "filesystem",
            "type": "mcpfilesystem", 
            "description": "Local filesystem operations",
            "local_mode": True
        }]
    }
    
    # Both should produce working tools
    simple_tools = load_tools_from_config(simple_config)
    complex_tools = load_tools_from_config(complex_config)
    
    assert len(simple_tools) > 0
    assert len(complex_tools) > 0
    
    # Simple tools should have auto-configured defaults
    fs_tool = next((t for t in simple_tools if t.id == "filesystem"), None)
    assert fs_tool is not None
    assert hasattr(fs_tool, 'local_mode')  # Should be auto-configured
```

---

## 🧪 **Regression Testing Strategy**

### **1. Core Functionality Tests**
```bash
# Run existing test suite
pytest tests/ -v

# Test specific integration scenarios
pytest tests/integration/ -v

# Test with real configurations
python example_mcp_config/test_filesystem_example.py
```

### **2. Configuration Compatibility Tests**
```python
def test_all_existing_configs():
    """Test that all existing example configs still work"""
    config_paths = [
        "example_mcp_config/",
        "langswarm/mcp/tools/filesystem/",
        "langswarm/mcp/tools/mcpgithubtool/"
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                loader = LangSwarmConfigLoader(config_path)
                workflows, agents, brokers, tools, tools_metadata = loader.load()
                
                # Basic functionality check
                assert len(tools) >= 0  # May be 0 for some configs
                
                # If agents exist, test basic chat
                if agents:
                    agent = list(agents.values())[0]
                    response = agent.chat("Hello")
                    assert response is not None
                    
            except Exception as e:
                pytest.fail(f"Config {config_path} failed to load: {e}")
```

### **3. Performance Regression Tests**
```python
def test_performance_regression():
    """Ensure new features don't significantly impact performance"""
    import time
    
    # Test configuration loading time
    start_time = time.time()
    loader = LangSwarmConfigLoader("example_mcp_config/")
    workflows, agents, brokers, tools, tools_metadata = loader.load()
    load_time = time.time() - start_time
    
    # Should load reasonably quickly
    assert load_time < 5.0  # 5 seconds max
    
    # Test agent response time
    if agents:
        agent = list(agents.values())[0]
        start_time = time.time()
        response = agent.chat("Hello")
        response_time = time.time() - start_time
        
        # Should respond reasonably quickly
        assert response_time < 30.0  # 30 seconds max
```

---

## 🚀 **Continuous Integration Tests**

### **CI Pipeline Additions**
```yaml
# .github/workflows/test-todo-features.yml
name: Test TODO Features

on: [push, pull_request]

jobs:
  test-llm-abstractions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Test Native Structured Responses
        run: pytest tests/core/wrappers/test_native_structured_responses.py -v
        
      - name: Test Native Tool Calling
        run: pytest tests/core/wrappers/test_native_tool_calling.py -v
        
      - name: Test Backward Compatibility
        run: pytest tests/compatibility/ -v
        
  test-simplification:
    runs-on: ubuntu-latest
    needs: test-llm-abstractions
    steps:
      - name: Test Single Config File
        run: pytest tests/core/config/test_single_config.py -v
        
      - name: Test Zero Config Agents
        run: pytest tests/core/agents/test_zero_config.py -v
        
      - name: Test Tool Auto-Discovery
        run: pytest tests/core/tools/test_auto_discovery.py -v
```

---

## 📊 **Test Coverage Requirements**

### **Minimum Coverage Targets**
- **Unit Tests**: 90% coverage for new code
- **Integration Tests**: All major user workflows
- **Regression Tests**: All existing functionality
- **Performance Tests**: No degradation > 20%

### **Test Reporting**
```bash
# Generate coverage report
pytest --cov=langswarm --cov-report=html

# Generate performance report
python scripts/performance_benchmark.py

# Generate compatibility report
python scripts/compatibility_check.py
```

---

## ✅ **Safety Checklist for Each Sub-task**

Before marking any sub-task as complete, verify:

1. **✅ All existing tests pass** 
2. **✅ New feature has comprehensive tests**
3. **✅ Backward compatibility maintained**
4. **✅ Performance regression < 20%**
5. **✅ Documentation updated**
6. **✅ Example configurations still work**
7. **✅ Error handling graceful**
8. **✅ Fallback mechanisms work**

This testing strategy ensures we can safely implement all TODO items while maintaining the stability and reliability that existing LangSwarm users depend on! 🧪✨ 
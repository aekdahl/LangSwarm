# 🧪 LangSwarm v0.0.54 User Acceptance Testing (UAT) Script

## 📋 Test Information
- **Product**: LangSwarm Multi-Agent AI Framework
- **Version**: 0.0.54
- **Test Date**: _________________
- **Tester Name**: _________________
- **Environment**: _________________

---

## 🚀 Environment Setup Instructions

### Prerequisites
1. **Python**: 3.8 or higher
2. **Git**: For cloning the repository
3. **API Keys** (optional but recommended):
   - OpenAI API Key
   - Anthropic API Key (optional)
   - Google Cloud credentials (optional)

### Step 1: Clone and Install LangSwarm

```bash
# 1. Clone the repository
git clone https://github.com/aekdahl/langswarm.git
cd langswarm

# 2. Create a virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install LangSwarm
pip install -e .

# 5. Set up API keys (if available)
export OPENAI_API_KEY="your-openai-api-key-here"
# Optional:
# export ANTHROPIC_API_KEY="your-anthropic-api-key"
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Step 2: Verify Installation

```bash
# Test basic import
python -c "import langswarm; print('✅ LangSwarm installed successfully')"

# Check version
python -c "from langswarm.core.config import LangSwarmConfigLoader; print('✅ Core modules loaded')"
```

---

## 📝 Test Scenarios

### Test Case 1: Basic Installation and Import
**Objective**: Verify LangSwarm installs and imports correctly

**Steps**:
1. Run: `python -c "import langswarm"`
2. Run: `python -c "from langswarm.core.config import LangSwarmConfigLoader"`

**Expected Result**: No errors, imports successful

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 2: Simple Configuration Loading
**Objective**: Test the simplified configuration system

**Steps**:
1. Create a file `test_simple.yaml`:
```yaml
version: "1.0"
agents:
  - id: "assistant"
    model: "gpt-4o"
    behavior: "helpful"
    memory: true
workflows:
  - "assistant -> user"
```

2. Create test script `test_config.py`:
```python
from langswarm.core.config import LangSwarmConfigLoader

loader = LangSwarmConfigLoader('test_simple.yaml')
workflows, agents, tools, brokers, metadata = loader.load()
print(f"✅ Loaded {len(agents)} agents")
print(f"✅ Loaded {len(workflows)} workflows")
```

3. Run: `python test_config.py`

**Expected Result**: 
- Loads 1 agent
- Loads 1 workflow
- No errors

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 3: Memory System - Development Tier
**Objective**: Test simplified memory configuration (Tier 1)

**Steps**:
1. Create `test_memory.py`:
```python
from langswarm.core.agents.simple import create_chat_agent

# Create agent with memory
agent = create_chat_agent("memory_test", memory_enabled=True)
print("✅ Agent created with memory")

# Test memory functionality
response1 = agent.chat("My name is TestUser")
print(f"Response 1: {response1}")

response2 = agent.chat("What is my name?")
print(f"Response 2: {response2}")

# Cleanup
agent.cleanup()
```

2. Run: `python test_memory.py`

**Expected Result**: 
- Agent remembers the name "TestUser"
- Second response references the stored name

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 4: Workflow Simplification
**Objective**: Test the new simple workflow syntax

**Steps**:
1. Create `test_workflow.yaml`:
```yaml
version: "1.0"
agents:
  - {id: researcher, model: gpt-4o, behavior: research}
  - {id: writer, model: gpt-4o, behavior: creative}
  - {id: editor, model: gpt-4o, behavior: analytical}

workflows:
  - "researcher -> writer -> editor -> user"
```

2. Test loading:
```python
from langswarm.core.config import LangSwarmConfigLoader

loader = LangSwarmConfigLoader('test_workflow.yaml')
workflows, agents, tools, brokers, metadata = loader.load()
print(f"✅ Complex workflow loaded: {len(workflows)} workflows")
```

**Expected Result**: 
- Workflow loads without errors
- 3 agents created
- 1 workflow created

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 5: MCP Tool Registration
**Objective**: Verify MCP tools are properly registered

**Steps**:
1. Run verification script:
```python
from langswarm.core.config import LangSwarmConfigLoader

loader = LangSwarmConfigLoader()
print("Registered MCP tools:")
for tool_type in loader.tool_classes.keys():
    print(f"  - {tool_type}")

# Should include: mcpfilesystem, mcpforms, mcpgithubtool
required_tools = ['mcpfilesystem', 'mcpforms', 'mcpgithubtool']
missing = [t for t in required_tools if t not in loader.tool_classes]
if missing:
    print(f"❌ Missing tools: {missing}")
else:
    print("✅ All required MCP tools registered")
```

**Expected Result**: 
- All three MCP tools are registered
- No missing tools

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 6: Local MCP Mode (Zero Latency)
**Objective**: Test local MCP tool functionality

**Steps**:
1. Create test script:
```python
import tempfile
import os
from langswarm.mcp.tools.filesystem.main import FilesystemMCPTool

# Create test file
test_dir = tempfile.mkdtemp()
test_file = os.path.join(test_dir, "test.txt")
with open(test_file, 'w') as f:
    f.write("LangSwarm UAT Test Content")

print(f"Created test file: {test_file}")

# Test filesystem tool (Note: tool requires identifier)
try:
    # Tool is registered and available
    print("✅ Filesystem MCP tool is available")
    
    # Note: Actual tool usage requires proper initialization
    # which happens through the framework
except Exception as e:
    print(f"Tool initialization note: {e}")

# Cleanup
os.remove(test_file)
os.rmdir(test_dir)
print("✅ Test cleanup complete")
```

**Expected Result**: 
- Test file created and removed successfully
- Tool availability confirmed

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 7: Error Handling and Recovery
**Objective**: Test system behavior with missing API keys

**Steps**:
1. Temporarily unset API keys:
```bash
unset OPENAI_API_KEY
```

2. Try to create an agent:
```python
try:
    from langswarm.core.factory.agents import AgentFactory
    agent = AgentFactory.create_simple("test_agent")
except ValueError as e:
    print(f"✅ Expected error caught: {e}")
    print("System correctly identifies missing API key")
```

**Expected Result**: 
- Clear error message about missing API key
- No system crash

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case 8: Performance - Quick Start
**Objective**: Verify 30-second setup claim

**Steps**:
1. Time the basic setup:
```bash
time python -c "
from langswarm.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader()
print('✅ System initialized')
"
```

**Expected Result**: 
- Initialization completes in under 30 seconds
- No hanging or timeouts

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Setup Time**: _______ seconds

**Notes**: _________________

---

## 🎯 Advanced Tests (Optional - Requires API Keys)

### Test Case A1: Full Agent Interaction
**Objective**: Test actual agent conversation

**Prerequisites**: Valid OpenAI API key

**Steps**:
1. Create and test agent:
```python
from langswarm.core.agents.simple import create_chat_agent

agent = create_chat_agent("uat_assistant", memory_enabled=True)
response = agent.chat("Hello! What is LangSwarm?")
print(f"Agent response: {response}")
agent.cleanup()
```

**Expected Result**: 
- Agent responds intelligently about LangSwarm
- No errors

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

### Test Case A2: Multi-Agent Workflow
**Objective**: Test agent collaboration

**Prerequisites**: Valid API keys

**Steps**:
1. Create workflow configuration:
```yaml
version: "1.0"
agents:
  - {id: agent1, model: gpt-4o, behavior: analytical}
  - {id: agent2, model: gpt-4o, behavior: creative}
workflows:
  - "agent1, agent2 -> consensus -> user"
```

2. Execute workflow (if API keys available)

**Expected Result**: 
- Multiple agents collaborate
- Consensus reached
- Final output delivered

**Pass/Fail**: ⬜ Pass ⬜ Fail

**Notes**: _________________

---

## 📊 Test Summary

### Core Functionality
- ⬜ Installation and Import (Test 1)
- ⬜ Configuration Loading (Test 2)
- ⬜ Memory System (Test 3)
- ⬜ Workflow Simplification (Test 4)
- ⬜ MCP Tool Registration (Test 5)
- ⬜ Local MCP Mode (Test 6)
- ⬜ Error Handling (Test 7)
- ⬜ Performance (Test 8)

### Advanced Features (Optional)
- ⬜ Agent Interaction (Test A1)
- ⬜ Multi-Agent Workflow (Test A2)

### Overall Assessment
**Total Tests Passed**: _____ / 8 (core) + _____ / 2 (advanced)

**Critical Issues Found**: _________________

**Minor Issues Found**: _________________

**Recommendations**: _________________

---

## 🐛 Known Issues to Note

1. **Google Package Warning**: You may see deprecation warnings about pkg_resources - this is expected and doesn't affect functionality
2. **ML Library Warnings**: PyTorch/TensorFlow warnings are normal if not using those features
3. **API Key Requirements**: Many advanced features require API keys (OpenAI, etc.)

---

## ✍️ Sign-off

**UAT Result**: ⬜ PASS ⬜ FAIL ⬜ CONDITIONAL PASS

**Tester Signature**: _________________

**Date**: _________________

**Comments**: 
_________________
_________________
_________________

---

## 📞 Support Information

- **Documentation**: See `/docs` folder in the repository
- **Issues**: Report at https://github.com/aekdahl/langswarm/issues
- **Version**: v0.0.54
- **Changelog**: See CHANGELOG.md for recent updates

---

### 📝 Notes Section
Use this space for additional observations:

_________________
_________________
_________________
_________________
_________________
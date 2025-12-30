# LangSwarm Error Handling Guide

**Understanding and resolving LangSwarm errors effectively**

## 🎯 Overview

LangSwarm V2 introduces a comprehensive error system designed to provide clear, actionable guidance when things go wrong. Every error includes context about what happened, why it failed, and what you can do to fix it.

---

## 🔍 Understanding LangSwarm Errors

### Error Message Format

LangSwarm V2 errors provide rich, structured information:

```
❌ Configuration file not found: config.yaml
🔍 Component: config_loader
⚙️ Operation: load_file
💡 Suggestion: Check that the config file exists and is readable
🔗 Caused by: FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'
```

**Error Components:**
- **❌ Message**: What went wrong
- **🔍 Component**: Which part of LangSwarm had the issue
- **⚙️ Operation**: What specific operation failed
- **💡 Suggestion**: How to fix the problem
- **🔗 Caused by**: Underlying technical error (if applicable)

### Error Severity Levels

| Severity | Symbol | Meaning | Action Required |
|----------|--------|---------|-----------------|
| **CRITICAL** | 🔥 | System halt required | Immediate attention, restart may be needed |
| **ERROR** | ❌ | Operation failed | Fix the issue, operation cannot continue |
| **WARNING** | ⚠️ | Potential issue | Review and consider fixing |
| **INFO** | ℹ️ | Informational | No action needed |

---

## 🛠️ Common Error Categories

### Configuration Errors

**Most Common Issues:**

#### Missing Configuration File
```
❌ Configuration file not found: langswarm.yaml
💡 Suggestion: Create a configuration file or specify the correct path
```

**Solution:**
```bash
# Create a basic configuration file
cat > langswarm.yaml << EOF
version: "1.0"
agents:
  - id: "assistant"
    model: "gpt-4o"
    behavior: "helpful"
workflows:
  - "assistant -> user"
EOF
```

#### Missing API Keys
```
❌ OpenAI API key not found
💡 Suggestion: Set OPENAI_API_KEY environment variable or add to config file
```

**Solutions:**
```bash
# Option 1: Environment variable
export OPENAI_API_KEY=sk-your-api-key-here

# Option 2: Configuration file
echo "openai_api_key: sk-your-api-key-here" >> langswarm.yaml
```

#### Invalid YAML Syntax
```
❌ Invalid YAML syntax in configuration
💡 Suggestion: Validate YAML syntax and fix formatting errors
```

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('langswarm.yaml'))"

# Use online YAML validator
# https://yaml-online-parser.appspot.com/
```

### Agent Errors

#### Agent Initialization Failures
```
❌ Failed to initialize agent with model gpt-4-unknown
💡 Suggestion: Check model name and API key validity
```

**Solution:**
```yaml
# Use correct model names
agents:
  - id: "assistant"
    model: "gpt-4o"  # ✅ Correct
    # model: "gpt-4-unknown"  # ❌ Invalid
```

#### Rate Limit Errors
```
❌ OpenAI API rate limit exceeded
💡 Suggestion: Wait 60 seconds before retrying or upgrade your OpenAI plan
```

**Solutions:**
```python
# Add retry logic with exponential backoff
import time
import random

def chat_with_retry(agent, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return agent.chat(message)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
```

### Tool Errors

#### Tool Permission Errors
```
❌ BigQuery access denied for dataset 'my_dataset'
💡 Suggestion: Check BigQuery permissions and service account access
```

**Solution:**
```bash
# Check Google Cloud authentication
gcloud auth list
gcloud auth application-default login

# Verify project and permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT
```

#### Tool Parameter Errors
```
❌ Invalid parameter 'file_path': must be a valid file path
💡 Suggestion: Provide an absolute or relative path to an existing file
```

**Solution:**
```python
# Use proper file paths
tool_params = {
    "file_path": "/absolute/path/to/file.txt",  # ✅ Absolute path
    # "file_path": "./relative/path/to/file.txt",  # ✅ Relative path
    # "file_path": "just-filename.txt",  # ❌ May not work
}
```

### Workflow Errors

#### Step Execution Failures
```
❌ Workflow step 'analyze_data' failed
💡 Suggestion: Check agent configuration and tool availability
```

**Solution:**
```yaml
workflows:
  - id: data_analysis
    steps:
      - id: analyze_data
        agent: data_analyst
        input: "${user_input}"
        # Ensure agent 'data_analyst' exists in agents.yaml
```

#### Routing Errors
```
❌ Invalid workflow routing: step 'missing_step' not found
💡 Suggestion: Check that all referenced steps exist in the workflow
```

**Solution:**
```yaml
workflows:
  - id: my_workflow
    steps:
      - id: step1
        agent: agent1
        output:
          to: step2  # ✅ Make sure step2 exists
      - id: step2  # ✅ This step exists
        agent: agent2
```

### Memory Errors

#### Database Connection Issues
```
❌ Failed to connect to ChromaDB
💡 Suggestion: Ensure ChromaDB is running and accessible
```

**Solutions:**
```bash
# Check if ChromaDB is running
curl -X GET "http://localhost:8000/api/v1/heartbeat"

# Start ChromaDB if needed
docker run -p 8000:8000 chromadb/chroma

# Or use SQLite memory (simpler for development)
```

```yaml
memory:
  backend: "sqlite"  # Simpler alternative
  # backend: "chromadb"  # Requires ChromaDB server
```

---

## 🚨 Emergency Troubleshooting

### Quick Diagnostic Steps

1. **Check Basic Configuration**
   ```bash
   # Verify config file exists and is valid
   python -c "
   import yaml
   with open('langswarm.yaml') as f:
       config = yaml.safe_load(f)
       print('✅ Configuration is valid')
       print(f'Agents: {len(config.get(\"agents\", []))}')
   "
   ```

2. **Verify API Keys**
   ```bash
   # Test OpenAI API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models | jq '.data[0].id'
   ```

3. **Check Dependencies**
   ```bash
   # Verify LangSwarm installation
   python -c "import langswarm; print(f'LangSwarm version: {langswarm.__version__}')"
   
   # Check required packages
   pip list | grep -E "(openai|langchain|pydantic)"
   ```

### Enable Debug Mode

When you need detailed error information:

```python
import os
from langswarm.core.debug import enable_debug_tracing

# Enable emergency debugging (34% performance impact)
if os.getenv('EMERGENCY_DEBUG') == 'true':
    enable_debug_tracing("emergency.jsonl")

# Your LangSwarm code - now fully traced
```

```bash
# Run with emergency debugging
export EMERGENCY_DEBUG=true
python your_script.py

# Analyze the debug trace
python -m langswarm.core.debug.cli analyze emergency.jsonl
```

---

## 🔧 Error Recovery Strategies

### Automatic Recovery

LangSwarm V2 includes built-in recovery strategies:

```python
from langswarm.core.errors import ErrorHandler

handler = ErrorHandler()

# Automatic recovery for transient errors
try:
    result = unreliable_operation()
except TransientError as e:
    # Handler automatically retries with exponential backoff
    result = handler.handle_error(e)
```

### Manual Recovery Patterns

#### Configuration Recovery
```python
def load_config_with_fallback():
    try:
        return load_config("langswarm.yaml")
    except ConfigurationError:
        # Fallback to environment variables
        return create_config_from_env()
    except Exception:
        # Last resort: minimal default config
        return get_minimal_config()
```

#### Agent Recovery
```python
def create_agent_with_fallback(model_name):
    models_to_try = [model_name, "gpt-4o", "gpt-3.5-turbo"]
    
    for model in models_to_try:
        try:
            return create_agent(model)
        except AgentError as e:
            if model == models_to_try[-1]:
                raise e  # Re-raise if last model fails
            continue
```

#### Tool Recovery
```python
def execute_tool_with_fallback(tool_name, params):
    try:
        return execute_tool(tool_name, params)
    except ToolError as e:
        if e.severity == ErrorSeverity.CRITICAL:
            raise  # Don't retry critical errors
        
        # Try alternative tool or simplified operation
        return execute_fallback_tool(tool_name, params)
```

---

## 📊 Error Prevention Best Practices

### Configuration Validation

```python
# Validate configuration before using it
from langswarm.core.config import validate_config

def safe_load_config():
    config = load_config("langswarm.yaml")
    
    # Validate before using
    is_valid, errors = validate_config(config)
    if not is_valid:
        for error in errors:
            print(f"❌ {error}")
        raise ConfigurationError("Invalid configuration")
    
    return config
```

### Input Validation

```python
# Validate inputs before processing
def safe_agent_chat(agent, message):
    if not isinstance(message, str):
        raise ValidationError("Message must be a string")
    
    if len(message.strip()) == 0:
        raise ValidationError("Message cannot be empty")
    
    if len(message) > 10000:
        raise ValidationError("Message too long (max 10,000 characters)")
    
    return agent.chat(message)
```

### Resource Monitoring

```python
# Monitor resources to prevent issues
import psutil

def check_system_resources():
    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        raise SystemResourceError("Memory usage too high")
    
    # Check disk space
    disk = psutil.disk_usage('/')
    if disk.percent > 95:
        raise SystemResourceError("Disk space critically low")
```

---

## 🆘 Getting Help

### Self-Diagnosis Tools

```bash
# Run LangSwarm health check
python -m langswarm.core.debug.cli health-check

# Test basic functionality
python -m langswarm.core.debug.cli run-case-1

# Analyze recent errors
python -m langswarm.core.debug.cli analyze debug_traces/
```

### Error Reporting

When reporting errors, include:

1. **Full Error Message**: Complete error output with context
2. **Configuration**: Your `langswarm.yaml` (sanitize API keys)
3. **Environment**: Python version, LangSwarm version, OS
4. **Reproduction Steps**: Minimal code to reproduce the issue
5. **Debug Trace**: If available, attach trace file

**Example Error Report:**
```
## Error Description
❌ ConfigurationError: Missing required API key

## Environment
- LangSwarm: v2.0.0
- Python: 3.9.7
- OS: macOS 12.0

## Configuration
```yaml
version: "1.0"
agents:
  - id: "assistant"
    model: "gpt-4o"
# Missing openai_api_key
```

## Reproduction Steps
1. Create config file without API key
2. Run: python -c "from langswarm import create_agent; create_agent('assistant')"
3. Error occurs

## Debug Trace
[Attach debug.jsonl if available]
```

---

**Remember: LangSwarm V2 errors are designed to be helpful and actionable. When in doubt, read the suggestion in the error message - it's specifically crafted to help you resolve the issue quickly.**

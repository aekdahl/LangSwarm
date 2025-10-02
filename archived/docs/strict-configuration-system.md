# LangSwarm V2 Strict Configuration System

## Overview

LangSwarm V2 implements a **strict, fail-fast configuration system** that eliminates all silent fallbacks, auto-generation, and placeholder values. The system is designed to fail immediately when any configuration is missing, invalid, or inaccessible, ensuring that deployment issues are caught early and not hidden by default values.

## Key Principles

1. **No Auto-Generation**: Configuration files are never created automatically
2. **No Silent Fallbacks**: Missing values cause immediate failures, not warnings
3. **No Placeholders**: Environment variables must be set or have explicit defaults
4. **Runtime Validation**: All dependencies are validated at startup
5. **Fail Fast**: Issues are caught immediately during configuration loading

## Configuration Requirements

### 1. Configuration File Discovery

**STRICT BEHAVIOR**: Configuration files must exist explicitly.

The system searches for configuration files in this order:
```
- langswarm.yaml
- langswarm.yml
- config.yaml
- config.yml
- .langswarm.yaml
- .langswarm.yml
```

In these directories:
```
- . (current directory)
- config/
- configs/
- ~/.langswarm/
- /etc/langswarm/
```

**❌ What happens when no config is found:**
```
ConfigurationError: No configuration file found. Searched for ['langswarm.yaml', 'langswarm.yml', ...] 
in paths: ['.', 'config', ...]. Please create a valid configuration file in one of these locations.
```

**✅ Solution:**
Create a valid configuration file in one of the searched locations.

### 2. Environment Variable Substitution

**STRICT BEHAVIOR**: All environment variables must be set or have explicit defaults.

**❌ Invalid (will fail):**
```yaml
agents:
  - id: assistant
    provider: openai
    api_key: ${OPENAI_API_KEY}  # Fails if OPENAI_API_KEY not set
```

**✅ Valid options:**
```yaml
# Option 1: Ensure environment variable is set
agents:
  - id: assistant
    provider: openai
    api_key: ${OPENAI_API_KEY}  # OPENAI_API_KEY must be set

# Option 2: Provide explicit default
agents:
  - id: assistant
    provider: openai
    api_key: ${OPENAI_API_KEY:sk-default-key}  # Uses default if not set
```

**Error when environment variable missing:**
```
ConfigurationError: Required environment variable 'OPENAI_API_KEY' is not set. 
Please set this environment variable or provide a default value using ${OPENAI_API_KEY:default_value} syntax.
```

### 3. Include Files

**STRICT BEHAVIOR**: All include files must exist and be accessible.

**❌ Invalid (will fail):**
```yaml
includes:
  - agents.yaml      # Must exist
  - tools.yaml       # Must exist
  - missing.yaml     # Will cause failure
```

**✅ Valid:**
```yaml
includes:
  - agents.yaml      # File exists and is readable
  - tools.yaml       # File exists and is readable
```

**Error when include file missing:**
```
ConfigurationError: Required include file not found: /path/to/missing.yaml. 
All include files must exist and be accessible.
```

**Error on circular includes:**
```
ConfigurationError: Circular include detected: /path/to/file.yaml. 
Include files cannot reference each other in a circular manner.
```

### 4. Runtime Dependency Validation

**STRICT BEHAVIOR**: All configured services and dependencies are validated at startup.

The system validates:

#### Provider API Keys
- **OpenAI**: Requires `OPENAI_API_KEY` environment variable
- **Anthropic**: Requires `ANTHROPIC_API_KEY` environment variable  
- **Gemini**: Requires `GEMINI_API_KEY` environment variable
- **Cohere**: Requires `COHERE_API_KEY` environment variable

#### Memory Backends
- **Redis**: Validates connection and requires `redis` package
- **PostgreSQL**: Validates `psycopg2` package installation
- **SQLite**: Validates directory write permissions
- **ChromaDB**: Validates `chromadb` package installation
- **Qdrant**: Validates `qdrant-client` package installation

#### SSL Configuration
- **Certificate files**: Must exist and be readable
- **Key files**: Must exist and be readable

#### File Permissions
- **Log files**: Directory must be writable
- **Trace files**: Directory must be writable
- **Database files**: Directory must be writable

**Example runtime validation errors:**
```
ConfigurationError: Runtime validation failed:
  - Required environment variable 'OPENAI_API_KEY' for provider 'openai' is not set
  - Redis backend configured but not accessible at redis://localhost:6379: Connection refused
  - SSL certificate file not found: /path/to/cert.pem
  - Log file directory '/var/log/langswarm' is not writable
```

## Configuration Validation

**STRICT BEHAVIOR**: All warnings are treated as errors by default.

The validation system uses `strict_mode=True` by default, which means:
- Configuration warnings become errors
- All issues must be resolved before startup
- No "best effort" configurations are allowed

### Validation Categories

1. **Schema Validation**: Required fields, data types, value ranges
2. **Cross-Reference Validation**: Agent/tool/workflow references must exist
3. **Environment Validation**: API keys and dependencies must be available
4. **Performance Validation**: Resource limits and optimization warnings
5. **Security Validation**: Security best practices enforcement

## Migration from Loose Configuration

If you're migrating from a system with fallbacks, here's how to fix common issues:

### 1. Missing Configuration Files
**Old behavior**: Auto-generated default config
**New requirement**: Create explicit configuration

```bash
# Create minimal configuration
cat > langswarm.yaml << EOF
version: "2.0"
name: "My LangSwarm Setup"
agents:
  - id: assistant
    provider: openai
    model: gpt-4o
    system_prompt: "You are a helpful AI assistant."
EOF
```

### 2. Missing Environment Variables
**Old behavior**: Placeholders or warnings
**New requirement**: Set all required variables

```bash
# Set required environment variables
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### 3. Missing Dependencies
**Old behavior**: Degraded functionality
**New requirement**: Install all dependencies

```bash
# Install required packages
pip install redis psycopg2 chromadb qdrant-client
```

### 4. File Permissions
**Old behavior**: Fallback to current directory
**New requirement**: Proper permissions

```bash
# Ensure proper permissions
mkdir -p /var/log/langswarm
chmod 755 /var/log/langswarm
```

## Testing Configuration

Use the validation tools to test your configuration:

```python
from langswarm.v2.core.config import load_config, validate_config

# Load and validate configuration
try:
    config = load_config("langswarm.yaml")
    is_valid, issues = validate_config(config, strict_mode=True)
    
    if not is_valid:
        for issue in issues:
            print(f"{issue.severity}: {issue.message}")
            if issue.suggestion:
                print(f"  Suggestion: {issue.suggestion}")
    else:
        print("Configuration is valid!")
        
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Best Practices

1. **Use Environment Variables**: Store sensitive data in environment variables
2. **Validate Early**: Test configuration in development before deployment
3. **Document Dependencies**: Clearly document all required packages and services
4. **Version Control**: Keep configuration files in version control
5. **Environment-Specific Configs**: Use separate configs for dev/staging/production
6. **Include Files**: Use includes to organize large configurations

## Error Recovery

When configuration errors occur:

1. **Read the error message carefully** - it contains specific guidance
2. **Check file paths** - ensure all files exist and are accessible
3. **Verify environment variables** - use `env | grep LANGSWARM` to check
4. **Test dependencies** - manually verify service connections
5. **Use validation tools** - run validation before deployment

## Example Strict Configuration

```yaml
version: "2.0"
name: "Production LangSwarm"
description: "Strict production configuration"

agents:
  - id: assistant
    name: "Production Assistant"
    provider: openai
    model: gpt-4o
    system_prompt: "You are a helpful AI assistant."
    temperature: 0.7
    tools: ["web_search", "file_system"]

tools:
  web_search:
    id: web_search
    type: builtin
    name: "Web Search"
    description: "Search the web for information"
    enabled: true
    
  file_system:
    id: file_system
    type: builtin
    name: "File System"
    description: "File system operations"
    enabled: true

memory:
  enabled: true
  backend: redis
  config:
    url: ${REDIS_URL:redis://localhost:6379}
    key_prefix: "langswarm:prod:"

security:
  openai_api_key_env: "OPENAI_API_KEY"
  require_auth: true
  encrypt_memory: true
  log_sensitive_data: false

observability:
  log_level: INFO
  structured_logging: true
  tracing_enabled: true
  trace_output_file: "/var/log/langswarm/traces.jsonl"
  metrics_enabled: true

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  ssl_enabled: true
  ssl_cert_file: "/etc/ssl/certs/langswarm.pem"
  ssl_key_file: "/etc/ssl/private/langswarm.key"
  cors_origins: ["https://yourdomain.com"]
```

This configuration will fail fast if:
- `REDIS_URL` environment variable is not set (and redis://localhost:6379 is not accessible)
- `OPENAI_API_KEY` environment variable is not set
- SSL certificate files don't exist
- Log directory is not writable
- Redis is not accessible
- Required packages are not installed

## Provider Builder Strict Mode

### Overview
The Agent Builder system now operates in strict mode, eliminating all fallbacks and ensuring that all provider dependencies are available and properly configured.

### 1. Strict Import Handling

**STRICT BEHAVIOR**: All provider modules must be available at import time.

**❌ Old behavior (with fallbacks):**
```python
try:
    from .providers.openai import OpenAIProvider
except ImportError:
    OpenAIProvider = None  # Graceful fallback
```

**✅ New behavior (strict):**
```python
# Direct imports - fail immediately if dependencies missing
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
# ... all providers imported directly
```

**Error when provider dependencies missing:**
```
ImportError: No module named 'openai'
Can't import openai package. Install with: pip install openai
```

### 2. Strict API Key Validation

**STRICT BEHAVIOR**: API keys must be provided or available in environment variables.

**❌ Invalid (will fail immediately):**
```python
# Missing API key
agent = AgentBuilder().openai().build()  # Fails: API key required
```

**✅ Valid options:**
```python
# Option 1: Provide API key directly
agent = AgentBuilder().openai(api_key="sk-...").build()

# Option 2: Set environment variable
# export OPENAI_API_KEY="sk-..."
agent = AgentBuilder().openai().build()
```

**API Key Requirements by Provider:**
- **OpenAI**: `OPENAI_API_KEY` required
- **Anthropic**: `ANTHROPIC_API_KEY` required
- **Gemini**: `GEMINI_API_KEY` or `GOOGLE_API_KEY` required
- **Cohere**: `COHERE_API_KEY` required
- **Mistral**: `MISTRAL_API_KEY` required
- **HuggingFace**: `HUGGINGFACE_API_KEY` required (unless `use_local=True`)
- **Local**: No API key required (uses local endpoints)
- **Mock**: No API key required (testing only)

### 3. Strict Model Validation

**STRICT BEHAVIOR**: Models must be supported by the provider.

**❌ Invalid (will fail):**
```python
agent = (AgentBuilder()
         .openai()
         .model("invalid-model")  # Fails: unsupported model
         .build())
```

**✅ Valid:**
```python
agent = (AgentBuilder()
         .openai()
         .model("gpt-4o")  # Supported model
         .build())
```

**Supported Models by Provider:**

**OpenAI:**
- `gpt-4o`, `gpt-4o-mini`, `gpt-4`, `gpt-4-turbo`
- `gpt-4-vision-preview`, `gpt-3.5-turbo`, `gpt-3.5-turbo-16k`
- `o1-preview`, `o1-mini`

**Anthropic:**
- `claude-3-5-sonnet-20241022`, `claude-3-5-sonnet-20240620`
- `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`, `claude-2.1`, `claude-2.0`, `claude-instant-1.2`

**Gemini:**
- `gemini-pro`, `gemini-pro-vision`, `gemini-ultra`

### 4. Strict Tool Injection

**STRICT BEHAVIOR**: All requested tools must be available in the registry.

**❌ Invalid (will fail):**
```python
agent = (AgentBuilder()
         .openai()
         .tools(["web_search", "nonexistent_tool"])  # Fails: tool not found
         .build())
```

**✅ Valid:**
```python
agent = (AgentBuilder()
         .openai()
         .tools(["web_search", "file_system"])  # All tools exist
         .build())
```

### 5. No Mock Provider Fallbacks

**STRICT BEHAVIOR**: No automatic fallback to mock providers.

**❌ Old behavior:**
```python
# Would silently fall back to mock provider if real provider unavailable
agent = AgentBuilder().openai().build()
```

**✅ New behavior:**
```python
# Fails immediately if provider not available
agent = AgentBuilder().openai().build()  # ImportError if openai package missing

# Mock provider only allowed if explicitly requested
agent = AgentBuilder().provider(ProviderType.MOCK).build()
```

### Error Examples

```python
# Missing API key
ValueError: OpenAI API key is required. Provide it via api_key parameter or set OPENAI_API_KEY environment variable.

# Invalid model
ValueError: Model 'invalid-model' not supported by OpenAI provider. Valid models: gpt-4o, gpt-4o-mini, ...

# Missing tools
ValueError: Requested tools not found in registry: ['nonexistent_tool']. Available tools: ['web_search', 'file_system', ...]. Ensure all tools are properly registered before building the agent.

# Missing provider dependency
ImportError: No module named 'anthropic'. Install with: pip install anthropic

# Tool injection failure
RuntimeError: Tool injection failed for agent 'my-agent': Tool 'custom_tool' not properly initialized
```

### Migration Guide

**1. Install all required provider dependencies:**
```bash
# Install providers you plan to use
pip install openai anthropic google-generativeai cohere mistralai transformers
```

**2. Set all required API keys:**
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export COHERE_API_KEY="..."
export MISTRAL_API_KEY="..."
export HUGGINGFACE_API_KEY="..."
```

**3. Use supported models only:**
```python
# Check documentation for supported models per provider
agent = AgentBuilder().openai().model("gpt-4o").build()  # ✅ Supported
```

**4. Register all required tools:**
```python
# Ensure tools are registered before use
from langswarm.v2.tools.registry import ToolRegistry
registry = ToolRegistry()
print(registry.list_tools())  # Check available tools
```

**5. Handle errors appropriately:**
```python
try:
    agent = AgentBuilder().openai().build()
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle missing API keys, invalid models, etc.
except ImportError as e:
    print(f"Dependency error: {e}")
    # Handle missing provider packages
except RuntimeError as e:
    print(f"Runtime error: {e}")
    # Handle tool injection failures, etc.
```

## Summary

The strict configuration system ensures that:
- **All dependencies are validated at startup**
- **Missing configuration causes immediate failure**
- **No silent fallbacks hide deployment issues**
- **Environment issues are caught early**
- **Configuration drift is prevented**
- **Provider dependencies are explicit and validated**
- **API keys must be properly configured**
- **All tools must be available and registered**
- **No mock provider fallbacks in production**

This approach may require more initial setup but provides much higher reliability and easier debugging in production environments.

# LangSwarm V2 Configuration Guide

**Modern, type-safe configuration system with templates, validation, and automated migration**

## 🎯 Overview

LangSwarm V2 provides a completely modernized configuration system that replaces the monolithic 4,664-line V1 config.py with a clean, modular, type-safe architecture. Configure LangSwarm with simple YAML files, environment variables, templates, and comprehensive validation.

**Key Benefits:**
- **Type Safety**: Full dataclass-based configuration with validation
- **Simple & Powerful**: Easy single-file configs, advanced multi-file support
- **Template System**: Pre-built templates for quick setup
- **Environment Integration**: Secure API key handling and variable substitution
- **Automated Migration**: Zero-effort V1 to V2 migration
- **Comprehensive Validation**: Schema, environment, performance, and security validation

---

## 🚀 Quick Start

### **Simple Configuration**

Create a `langswarm.yaml` file:

```yaml
# Simple chatbot configuration
agents:
  - id: "chatbot"
    name: "Simple Chatbot"
    provider: "openai"
    model: "gpt-4"
    system_prompt: "You are a helpful assistant."

tools:
  - id: "filesystem"
    name: "File System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]

workflows:
  - id: "chat_workflow"
    name: "Chat Workflow"
    agent_id: "chatbot"
    tool_ids: ["filesystem"]
```

### **Load and Use Configuration**

```python
from langswarm.core.config import load_config

# Load configuration
config = load_config("langswarm.yaml")

# Access type-safe configuration
agent = config.get_agent("chatbot")
print(f"Agent: {agent.name} using {agent.provider}")

tool = config.get_tool("filesystem")
print(f"Tool: {tool.name} ({tool.type})")

workflow = config.get_workflow("chat_workflow")
print(f"Workflow: {workflow.name}")
```

### **Using Templates**

```python
from langswarm.core.config import load_template

# Use pre-built templates
config = load_template("development_setup")  # Development environment
config = load_template("production_setup")   # Production environment
config = load_template("simple_chatbot")     # Simple chatbot setup
```

---

## 📋 Configuration Schema

### **Main Configuration Structure**

```python
from langswarm.core.config.schema import LangSwarmConfig

@dataclass
class LangSwarmConfig:
    """Complete LangSwarm configuration"""
    agents: List[AgentConfig] = field(default_factory=list)
    tools: List[ToolConfig] = field(default_factory=list)
    workflows: List[WorkflowConfig] = field(default_factory=list)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
```

### **Agent Configuration**

```yaml
agents:
  - id: "gpt4_agent"
    name: "GPT-4 Agent"
    provider: "openai"          # openai, anthropic, gemini, huggingface, ollama
    model: "gpt-4"
    system_prompt: "You are a helpful AI assistant."
    temperature: 0.7
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"  # Environment variable for API key
    
  - id: "claude_agent"
    name: "Claude Agent"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: "You are Claude, a helpful AI assistant."
    temperature: 0.5
    api_key_env: "ANTHROPIC_API_KEY"
```

### **Tool Configuration**

```yaml
tools:
  # MCP Tool
  - id: "filesystem"
    name: "File System Tool"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]
      
  # Memory Tool
  - id: "memory_sqlite"
    name: "SQLite Memory"
    type: "memory"
    backend: "sqlite"
    connection_params:
      db_path: "memory.db"
      
  # Plugin Tool
  - id: "notification"
    name: "Notification Plugin"
    type: "plugin"
    plugin_config:
      module_path: "langswarm.plugins.notification"
      provider: "slack"
```

### **Workflow Configuration**

```yaml
workflows:
  - id: "research_workflow"
    name: "Research Assistant"
    agent_id: "gpt4_agent"
    tool_ids: ["filesystem", "memory_sqlite"]
    execution_mode: "sequential"  # sequential, parallel, conditional
    max_iterations: 10
    timeout_seconds: 300
```

### **Memory Configuration**

```yaml
memory:
  default_backend: "sqlite"
  backends:
    sqlite:
      db_path: "memory.db"
      enable_wal: true
    redis:
      host: "localhost"
      port: 6379
      db: 0
    chromadb:
      persist_directory: "./chromadb"
      collection_name: "langswarm_memory"
```

---

## 🌍 Environment Variables

### **Environment Variable Substitution**

```yaml
# Use environment variables with ${VAR} syntax
agents:
  - id: "openai_agent"
    name: "OpenAI Agent"
    provider: "openai"
    model: "${OPENAI_MODEL:gpt-4}"  # Default to gpt-4 if not set
    api_key_env: "OPENAI_API_KEY"
    
server:
  host: "${HOST:localhost}"        # Default to localhost
  port: ${PORT:8000}              # Default to 8000
  debug: ${DEBUG:false}           # Default to false
```

### **Required Environment Variables**

```bash
# API Keys
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export GOOGLE_API_KEY="your_google_key"

# Optional Configuration
export OPENAI_MODEL="gpt-4"
export HOST="0.0.0.0"
export PORT="8080"
export DEBUG="true"
```

### **Environment Validation**

```python
from langswarm.core.config import validate_environment

# Validate environment before starting
is_valid, missing_vars = validate_environment(config)

if not is_valid:
    print(f"Missing environment variables: {missing_vars}")
    exit(1)
```

---

## 📁 Multi-File Configuration

### **Main Configuration File**

```yaml
# langswarm.yaml
includes:
  - "agents.yaml"
  - "tools.yaml"
  - "workflows.yaml"

memory:
  default_backend: "sqlite"
  
server:
  host: "localhost"
  port: 8000
```

### **Separate Component Files**

**agents.yaml**:
```yaml
agents:
  - id: "gpt4_agent"
    name: "GPT-4 Agent"
    provider: "openai"
    model: "gpt-4"
    
  - id: "claude_agent"
    name: "Claude Agent" 
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
```

**tools.yaml**:
```yaml
tools:
  - id: "filesystem"
    name: "File System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]
```

**workflows.yaml**:
```yaml
workflows:
  - id: "main_workflow"
    name: "Main Workflow"
    agent_id: "gpt4_agent"
    tool_ids: ["filesystem"]
```

### **Loading Multi-File Configuration**

```python
# Automatically processes includes
config = load_config("langswarm.yaml")

# All components loaded from separate files
print(f"Agents: {len(config.agents)}")
print(f"Tools: {len(config.tools)}")
print(f"Workflows: {len(config.workflows)}")
```

---

## 📝 Templates

### **Available Templates**

#### **1. Simple Chatbot Template**

```python
from langswarm.core.config import load_template

config = load_template("simple_chatbot")
```

**Features:**
- Single GPT-4 agent
- Basic filesystem tool
- Simple chat workflow
- Perfect for getting started

#### **2. Development Setup Template**

```python
config = load_template("development_setup")
```

**Features:**
- Multiple agents (OpenAI, Anthropic)
- Comprehensive toolset (filesystem, memory, search)
- Development workflows
- Debug and logging enabled
- Local SQLite memory

#### **3. Production Setup Template**

```python
config = load_template("production_setup")
```

**Features:**
- Production-ready agent configurations
- Scalable Redis memory backend
- Performance-optimized settings
- Security configurations
- Monitoring and observability

### **Custom Template Creation**

```python
from langswarm.core.config import export_template

# Export current config as template
export_template(config, "my_custom_template.yaml", include_comments=True)
```

**Generated template with comments:**
```yaml
# Custom LangSwarm Configuration Template
# Generated on 2024-12-19

agents:
  # Primary conversational agent
  - id: "main_agent"
    name: "Main Assistant"
    provider: "openai"  # Options: openai, anthropic, gemini, huggingface, ollama
    model: "gpt-4"      # Model name for the provider
    # ... more options with comments
```

---

## ✅ Configuration Validation

### **Comprehensive Validation**

```python
from langswarm.core.config import validate_config

# Load and validate configuration
config = load_config("langswarm.yaml")
is_valid, validation_report = validate_config(config)

if is_valid:
    print("✅ Configuration is valid")
else:
    print("❌ Configuration has issues:")
    for issue in validation_report.issues:
        print(f"  {issue.severity}: {issue.message}")
```

### **Validation Categories**

#### **1. Schema Validation**
- Type checking and structure validation
- Required field verification
- Enum value validation

#### **2. Cross-Reference Validation**
- Agent references in workflows exist
- Tool references in workflows exist
- Provider and model compatibility

#### **3. Environment Validation**
- Required API keys present
- Environment variable accessibility
- Runtime dependency checking

#### **4. Performance Validation**
- Resource usage analysis
- Performance impact assessment
- Optimization recommendations

#### **5. Security Validation**
- API key security best practices
- Configuration security audit
- Sensitive data exposure checks

### **Validation Report**

```python
# Detailed validation report
print(f"Validation Summary:")
print(f"  Total issues: {len(validation_report.issues)}")
print(f"  Errors: {validation_report.error_count}")
print(f"  Warnings: {validation_report.warning_count}")
print(f"  Info: {validation_report.info_count}")

# Detailed issues
for issue in validation_report.issues:
    print(f"\n{issue.severity}: {issue.message}")
    print(f"  Component: {issue.component}")
    print(f"  Suggestion: {issue.suggestion}")
```

**Example validation output:**
```
ERROR: Agent 'gpt4_agent' referenced in workflow 'main_workflow' does not exist
  Component: workflows[0].agent_id
  Suggestion: Add agent with id 'gpt4_agent' or update workflow agent_id

WARNING: API key environment variable 'OPENAI_API_KEY' not set
  Component: agents[0].api_key_env
  Suggestion: Set environment variable or configure api_key_env
```

---

## 🔧 Configuration Management

### **Configuration Comparison**

```python
from langswarm.core.config import compare_configs

# Compare two configurations
config1 = load_config("current.yaml")
config2 = load_config("new.yaml")

comparison = compare_configs(config1, config2)

print(f"Configuration Differences:")
print(f"  Added: {len(comparison.added)}")
print(f"  Modified: {len(comparison.modified)}")
print(f"  Removed: {len(comparison.removed)}")

# Detailed differences
for diff in comparison.differences:
    print(f"{diff.type}: {diff.path} - {diff.description}")
```

### **Configuration Optimization**

```python
from langswarm.core.config import optimize_config

# Get optimization suggestions
optimization_report = optimize_config(config)

print(f"Optimization Suggestions:")
for category, suggestions in optimization_report.items():
    print(f"\n{category.title()}:")
    for suggestion in suggestions:
        print(f"  • {suggestion.description}")
        print(f"    Impact: {suggestion.impact}")
        print(f"    Effort: {suggestion.effort}")
```

**Example optimization output:**
```
Performance:
  • Use Redis instead of SQLite for memory in production
    Impact: 3x faster memory operations
    Effort: Low - change backend in config

  • Enable agent response caching
    Impact: 50% faster repeated queries
    Effort: Low - add caching config

Cost:
  • Use GPT-3.5-turbo for non-critical workflows
    Impact: 90% cost reduction
    Effort: Medium - test quality impact

Security:
  • Move API keys to environment variables
    Impact: Improved security posture
    Effort: Low - update config and environment
```

### **Configuration Export**

```python
from langswarm.core.config import export_config

# Export with comments for documentation
export_config(config, "documented_config.yaml", include_comments=True)

# Export minimal config for production
export_config(config, "production_config.yaml", include_comments=False)
```

---

## 🔄 Advanced Features

### **Conditional Configuration**

```yaml
# Environment-specific settings
agents:
  - id: "main_agent"
    name: "Main Agent"
    provider: "openai"
    model: "${MODEL:gpt-4}"
    # Development: faster, cheaper model
    # Production: powerful, reliable model
    
server:
  debug: ${DEBUG:false}
  # Development: true
  # Production: false
  
memory:
  backend: "${MEMORY_BACKEND:sqlite}"
  # Development: sqlite
  # Production: redis
```

### **Configuration Merging**

```python
from langswarm.core.config import merge_configs

# Base configuration
base_config = load_config("base.yaml")

# Environment-specific overrides
dev_config = load_config("development.yaml")
prod_config = load_config("production.yaml")

# Merge configurations
if environment == "development":
    config = merge_configs(base_config, dev_config)
else:
    config = merge_configs(base_config, prod_config)
```

### **Dynamic Configuration**

```python
# Modify configuration at runtime
config = load_config("langswarm.yaml")

# Add new agent
new_agent = AgentConfig(
    id="dynamic_agent",
    name="Dynamic Agent",
    provider="anthropic",
    model="claude-3-sonnet-20240229"
)
config.agents.append(new_agent)

# Update existing agent
agent = config.get_agent("main_agent")
agent.temperature = 0.8
agent.max_tokens = 4096

# Validate modified configuration
is_valid, report = validate_config(config)
```

---

## 📊 Configuration Examples

### **Development Environment**

```yaml
# development.yaml
agents:
  - id: "dev_agent"
    name: "Development Agent"
    provider: "openai"
    model: "gpt-3.5-turbo"  # Faster, cheaper for development
    temperature: 0.8        # More creative for testing
    max_tokens: 1024

tools:
  - id: "filesystem"
    name: "File System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]
      
memory:
  default_backend: "sqlite"
  backends:
    sqlite:
      db_path: "./dev_memory.db"

server:
  debug: true
  log_level: "DEBUG"
  
observability:
  logging:
    level: "DEBUG"
    format: "detailed"
  tracing:
    enabled: true
    output_file: "dev_traces.jsonl"
```

### **Production Environment**

```yaml
# production.yaml
agents:
  - id: "prod_agent"
    name: "Production Agent"
    provider: "openai"
    model: "gpt-4"           # Most capable model
    temperature: 0.3         # Consistent, reliable responses
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"
    
tools:
  - id: "filesystem"
    name: "File System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]
      timeout: 30
      
  - id: "memory_redis"
    name: "Redis Memory"
    type: "memory"
    backend: "redis"
    connection_params:
      host: "${REDIS_HOST:localhost}"
      port: ${REDIS_PORT:6379}
      password: "${REDIS_PASSWORD}"

memory:
  default_backend: "redis"
  
server:
  host: "0.0.0.0"
  port: ${PORT:8000}
  workers: ${WORKERS:4}
  debug: false
  
security:
  rate_limiting:
    enabled: true
    requests_per_minute: 60
  api_key_rotation:
    enabled: true
    rotation_days: 30
    
observability:
  logging:
    level: "INFO"
    format: "json"
  metrics:
    enabled: true
    export_interval: 60
  tracing:
    enabled: true
    sampling_rate: 0.1
```

### **Multi-Agent Setup**

```yaml
# multi_agent.yaml
agents:
  - id: "researcher"
    name: "Research Specialist"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a research specialist. You excel at:
      - Gathering information from multiple sources
      - Analyzing data and trends
      - Creating comprehensive research reports
      
  - id: "writer"
    name: "Content Writer"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: |
      You are a skilled content writer. You excel at:
      - Creating engaging, well-structured content
      - Adapting tone and style for different audiences
      - Editing and improving existing content
      
  - id: "reviewer"
    name: "Quality Reviewer"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a quality reviewer. You excel at:
      - Reviewing content for accuracy and quality
      - Providing constructive feedback
      - Ensuring consistency and standards

workflows:
  - id: "content_creation"
    name: "Content Creation Pipeline"
    steps:
      - agent_id: "researcher"
        task: "research"
        tools: ["web_search", "memory_sqlite"]
      - agent_id: "writer"
        task: "write"
        tools: ["filesystem", "memory_sqlite"]
      - agent_id: "reviewer"
        task: "review"
        tools: ["filesystem"]
```

---

## 🎯 Best Practices

### **Configuration Organization**
- **Single File**: Use for simple setups with <10 components
- **Multi-File**: Split by component type for larger configurations
- **Environment Specific**: Separate base config from environment overrides
- **Templates**: Start with templates and customize as needed

### **Security Best Practices**
- **Environment Variables**: Always use environment variables for API keys
- **No Hardcoded Secrets**: Never put secrets directly in configuration files
- **Minimal Permissions**: Configure only necessary access levels
- **Regular Rotation**: Implement API key rotation policies

### **Performance Optimization**
- **Memory Backends**: Use Redis for production, SQLite for development
- **Model Selection**: Choose appropriate models for each use case
- **Caching**: Enable caching for frequently accessed data
- **Resource Limits**: Set appropriate timeouts and token limits

### **Maintenance**
- **Validation**: Always validate configurations before deployment
- **Version Control**: Keep configurations in version control
- **Documentation**: Use templates with comments for team configurations
- **Regular Reviews**: Periodically review and optimize configurations

---

**LangSwarm V2's configuration system provides a modern, type-safe, and user-friendly way to configure complex AI applications with enterprise-grade features and comprehensive validation.**

# Migration Examples

This directory contains before/after examples showing how to migrate from multi-file to single-file configurations.

## Migration Overview

The migration from multi-file to single-file configuration involves:

1. **Consolidating** all configuration files into a single `langswarm.yaml`
2. **Simplifying** agent definitions using behavior-based system prompts
3. **Reducing** configuration complexity with smart defaults
4. **Maintaining** all existing functionality

## Example Migration

### Before: Multi-file Configuration (8 files)

**Current structure:**
```
example_mcp_config/
├── agents.yaml          # 25 lines
├── tools.yaml           # 40 lines  
├── workflows.yaml       # 30 lines
├── brokers.yaml         # 20 lines
├── queues.yaml          # 15 lines
├── registries.yaml      # 10 lines
├── plugins.yaml         # 8 lines
└── retrievers.yaml      # 12 lines
Total: 8 files, 160 lines
```

**agents.yaml:**
```yaml
agents:
  - id: "chat_response_agent"
    name: "Main Chat Response Agent"
    model: "gpt-4o"
    agent_type: "generic"
    system_prompt: |
      You are a helpful assistant. You help users with their questions and tasks.
      You are polite, informative, and try to provide accurate responses.
      
      You have access to the following tools:
      - filesystem: You can read files and list directories
      - github: You can interact with GitHub repositories
      
      Always be helpful and provide detailed explanations when needed.
    tools: ["filesystem", "github"]
    max_tokens: 4000
    temperature: 0.7
```

**tools.yaml:**
```yaml
tools:
  - id: "filesystem"
    type: "mcpfilesystem"
    local_mode: true
    settings:
      allowed_paths: ["."]
      max_file_size: "10MB"
      
  - id: "github"
    type: "mcpgithubtool"
    local_mode: true
    settings:
      default_branch: "main"
      auto_fork: false
```

**workflows.yaml:**
```yaml
workflows:
  - id: "main-workflow"
    name: "Main Processing Workflow"
    steps:
      - id: "process-input"
        agent: "chat_response_agent"
        input: "{{user_input}}"
        output:
          save_as: "response"
```

**brokers.yaml:**
```yaml
brokers:
  - id: "main-broker"
    type: "internal"
    settings:
      max_queue_size: 1000
```

**queues.yaml:**
```yaml
queues:
  - id: "main-queue"
    broker: "main-broker"
    settings:
      max_size: 500
```

**registries.yaml:**
```yaml
registries:
  - id: "tool-registry"
    type: "local"
    settings:
      cache_enabled: true
```

**plugins.yaml:**
```yaml
plugins:
  - id: "logging-plugin"
    type: "logging"
    settings:
      log_level: "INFO"
```

**retrievers.yaml:**
```yaml
retrievers:
  - id: "main-retriever"
    type: "chromadb"
    settings:
      collection_name: "main"
```

### After: Single-file Configuration (1 file)

**New structure:**
```
langswarm.yaml           # 45 lines, everything in one place
```

**langswarm.yaml:**
```yaml
version: "1.0"
project_name: "migrated-app"

# Core settings
langswarm:
  debug: false
  log_level: "INFO"

# Simplified agent definition
agents:
  - id: "chat_response_agent"
    name: "Main Chat Response Agent"
    model: "gpt-4o"
    behavior: "helpful"  # Auto-generates appropriate system prompt
    tools: ["filesystem", "github"]
    max_tokens: 4000
    temperature: 0.7

# Simplified tool configuration
tools:
  filesystem:
    local_mode: true
    settings:
      allowed_paths: ["."]
      max_file_size: "10MB"
      
  github:
    auto_configure: true  # Auto-detect from environment
    settings:
      default_branch: "main"
      auto_fork: false

# Workflow definition
workflows:
  - id: "main-workflow"
    name: "Main Processing Workflow"
    steps:
      - id: "process-input"
        agent: "chat_response_agent"
        input: "{{user_input}}"
        output:
          save_as: "response"

# Advanced configurations (only when needed)
advanced:
  brokers:
    - id: "main-broker"
      type: "internal"
      settings:
        max_queue_size: 1000
  
  queues:
    - id: "main-queue"
      broker: "main-broker"
      settings:
        max_size: 500
  
  registries:
    - id: "tool-registry"
      type: "local"
      settings:
        cache_enabled: true
  
  plugins:
    - id: "logging-plugin"
      type: "logging"
      settings:
        log_level: "INFO"
  
  retrievers:
    - id: "main-retriever"
      type: "chromadb"
      settings:
        collection_name: "main"
```

## Key Benefits of Migration

### 1. Dramatic Simplification
- **Files**: 8 files → 1 file
- **Lines**: 160 lines → 45 lines  
- **Complexity**: High → Low

### 2. Behavior-Based System Prompts
**Before:**
```yaml
system_prompt: |
  You are a helpful assistant. You help users with their questions and tasks.
  You are polite, informative, and try to provide accurate responses.
  
  You have access to the following tools:
  - filesystem: You can read files and list directories
  - github: You can interact with GitHub repositories
  
  Always be helpful and provide detailed explanations when needed.
```

**After:**
```yaml
behavior: "helpful"  # Auto-generates equivalent system prompt
```

### 3. Smart Configuration Defaults
**Before:**
```yaml
tools:
  - id: "filesystem"
    type: "mcpfilesystem"
    local_mode: true
    settings:
      allowed_paths: ["."]
```

**After:**
```yaml
tools:
  filesystem:
    local_mode: true  # Type auto-detected, smart defaults applied
    settings:
      allowed_paths: ["."]
```

### 4. Progressive Complexity
- **Basic configs**: Only specify what you need
- **Advanced configs**: Use `advanced:` section for complex setups
- **Gradual migration**: Can start simple and add complexity later

## Migration Process

### Automated Migration
```bash
# Use the built-in migration tool
langswarm migrate-config /path/to/current/config --output langswarm.yaml

# Validate the migrated configuration
langswarm validate-config langswarm.yaml
```

### Manual Migration Steps

1. **Create base structure**:
   ```yaml
   version: "1.0"
   project_name: "your-app-name"
   ```

2. **Migrate agents** (simplify system prompts):
   ```yaml
   agents:
     - id: "agent-id"
       behavior: "helpful"  # or "coding", "research", etc.
       # ... other settings
   ```

3. **Migrate tools** (use smart defaults):
   ```yaml
   tools:
     filesystem:
       local_mode: true
       # ... only specify non-default settings
   ```

4. **Migrate workflows**:
   ```yaml
   workflows:
     - id: "workflow-id"
       # ... copy existing workflow definition
   ```

5. **Move complex configs to advanced section**:
   ```yaml
   advanced:
     brokers: [...]
     queues: [...]
     # ... other advanced configs
   ```

## Validation

After migration, validate that:
- All agents are properly defined
- All tools are configured correctly
- Workflows reference existing agents
- No configuration errors exist

```bash
langswarm validate-config langswarm.yaml
```

## Rollback Strategy

If needed, you can convert back to multi-file configuration:

```bash
langswarm split-config langswarm.yaml --output-dir ./multi-file-config
```

This maintains the exact same functionality while providing the flexibility to use either approach.

## Next Steps

1. **Test** the migrated configuration
2. **Validate** all functionality works as expected
3. **Simplify** further by removing unnecessary settings
4. **Document** any custom configurations for your team 
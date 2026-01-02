# LangSwarm Simplified Configuration Strategy

## 🎯 **Goal: Simple by Default, Powerful When Needed**

We'll simplify configuration without sacrificing flexibility by:
1. **Minimal required fields** - Only what's absolutely necessary
2. **Smart defaults** - Sensible defaults for everything else
3. **Progressive disclosure** - Add complexity only when needed
4. **Template library** - Pre-built configs for common use cases

## 📝 **Minimal Configuration Examples**

### **1. Absolute Minimum (5 lines)**
```yaml
version: "2.0"
agents:
  - id: "assistant"
    provider: "openai"
    model: "gpt-3.5-turbo"
```

**What you get with these 5 lines:**
- ✅ Working AI assistant
- ✅ SQLite memory (automatic)
- ✅ Default system prompt
- ✅ Error handling
- ✅ Token tracking
- ✅ Conversation history

### **2. Common Use Case (8 lines)**
```yaml
version: "2.0"
agents:
  - id: "assistant"
    provider: "openai"
    model: "gpt-4"
    system_prompt: "You are a helpful coding assistant."
workflows:
  - "assistant -> user"
```

### **3. Multi-Agent (12 lines)**
```yaml
version: "2.0"
agents:
  - id: "researcher"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: "Research and gather information."
    
  - id: "writer"
    provider: "openai"
    model: "gpt-4"
    system_prompt: "Create polished content."
    
workflows:
  - "researcher -> writer -> user"
```

## 🧙 **Smart Defaults System**

### **Provider Defaults**
```yaml
# If you write this:
agents:
  - id: "assistant"
    model: "gpt-4"
    
# LangSwarm assumes:
agents:
  - id: "assistant"
    provider: "openai"  # Auto-detected from model name
    model: "gpt-4"
    temperature: 0.7
    max_tokens: null    # Use model default
    system_prompt: "You are a helpful AI assistant."
```

### **Memory Defaults**
```yaml
# No memory config = SQLite with smart defaults
# Equivalent to:
memory:
  backend: "sqlite"
  settings:
    persist_directory: "./langswarm_data"
    enable_embeddings: false
    ttl_seconds: 86400  # 24 hours
```

### **Security Defaults**
```yaml
# No security config = Safe defaults
# Equivalent to:
security:
  api_key_validation: true
  rate_limiting:
    enabled: true
    requests_per_minute: 60
  input_sanitization: true
  max_input_length: 10000
```

## 📚 **Template Library**

### **1. Simple Chatbot**
```yaml
# templates/chatbot.yaml
version: "2.0"
name: "Simple Chatbot"
agents:
  - id: "chatbot"
    model: "gpt-3.5-turbo"
    system_prompt: "You are a friendly chatbot."
```

### **2. Customer Support**
```yaml
# templates/customer-support.yaml
version: "2.0"
name: "Customer Support System"
agents:
  - id: "classifier"
    model: "gpt-3.5-turbo"
    system_prompt: "Classify customer inquiries: technical, billing, general."
    
  - id: "technical"
    model: "gpt-4"
    system_prompt: "Provide technical support."
    
  - id: "billing"
    model: "gpt-3.5-turbo"
    system_prompt: "Handle billing inquiries."
    
workflows:
  - "classifier -> (technical | billing) -> user"
```

### **3. Content Creation**
```yaml
# templates/content-creator.yaml
version: "2.0"
name: "Content Creation Pipeline"
agents:
  - id: "researcher"
    model: "gpt-3.5-turbo"
    tools: ["web_search"]
    
  - id: "writer"
    model: "gpt-4"
    
  - id: "editor"
    model: "gpt-3.5-turbo"
    
workflows:
  - "researcher -> writer -> editor -> user"
```

### **4. Code Assistant**
```yaml
# templates/code-assistant.yaml
version: "2.0"
name: "Coding Assistant"
agents:
  - id: "coder"
    model: "gpt-4"
    system_prompt: "Expert programmer. Write clean, tested code."
    tools: ["filesystem", "code_executor"]
```

## 🔄 **Progressive Disclosure**

### **Level 1: Beginner (Required Only)**
```yaml
version: "2.0"
agents:
  - id: "assistant"
    model: "gpt-4"
```

### **Level 2: Intermediate (Common Customizations)**
```yaml
version: "2.0"
agents:
  - id: "assistant"
    model: "gpt-4"
    system_prompt: "Custom instructions here"
    temperature: 0.8
    tools: ["web_search"]
    
workflows:
  - "assistant -> user"
  
memory:
  backend: "redis"  # Upgrade from SQLite
```

### **Level 3: Advanced (Full Control)**
```yaml
version: "2.0"
agents:
  - id: "assistant"
    provider: "openai"
    model: "gpt-4"
    system_prompt: "Custom instructions"
    temperature: 0.8
    max_tokens: 2000
    top_p: 0.95
    frequency_penalty: 0.5
    presence_penalty: 0.5
    tools: ["web_search", "code_executor"]
    memory_strategy: "conversation_buffer_window"
    
workflows:
  - id: "main"
    steps:
      - agent: "assistant"
        tools: ["web_search"]
        max_retries: 3
        timeout: 30
        
memory:
  backend: "redis"
  settings:
    host: "localhost"
    port: 6379
    ttl_seconds: 3600
    max_messages: 100
    
security:
  api_key_validation: true
  allowed_models: ["gpt-4", "gpt-3.5-turbo"]
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 20
```

## 🛠️ **Configuration Shortcuts**

### **1. Model Name Auto-Detection**
```yaml
# These are equivalent:
model: "gpt-4"          # Auto-detects OpenAI
model: "claude-3"       # Auto-detects Anthropic  
model: "gemini-pro"     # Auto-detects Google
```

### **2. Single-Line Workflows**
```yaml
# These are equivalent:
workflows:
  - "assistant -> user"
  
workflows:
  - id: "default"
    steps:
      - agent: "assistant"
        output:
          to: "user"
```

### **3. Tool Shortcuts**
```yaml
# These are equivalent:
tools: ["filesystem", "web_search"]

tools:
  filesystem:
    type: "mcp"
    local_mode: true
  web_search:
    type: "mcp"
    local_mode: true
```

## 🎯 **Implementation Strategy**

### **1. Config Validator with Defaults**
```python
class ConfigValidator:
    def validate_and_fill_defaults(self, config):
        # Auto-detect provider from model name
        if "provider" not in agent and "model" in agent:
            agent["provider"] = self.detect_provider(agent["model"])
            
        # Apply smart defaults
        agent.setdefault("temperature", 0.7)
        agent.setdefault("system_prompt", "You are a helpful AI assistant.")
        
        # Add default memory if not specified
        if "memory" not in config:
            config["memory"] = {
                "backend": "sqlite",
                "settings": {"persist_directory": "./langswarm_data"}
            }
```

### **2. Template Loader**
```python
class TemplateLoader:
    def load_template(self, template_name):
        # Load from templates directory
        template_path = f"templates/{template_name}.yaml"
        return load_yaml(template_path)
        
    def list_templates(self):
        return [
            "chatbot",
            "customer-support",
            "content-creator",
            "code-assistant",
            "rag-system",
            "multi-agent-debate"
        ]
```

### **3. Configuration Builder CLI**
```bash
# Interactive configuration builder
langswarm init

? What type of system? › 
  ○ Simple chatbot
  ○ Customer support
  ○ Content creation
  ○ Custom

? Which AI provider? ›
  ● OpenAI (recommended)
  ○ Anthropic
  ○ Google
  ○ Multiple providers

? Enable memory? (Y/n) › Yes

✅ Created langswarm.yaml with your configuration!
```

## 📊 **Before vs After**

### **Before: Complex Configuration**
```yaml
# 100+ lines of required configuration
version: "2.0"
agents:
  - id: "assistant"
    name: "General Assistant"
    provider: "openai"
    model: "gpt-3.5-turbo"
    api_key: "${OPENAI_API_KEY}"
    temperature: 0.7
    max_tokens: null
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
    stop_sequences: []
    system_prompt: "..."
    retry_config:
      max_retries: 3
      backoff_multiplier: 2
    timeout: 30
    # ... many more fields
```

### **After: Simple Configuration**
```yaml
# 5 lines minimum
version: "2.0"
agents:
  - id: "assistant"
    model: "gpt-3.5-turbo"
    system_prompt: "You are helpful."  # Optional
```

## ✅ **Benefits**

1. **Lower Barrier to Entry**: New users can start with 5 lines
2. **No Loss of Flexibility**: Power users can still configure everything
3. **Smart Defaults**: Sensible defaults based on best practices
4. **Template Library**: Pre-built configs for common use cases
5. **Progressive Complexity**: Add features as you learn
6. **Auto-Detection**: Provider detection from model names
7. **Shortcuts**: Single-line workflows and tool definitions

This approach maintains full backward compatibility while making LangSwarm much more approachable for new users.
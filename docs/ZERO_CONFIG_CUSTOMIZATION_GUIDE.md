# 🎛️ Zero-Config Agents Customization Guide

This guide shows you how to customize the default values used by the Zero-Config Agents system. The zero-config system provides intelligent defaults, but you can easily customize them to match your specific needs.

## 📍 **Overview: Where Defaults Live**

The zero-config system stores defaults in several key locations:

1. **Behavior Profiles** (`langswarm/core/defaults.py`) - Main customization point
2. **Base Configuration** (`langswarm/core/config.py`) - Fundamental defaults
3. **Tool Registry** (`langswarm/core/defaults.py`) - Available tools and properties
4. **Environment Detection** (`langswarm/core/detection.py`) - Model selection priorities

## 🎯 **Primary Location: Behavior Profiles**

**File: `langswarm/core/defaults.py`**  
**Lines: 89-148**

This is where you'll customize most defaults. The system includes 6 built-in behavior profiles:

### Current Behavior Profiles

```python
def _load_behavior_profiles(self) -> Dict[str, BehaviorProfile]:
    """Load predefined behavior profiles with optimal settings"""
    profiles = {
        "helpful": BehaviorProfile(
            name="Helpful Assistant",
            description="General-purpose helpful assistant for everyday tasks",
            preferred_models=["gpt-4o-mini", "claude-3-haiku-20240307", "gpt-4o"],
            max_tokens=4000,
            temperature=0.7,
            tools=["filesystem"],
            memory_need="medium",
            streaming=True,
            response_style="friendly",
            capabilities=["files"]
        ),
        
        "coding": BehaviorProfile(
            name="Coding Assistant",
            description="Programming assistant for code development and debugging",
            preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022", "gpt-4o-mini"],
            max_tokens=8000,
            temperature=0.1,
            tools=["filesystem", "github", "codebase_indexer"],
            memory_need="high",
            streaming=True,
            response_style="precise",
            capabilities=["files", "code", "analysis"]
        ),
        
        "research": BehaviorProfile(
            name="Research Assistant",
            description="Research assistant for information gathering and analysis",
            preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-pro"],
            max_tokens=6000,
            temperature=0.3,
            tools=["filesystem", "github", "aggregation", "consensus"],
            memory_need="high",
            streaming=True,
            response_style="analytical",
            capabilities=["files", "web", "memory", "analysis"]
        ),
        
        "creative": BehaviorProfile(
            name="Creative Assistant",
            description="Creative assistant for writing, brainstorming, and content generation",
            preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022", "gpt-4o-mini"],
            max_tokens=4000,
            temperature=0.8,
            tools=["filesystem", "files"],
            memory_need="medium",
            streaming=True,
            response_style="creative",
            capabilities=["files"]
        ),
        
        "analytical": BehaviorProfile(
            name="Analytical Assistant",
            description="Data analysis and logical reasoning assistant",
            preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-pro"],
            max_tokens=6000,
            temperature=0.2,
            tools=["filesystem", "aggregation", "multi_agent_reranking"],
            memory_need="high",
            streaming=False,  # Analysis often benefits from complete responses
            response_style="methodical",
            capabilities=["files", "analysis", "memory"]
        ),
        
        "support": BehaviorProfile(
            name="Support Assistant",
            description="Customer support assistant for help and troubleshooting",
            preferred_models=["gpt-4o-mini", "claude-3-haiku-20240307", "gpt-3.5-turbo"],
            max_tokens=3000,
            temperature=0.5,
            tools=["filesystem", "files"],
            memory_need="medium",
            streaming=True,
            response_style="patient",
            capabilities=["files"]
        )
    }
```

### BehaviorProfile Fields Explained

- **`name`**: Human-readable name for the behavior
- **`description`**: Brief description of the behavior's purpose
- **`preferred_models`**: List of models in order of preference
- **`max_tokens`**: Maximum tokens for responses
- **`temperature`**: Creativity level (0.0-1.0)
- **`tools`**: List of tools to auto-assign
- **`memory_need`**: "low", "medium", or "high" memory requirements
- **`streaming`**: Whether to enable streaming responses
- **`response_style`**: Style descriptor for system prompts
- **`capabilities`**: High-level capabilities this behavior provides

## 🔧 **Tool Registry Configuration**

**File: `langswarm/core/defaults.py`**  
**Lines: 176-228**

The tool registry defines available tools and their properties:

```python
def _load_tool_registry(self) -> Dict[str, Dict[str, Any]]:
    """Load registry of available tools and their capabilities"""
    return {
        "filesystem": {
            "type": "mcpfilesystem",
            "capabilities": ["files", "directories"],
            "resource_usage": "low",
            "always_available": True
        },
        "files": {
            "type": "files",
            "capabilities": ["files"],
            "resource_usage": "low",
            "always_available": True
        },
        "github": {
            "type": "mcpgithubtool",
            "capabilities": ["web", "code", "repositories"],
            "resource_usage": "medium",
            "requires_api": True
        },
        "codebase_indexer": {
            "type": "codebase_indexer",
            "capabilities": ["code", "analysis"],
            "resource_usage": "high",
            "requires_memory": True
        },
        "aggregation": {
            "type": "aggregation",
            "capabilities": ["analysis", "web"],
            "resource_usage": "medium",
            "requires_api": True
        },
        "consensus": {
            "type": "consensus",
            "capabilities": ["analysis"],
            "resource_usage": "high",
            "requires_memory": True
        },
        "multi_agent_reranking": {
            "type": "multi_agent_reranking",
            "capabilities": ["analysis"],
            "resource_usage": "high",
            "requires_api": True
        },
        "dynamic_forms": {
            "type": "dynamic_forms",
            "capabilities": ["forms", "ui"],
            "resource_usage": "low",
            "always_available": True
        },
        "message_queue_publisher": {
            "type": "message_queue_publisher",
            "capabilities": ["messaging"],
            "resource_usage": "medium",
            "requires_queue": True
        }
    }
```

### Tool Registry Fields Explained

- **`type`**: The tool implementation type
- **`capabilities`**: What high-level capabilities this tool provides
- **`resource_usage`**: "low", "medium", or "high" resource requirements
- **`always_available`**: Whether the tool is always available
- **`requires_api`**: Whether the tool needs API access
- **`requires_memory`**: Whether the tool needs significant memory
- **`requires_queue`**: Whether the tool needs message queue access

## 📋 **Base Configuration Defaults**

**File: `langswarm/core/config.py`**  
**Lines: 82-98**

These are the fundamental defaults applied to all agents:

```python
@dataclass
class AgentConfig:
    """Unified agent configuration"""
    id: str
    name: Optional[str] = None
    model: str = "gpt-4o"              # Default model
    behavior: Optional[str] = None
    system_prompt: Optional[str] = None
    agent_type: str = "generic"        # Default agent type
    tools: List[str] = field(default_factory=list)
    memory: Union[bool, Dict[str, Any]] = False  # Default memory setting
    streaming: bool = False            # Default streaming setting
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    response_format: Optional[str] = None
```

## 🎯 **Model Selection Priorities**

**File: `langswarm/core/detection.py`**  
**Lines: 440-460**

The system prioritizes models in this order:

```python
def _select_optimal_model(self, available_models: List[str]) -> str:
    """Choose the best available model based on capabilities and cost"""
    
    # Model preference order: capability > cost > speed > availability
    model_priority = [
        # Premium models (best capability)
        "gpt-4o",
        "claude-3-5-sonnet-20241022",
        "gpt-4",
        "claude-3-opus-20240229",
        
        # Balanced models (good capability/cost)
        "gpt-4o-mini",
        "claude-3-5-haiku-20241022",
        "gpt-4-turbo",
        "claude-3-sonnet-20240229",
        "gemini-1.5-pro",
        
        # Fast/cheap models
        "claude-3-haiku-20240307",
        "gpt-3.5-turbo",
        "gemini-pro",
        "gemini-1.5-flash",
        
        # Local models (privacy/cost)
        "ollama/llama2",
        "ollama/mistral",
        "ollama/codellama",
        "local/llama-2-7b-chat",
    ]
```

## 🛠 **Customization Examples**

### 1. **Add a Custom Behavior Profile**

In `langswarm/core/defaults.py`, add to the `_load_behavior_profiles()` method:

```python
def _load_behavior_profiles(self) -> Dict[str, BehaviorProfile]:
    profiles = {
        # ... existing profiles ...
        
        # ADD YOUR CUSTOM PROFILE:
        "data_scientist": BehaviorProfile(
            name="Data Science Assistant",
            description="Specialized for data analysis and ML tasks",
            preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022"],
            max_tokens=8000,
            temperature=0.2,
            tools=["filesystem", "aggregation", "multi_agent_reranking"],
            memory_need="high",
            streaming=False,
            response_style="analytical",
            capabilities=["files", "analysis", "memory"]
        ),
        
        "translator": BehaviorProfile(
            name="Translation Assistant",
            description="Specialized for language translation tasks",
            preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022"],
            max_tokens=4000,
            temperature=0.3,
            tools=["filesystem", "files"],
            memory_need="medium",
            streaming=True,
            response_style="precise",
            capabilities=["files"]
        ),
    }
```

### 2. **Modify Existing Behavior Defaults**

Change the coding behavior to use different defaults:

```python
"coding": BehaviorProfile(
    name="Coding Assistant",
    description="Programming assistant for code development and debugging",
    preferred_models=["claude-3-5-sonnet-20241022", "gpt-4o"],  # Prefer Claude
    max_tokens=12000,        # Increase token limit
    temperature=0.05,        # More deterministic
    tools=["filesystem", "github", "codebase_indexer", "dynamic_forms"],  # Add forms
    memory_need="high",
    streaming=True,
    response_style="precise",
    capabilities=["files", "code", "analysis", "forms"]  # Add forms capability
),
```

### 3. **Add a Custom Tool**

In the `_load_tool_registry()` method:

```python
def _load_tool_registry(self) -> Dict[str, Dict[str, Any]]:
    return {
        # ... existing tools ...
        
        # ADD YOUR CUSTOM TOOL:
        "database_connector": {
            "type": "database_connector",
            "capabilities": ["database", "sql"],
            "resource_usage": "medium",
            "requires_api": True
        },
        
        "image_generator": {
            "type": "image_generator",
            "capabilities": ["images", "generation"],
            "resource_usage": "high",
            "requires_api": True
        },
        
        "email_sender": {
            "type": "email_sender",
            "capabilities": ["email", "communication"],
            "resource_usage": "low",
            "requires_api": True
        },
    }
```

### 4. **Change Default Model**

In `langswarm/core/config.py`, line 87:

```python
model: str = "claude-3-5-sonnet-20241022"  # Instead of "gpt-4o"
```

### 5. **Modify Model Selection Priority**

In `langswarm/core/detection.py`, reorder the `model_priority` list:

```python
model_priority = [
    # Put your preferred models first
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022", 
    "gpt-4o",
    "gpt-4o-mini",
    # ... rest of the models
]
```

### 6. **Change Default Memory Settings**

In `langswarm/core/config.py`:

```python
memory: Union[bool, Dict[str, Any]] = True  # Enable memory by default
```

### 7. **Adjust Temperature Defaults**

Make all behaviors more conservative:

```python
# In each BehaviorProfile, reduce temperature by 0.2
temperature=0.5,  # Instead of 0.7 for helpful
temperature=0.0,  # Instead of 0.1 for coding (maximum determinism)
temperature=0.1,  # Instead of 0.3 for research
```

## 🎯 **Advanced Customization**

### Custom Profile Loading

You can extend the system to load custom profiles from external files. In `_load_custom_profiles()`:

```python
def _load_custom_profiles(self) -> Dict[str, BehaviorProfile]:
    """Load custom behavior profiles from configuration"""
    custom_profiles = {}
    
    # Load from YAML file
    custom_file = os.getenv("LANGSWARM_CUSTOM_PROFILES", "custom_profiles.yaml")
    if os.path.exists(custom_file):
        with open(custom_file, 'r') as f:
            data = yaml.safe_load(f)
            
        for profile_id, profile_data in data.get("profiles", {}).items():
            custom_profiles[profile_id] = BehaviorProfile(
                name=profile_data["name"],
                description=profile_data["description"],
                preferred_models=profile_data["preferred_models"],
                max_tokens=profile_data["max_tokens"],
                temperature=profile_data["temperature"],
                tools=profile_data["tools"],
                memory_need=profile_data["memory_need"],
                streaming=profile_data["streaming"],
                response_style=profile_data["response_style"],
                capabilities=profile_data["capabilities"]
            )
    
    return custom_profiles
```

Then create `custom_profiles.yaml`:

```yaml
profiles:
  academic_writer:
    name: "Academic Writing Assistant"
    description: "Specialized for academic paper writing and research"
    preferred_models: ["gpt-4o", "claude-3-5-sonnet-20241022"]
    max_tokens: 8000
    temperature: 0.4
    tools: ["filesystem", "github", "aggregation"]
    memory_need: "high"
    streaming: true
    response_style: "academic"
    capabilities: ["files", "research", "writing"]
```

## 🧪 **Testing Your Changes**

### Quick Test

After making changes, test them:

```bash
cd /Users/alexanderekdahl/Docker/LangSwarm
python -c "
from langswarm.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader()
agent = loader.create_zero_config_agent('test', 'helpful')
print(f'Model: {agent.model}')
print(f'Tools: {agent.tools}')
print(f'Temperature: {agent.temperature}')
print(f'Max Tokens: {agent.max_tokens}')
"
```

### Full Demo Test

Run the comprehensive demo:

```bash
python demos/demo_zero_config_agents.py
```

### Test Custom Behavior

If you added a custom behavior:

```bash
python -c "
from langswarm.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader()
behaviors = loader.get_available_behaviors()
print('Available behaviors:', behaviors)

if 'data_scientist' in behaviors:
    agent = loader.create_zero_config_agent('test', 'data_scientist')
    print(f'Data Scientist Agent - Model: {agent.model}, Tools: {agent.tools}')
"
```

### Test Specific Configuration

Create a test config file:

```yaml
# test_config.yaml
version: "1.0"
agents:
  - id: "test-agent"
    behavior: "coding"
```

```bash
python -c "
from langswarm.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader()
config = loader.load_single_config('test_config.yaml')
print(f'Agent: {config.agents[0].id}')
print(f'Model: {config.agents[0].model}')
print(f'Tools: {config.agents[0].tools}')
"
```

## 📝 **Best Practices**

### 1. **Backup Before Changes**
```bash
cp langswarm/core/defaults.py langswarm/core/defaults.py.backup
cp langswarm/core/config.py langswarm/core/config.py.backup
```

### 2. **Test Changes Incrementally**
- Modify one behavior at a time
- Test each change before moving to the next
- Keep notes of what you changed

### 3. **Validate Model Names**
Ensure model names in `preferred_models` match actual available models:

```python
# Test model availability
from langswarm.core.detection import detect_environment
capabilities = detect_environment()
print("Available models:", capabilities.available_models)
```

### 4. **Document Your Changes**
Add comments explaining your customizations:

```python
"coding": BehaviorProfile(
    # CUSTOMIZATION: Increased tokens for complex coding tasks
    max_tokens=12000,  # Default was 8000
    
    # CUSTOMIZATION: Added forms tool for UI development
    tools=["filesystem", "github", "codebase_indexer", "dynamic_forms"],
    
    # ... rest of profile
),
```

### 5. **Version Control**
Commit your changes to track what you've modified:

```bash
git add langswarm/core/defaults.py
git commit -m "Customize zero-config defaults: added data_scientist behavior"
```

## 🚨 **Common Issues and Solutions**

### Issue 1: Model Not Found
**Problem**: Custom model in `preferred_models` not available
**Solution**: Check available models with detection system, use fallback models

### Issue 2: Tool Not Found
**Problem**: Custom tool in behavior profile not registered
**Solution**: Add tool to `_load_tool_registry()` method first

### Issue 3: Import Errors
**Problem**: Circular import when adding custom logic
**Solution**: Use late imports or move logic to separate module

### Issue 4: Temperature Out of Range
**Problem**: Invalid temperature values
**Solution**: Ensure temperature is between 0.0 and 1.0

### Issue 5: Memory Configuration Errors
**Problem**: Invalid memory configuration
**Solution**: Use boolean `True`/`False` or proper dict format

## 🎯 **Configuration File Override**

You can also override defaults in your config file without modifying code:

```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: "custom-coder"
    behavior: "coding"
    model: "claude-3-5-sonnet-20241022"  # Override default model
    temperature: 0.05                    # Override default temperature
    max_tokens: 12000                    # Override default tokens
    tools: ["filesystem", "github", "dynamic_forms"]  # Override default tools
```

This allows per-agent customization without changing the global defaults.

## 📚 **Related Documentation**

- [Zero-Config Agents Implementation Guide](./simplification/02-zero-config-agents.md)
- [Zero-Config Examples](./simplification/examples/zero-config-examples.yaml)
- [Single Configuration File Guide](./simplification/01-single-configuration-file.md)

## 🎉 **Summary**

The zero-config system is highly customizable while maintaining its simplicity:

1. **Edit behavior profiles** in `defaults.py` for most customizations
2. **Add custom tools** to the tool registry
3. **Modify base defaults** in `config.py` for fundamental changes
4. **Adjust model priorities** in `detection.py`
5. **Test thoroughly** after each change
6. **Use configuration files** for per-agent overrides

With these customization options, you can tailor the zero-config system to perfectly match your specific use cases while maintaining the revolutionary simplicity that makes it so powerful! 🚀 
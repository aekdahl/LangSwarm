# Zero-Config Agents

**Status**: 🚧 **IN PROGRESS**  
**Priority**: HIGH  
**Impact**: Reduces agent setup from 15 lines to 1 line, eliminates 90% of configuration errors

## Problem Statement

Even with the unified configuration file, creating agents still requires significant configuration:

```yaml
# Current: Still complex
agents:
  - id: "my-agent"
    name: "My Assistant"
    model: "gpt-4o"
    behavior: "helpful"
    tools: ["filesystem"]
    memory: true
    streaming: false
    max_tokens: 4000
    temperature: 0.7
```

### Current Pain Points

1. **Model Selection Complexity**: Users must know which models are available
2. **Provider Configuration**: Setting up API keys and endpoints manually
3. **Tool Discovery**: Manual specification of which tools to include
4. **Parameter Tuning**: Guessing optimal values for temperature, max_tokens, etc.
5. **Environment Mismatch**: Configuration doesn't adapt to available resources

## Solution Design

### Zero-Config Agent Creation

Enable agents to be created with minimal specification:

```yaml
# Level 0: Absolute Minimum (1 line)
agents:
  - id: "assistant"

# Level 1: Behavior-Driven (2 lines)  
agents:
  - id: "assistant"
    behavior: "coding"

# Level 2: Capability-Focused (3 lines)
agents:
  - id: "assistant"
    behavior: "helpful"
    capabilities: ["files", "web", "memory"]
```

### Intelligent Auto-Detection

The system automatically detects and configures:

1. **Available Models**: Scan environment for API keys and endpoints
2. **Optimal Settings**: Choose best defaults based on use case
3. **Tool Capabilities**: Auto-enable relevant tools based on behavior
4. **Resource Limits**: Adapt to system capabilities and quotas

## Implementation Approach

### Phase 1: Environment Detection ✅ **IN PROGRESS**

1. **API Key Detection**: Scan for OpenAI, Anthropic, Google, etc. keys
2. **Model Availability**: Test which models are accessible
3. **Resource Detection**: Check system memory, GPU availability
4. **Network Capabilities**: Detect internet access and API endpoints

### Phase 2: Smart Defaults 

1. **Model Selection Algorithm**: Choose optimal model based on behavior and availability
2. **Parameter Optimization**: Use behavior-specific optimal settings
3. **Tool Auto-Assignment**: Map behaviors to relevant tool sets
4. **Memory Configuration**: Auto-configure based on behavior and resources

### Phase 3: Minimal Syntax

1. **Single-ID Creation**: `agents: ["assistant"]` syntax
2. **Capability-Based Configuration**: `capabilities: ["files"]` auto-expands
3. **Environment-Aware Loading**: Different configs for dev/staging/prod
4. **Progressive Enhancement**: Start minimal, add complexity as needed

## Technical Implementation

### Environment Detection System

```python
# langswarm/core/detection.py

@dataclass
class EnvironmentCapabilities:
    """Detected environment capabilities"""
    available_models: List[str]
    preferred_model: str
    api_endpoints: Dict[str, str]
    system_memory: int
    has_gpu: bool
    internet_access: bool
    max_concurrent_requests: int

class EnvironmentDetector:
    """Auto-detect available models and optimal configurations"""
    
    def detect_capabilities(self) -> EnvironmentCapabilities:
        """Scan environment and return available capabilities"""
        return EnvironmentCapabilities(
            available_models=self._detect_available_models(),
            preferred_model=self._select_optimal_model(),
            api_endpoints=self._detect_api_endpoints(),
            system_memory=self._get_system_memory(),
            has_gpu=self._check_gpu_availability(),
            internet_access=self._test_internet_connectivity(),
            max_concurrent_requests=self._calculate_safe_concurrency()
        )
    
    def _detect_available_models(self) -> List[str]:
        """Test which models are accessible via API keys"""
        available = []
        
        # OpenAI models
        if os.getenv("OPENAI_API_KEY"):
            available.extend(["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
        
        # Anthropic models  
        if os.getenv("ANTHROPIC_API_KEY"):
            available.extend(["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"])
        
        # Google models
        if os.getenv("GOOGLE_API_KEY"):
            available.extend(["gemini-pro", "gemini-pro-vision"])
        
        # Local models (Ollama, etc.)
        if self._check_local_models():
            available.extend(["llama2", "mistral", "codellama"])
        
        return available
    
    def _select_optimal_model(self) -> str:
        """Choose the best available model based on capabilities and cost"""
        available = self._detect_available_models()
        
        # Preference order: capability > cost > speed
        model_priority = [
            "gpt-4o",                    # Best overall
            "claude-3-5-sonnet-20241022", # Great reasoning
            "gpt-4o-mini",               # Good balance
            "claude-3-haiku-20240307",   # Fast and cheap
            "gpt-3.5-turbo",             # Fallback
            "gemini-pro",                # Alternative
            "llama2"                     # Local fallback
        ]
        
        for model in model_priority:
            if model in available:
                return model
        
        raise EnvironmentError("No supported models found. Please configure API keys.")
```

### Smart Defaults System

```python
# langswarm/core/defaults.py

class SmartDefaults:
    """Generate optimal configuration based on behavior and environment"""
    
    def __init__(self, capabilities: EnvironmentCapabilities):
        self.capabilities = capabilities
    
    def generate_agent_config(self, agent_id: str, behavior: str = "helpful") -> AgentConfig:
        """Generate complete agent configuration from minimal input"""
        
        # Select optimal model for behavior
        model = self._select_behavior_model(behavior)
        
        # Get behavior-specific parameters
        params = self._get_behavior_parameters(behavior)
        
        # Auto-select tools based on behavior
        tools = self._select_behavior_tools(behavior)
        
        # Configure memory based on behavior and resources
        memory_config = self._configure_memory(behavior)
        
        return AgentConfig(
            id=agent_id,
            name=self._generate_agent_name(agent_id, behavior),
            model=model,
            behavior=behavior,
            tools=tools,
            memory=memory_config,
            streaming=self._should_enable_streaming(behavior),
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            system_prompt=None  # Generated by behavior system
        )
    
    def _select_behavior_model(self, behavior: str) -> str:
        """Choose optimal model for specific behavior"""
        behavior_models = {
            "coding": ["gpt-4o", "claude-3-5-sonnet-20241022", "gpt-4o-mini"],
            "research": ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-pro"],
            "creative": ["gpt-4o", "claude-3-5-sonnet-20241022", "gpt-4o-mini"],
            "analytical": ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-pro"],
            "helpful": ["gpt-4o-mini", "gpt-4o", "claude-3-haiku-20240307"],
            "support": ["gpt-4o-mini", "claude-3-haiku-20240307", "gpt-3.5-turbo"]
        }
        
        preferred = behavior_models.get(behavior, behavior_models["helpful"])
        available = self.capabilities.available_models
        
        for model in preferred:
            if model in available:
                return model
        
        return self.capabilities.preferred_model
    
    def _get_behavior_parameters(self, behavior: str) -> Dict[str, Any]:
        """Get optimal parameters for behavior"""
        params = {
            "coding": {"max_tokens": 8000, "temperature": 0.1},
            "research": {"max_tokens": 6000, "temperature": 0.3},
            "creative": {"max_tokens": 4000, "temperature": 0.8},
            "analytical": {"max_tokens": 6000, "temperature": 0.2},
            "helpful": {"max_tokens": 4000, "temperature": 0.7},
            "support": {"max_tokens": 3000, "temperature": 0.5}
        }
        
        return params.get(behavior, params["helpful"])
    
    def _select_behavior_tools(self, behavior: str) -> List[str]:
        """Auto-select tools based on behavior"""
        behavior_tools = {
            "coding": ["filesystem", "github", "codebase_indexer"],
            "research": ["filesystem", "github", "aggregation", "consensus"],
            "creative": ["filesystem", "files"],
            "analytical": ["filesystem", "aggregation", "multi_agent_reranking"],
            "helpful": ["filesystem"],
            "support": ["filesystem", "files"]
        }
        
        # Filter tools based on what's actually available
        requested_tools = behavior_tools.get(behavior, ["filesystem"])
        available_tools = self._get_available_tools()
        
        return [tool for tool in requested_tools if tool in available_tools]
    
    def _configure_memory(self, behavior: str) -> Union[bool, Dict[str, Any]]:
        """Configure memory based on behavior and system resources"""
        memory_needs = {
            "coding": "high",      # Need context across files
            "research": "high",    # Need to remember findings
            "creative": "medium",  # Some context helpful
            "analytical": "high",  # Need data persistence
            "helpful": "medium",   # Basic conversation memory
            "support": "medium"    # Session continuity
        }
        
        need_level = memory_needs.get(behavior, "medium")
        
        if need_level == "high" and self.capabilities.system_memory > 8000:  # 8GB+
            return {
                "enabled": True,
                "backend": "auto",
                "settings": {"max_memory_size": "500MB"}
            }
        elif need_level in ["high", "medium"] and self.capabilities.system_memory > 4000:  # 4GB+
            return {
                "enabled": True,
                "backend": "auto", 
                "settings": {"max_memory_size": "100MB"}
            }
        elif need_level == "medium":
            return True  # Basic memory
        else:
            return False  # No memory for resource-constrained environments
```

### Enhanced Configuration Loader

```python
# Extend langswarm/core/config.py

class LangSwarmConfigLoader:
    """Enhanced loader with zero-config agent support"""
    
    def __init__(self, config_path="."):
        super().__init__(config_path)
        self.detector = EnvironmentDetector()
        self.capabilities = None
        self.smart_defaults = None
    
    def _ensure_capabilities_detected(self):
        """Lazy-load environment detection"""
        if self.capabilities is None:
            self.capabilities = self.detector.detect_capabilities()
            self.smart_defaults = SmartDefaults(self.capabilities)
    
    def _process_zero_config_agents(self, agents_config: List[Any]) -> List[AgentConfig]:
        """Process agents with zero-config enhancement"""
        self._ensure_capabilities_detected()
        
        processed_agents = []
        
        for agent_spec in agents_config:
            if isinstance(agent_spec, str):
                # Minimal syntax: agents: ["assistant"]
                agent_config = self.smart_defaults.generate_agent_config(
                    agent_id=agent_spec,
                    behavior="helpful"
                )
            elif isinstance(agent_spec, dict):
                agent_id = agent_spec["id"]
                behavior = agent_spec.get("behavior", "helpful")
                
                # Generate smart defaults first
                agent_config = self.smart_defaults.generate_agent_config(agent_id, behavior)
                
                # Override with any explicitly provided values
                for key, value in agent_spec.items():
                    if hasattr(agent_config, key) and value is not None:
                        setattr(agent_config, key, value)
                
                # Handle capability-based tool selection
                if "capabilities" in agent_spec:
                    agent_config.tools = self._expand_capabilities(agent_spec["capabilities"])
            
            processed_agents.append(agent_config)
        
        return processed_agents
    
    def _expand_capabilities(self, capabilities: List[str]) -> List[str]:
        """Expand capability names to actual tool IDs"""
        capability_map = {
            "files": ["filesystem", "files"],
            "web": ["github", "aggregation"],
            "memory": ["memory"],  # Handled separately
            "code": ["filesystem", "github", "codebase_indexer"],
            "analysis": ["aggregation", "consensus", "multi_agent_reranking"],
            "forms": ["dynamic_forms"],
                            "messaging": ["message_queue_publisher", "message_queue_consumer"]
        }
        
        tools = []
        for capability in capabilities:
            if capability in capability_map:
                tools.extend(capability_map[capability])
            else:
                # Assume it's a direct tool name
                tools.append(capability)
        
        # Remove duplicates and filter available tools
        available_tools = self._get_available_tools()
        return list(set(tool for tool in tools if tool in available_tools))
```

## Configuration Examples

### Ultra-Minimal (1 line)
```yaml
# Zero configuration - everything auto-detected
agents: ["assistant"]
```

**Auto-Generated:**
- Model: Best available (gpt-4o, claude-3-5-sonnet, etc.)
- Behavior: "helpful" (default)
- Tools: ["filesystem"] (safe default)
- Memory: Auto-configured based on system resources
- Parameters: Optimal defaults for helpful behavior

### Behavior-Driven (2 lines)
```yaml
agents:
  - id: "coder"
    behavior: "coding"
```

**Auto-Generated:**
- Model: Best coding model (gpt-4o for complex reasoning)
- Tools: ["filesystem", "github", "codebase_indexer"]
- Memory: High memory allocation for code context
- Parameters: Low temperature (0.1) for precise code
- Max tokens: 8000 for longer code completions

### Capability-Based (3 lines)
```yaml
agents:
  - id: "researcher"
    behavior: "research"
    capabilities: ["files", "web", "memory"]
```

**Auto-Generated:**
- Model: Best research model (gpt-4o, claude-3-5-sonnet)
- Tools: ["filesystem", "files", "github", "aggregation", "memory"]
- Memory: Persistent memory backend for research continuity
- Parameters: Medium temperature (0.3) for balanced creativity
- Max tokens: 6000 for comprehensive responses

### Environment-Adaptive
```yaml
# Development environment
agents:
  - id: "dev-assistant"
    behavior: "coding"
    # Auto-detects: Local models, unlimited memory, all tools

# Production environment  
agents:
  - id: "prod-assistant"
    behavior: "helpful"
    # Auto-detects: API models, limited memory, essential tools only
```

## Smart Detection Logic

### Model Selection Algorithm

1. **Detect Available Models**:
   - Check API keys (OpenAI, Anthropic, Google)
   - Test local model endpoints (Ollama, LM Studio)
   - Validate connectivity and quotas

2. **Behavior-Model Matching**:
   - Coding: Prefer models with strong reasoning (gpt-4o, claude-3-5-sonnet)
   - Creative: Prefer models with high creativity (gpt-4o, claude-3-5-sonnet)
   - Support: Prefer fast, cost-effective models (gpt-4o-mini, claude-3-haiku)

3. **Fallback Strategy**:
   - Primary: Best available model for behavior
   - Secondary: Best available model overall
   - Tertiary: Most cost-effective available model
   - Emergency: Local model if available

### Resource-Aware Configuration

```yaml
# High-resource environment (16GB+ RAM, good internet)
agents:
  - id: "assistant"
    # Auto-configures:
    # - model: "gpt-4o"
    # - memory: 500MB persistent storage
    # - streaming: true
    # - max_concurrent: 10

# Low-resource environment (4GB RAM, limited internet)  
agents:
  - id: "assistant"
    # Auto-configures:
    # - model: "gpt-4o-mini"
    # - memory: 50MB basic memory
    # - streaming: false
    # - max_concurrent: 2
```

## Environment Variables

### API Configuration
```bash
# Auto-detected by Zero-Config system
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Optional: Override defaults
export LANGSWARM_DEFAULT_MODEL="gpt-4o-mini"
export LANGSWARM_MAX_MEMORY="100MB"
export LANGSWARM_ENVIRONMENT="production"
```

### Development vs Production
```bash
# Development - enables debug features
export LANGSWARM_ENVIRONMENT="development"
# - Enables all available tools
# - Uses larger context windows
# - Enables debug logging

# Production - optimizes for efficiency  
export LANGSWARM_ENVIRONMENT="production"
# - Uses only essential tools
# - Optimizes for cost and speed
# - Minimal logging
```

## Migration from Current System

### Before (15 lines)
```yaml
agents:
  - id: "coding-assistant"
    name: "Coding Assistant"
    model: "gpt-4o"
    behavior: "coding"
    agent_type: "generic"
    tools: ["filesystem", "github"]
    memory: true
    streaming: true
    max_tokens: 8000
    temperature: 0.1
    response_format: null
    system_prompt: |
      You are a coding assistant...
      [50+ lines of prompt]
```

### After (1-3 lines)
```yaml
# Option 1: Absolute minimum
agents: ["coding-assistant"]

# Option 2: Behavior-driven
agents:
  - id: "coding-assistant"
    behavior: "coding"

# Option 3: Capability-focused
agents:
  - id: "coding-assistant"
    behavior: "coding"
    capabilities: ["files", "code"]
```

## Implementation Timeline

- ✅ **Week 1**: Environment detection system
- 🚧 **Week 2**: Smart defaults implementation  
- ⏳ **Week 3**: Minimal syntax support
- ⏳ **Week 4**: Capability-based expansion
- ⏳ **Week 5**: Testing and validation
- ⏳ **Week 6**: Documentation and examples

## Success Metrics

### Quantitative Targets
- **Configuration Lines**: 15 lines → 1-3 lines (80-95% reduction)
- **Setup Time**: 15 minutes → 30 seconds (97% reduction)
- **Configuration Errors**: 90% reduction through auto-detection
- **Time to First Agent**: 2 minutes → 10 seconds

### Qualitative Goals
- **Zero Learning Curve**: Works without reading documentation
- **Environment Adaptive**: Same config works across dev/staging/prod
- **Intelligent Defaults**: Optimal settings without tuning
- **Progressive Enhancement**: Start simple, add complexity as needed

## Related Documents

- [Single Configuration File](./01-single-configuration-file.md) (Foundation)
- [Smart Tool Auto-Discovery](./03-smart-tool-auto-discovery.md) (Next Priority)
- [Zero-Config Examples](./examples/zero-config-examples.yaml)

## Impact Summary

Zero-Config Agents represents a **revolutionary simplification** in AI agent creation:

🎯 **Primary Goals:**
- **Setup Time**: 15 minutes → 30 seconds
- **Configuration Complexity**: 15 lines → 1 line  
- **Learning Curve**: Hours → Zero (works immediately)
- **Environment Adaptation**: Manual → Automatic

🚀 **Key Innovations:**
- **Auto-Detection**: Scans environment and selects optimal configurations
- **Behavior-Driven**: Single `behavior` parameter drives all settings
- **Resource-Aware**: Adapts to system capabilities automatically  
- **Progressive Complexity**: Start with 1 line, enhance as needed

💯 **100% Backward Compatibility**: Existing detailed configurations continue to work while new projects benefit from zero-config simplicity.

This creates the foundation for true "plug-and-play" AI agents that work out of the box in any environment. 
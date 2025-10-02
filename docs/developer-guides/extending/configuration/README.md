# Extending LangSwarm V2 Configuration System

**Complete guide for extending and customizing the V2 configuration system**

## 🎯 Overview

LangSwarm V2's configuration system is designed for extensibility, allowing developers to add custom configuration schemas, validation rules, loaders, and utilities while maintaining type safety and integration with the core system.

**Extension Capabilities:**
- **Custom Configuration Schemas**: Add new configuration sections and types
- **Custom Validation Rules**: Implement domain-specific validation logic
- **Custom Configuration Loaders**: Support additional file formats and sources
- **Custom Templates**: Create reusable configuration templates
- **Custom Optimization Rules**: Add configuration optimization analysis
- **Integration Hooks**: Integrate with external configuration systems

---

## 🏗️ Configuration Schema Extension

### **Adding Custom Configuration Sections**

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from langswarm.core.config.schema import LangSwarmConfig
from langswarm.core.config.validation import ValidationIssue

@dataclass
class CustomIntegrationConfig:
    """Custom integration configuration"""
    
    enabled: bool = False
    provider: str = ""
    api_endpoint: str = ""
    timeout_seconds: int = 30
    retry_count: int = 3
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    def validate(self) -> List[ValidationIssue]:
        """Validate custom integration configuration"""
        issues = []
        
        if self.enabled and not self.provider:
            issues.append(ValidationIssue(
                severity="ERROR",
                message="Provider is required when integration is enabled",
                component="custom_integration.provider",
                suggestion="Set provider name or disable integration",
                category="configuration"
            ))
        
        if self.enabled and not self.api_endpoint:
            issues.append(ValidationIssue(
                severity="ERROR", 
                message="API endpoint is required when integration is enabled",
                component="custom_integration.api_endpoint",
                suggestion="Set API endpoint URL",
                category="configuration"
            ))
        
        if self.timeout_seconds <= 0:
            issues.append(ValidationIssue(
                severity="WARNING",
                message="Timeout should be positive",
                component="custom_integration.timeout_seconds",
                suggestion="Set timeout to positive value (e.g., 30)",
                category="performance"
            ))
        
        return issues

# Extend main configuration
@dataclass
class ExtendedLangSwarmConfig(LangSwarmConfig):
    """Extended configuration with custom sections"""
    
    custom_integration: CustomIntegrationConfig = field(default_factory=CustomIntegrationConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    
    def validate(self) -> Tuple[bool, List[ValidationIssue]]:
        """Extended validation including custom sections"""
        # Run base validation
        is_valid, issues = super().validate()
        
        # Add custom validation
        custom_issues = []
        custom_issues.extend(self.custom_integration.validate())
        custom_issues.extend(self.monitoring.validate())
        custom_issues.extend(self.deployment.validate())
        
        # Combine issues
        all_issues = issues + custom_issues
        overall_valid = is_valid and not any(
            issue.severity == "ERROR" for issue in custom_issues
        )
        
        return overall_valid, all_issues
```

### **Custom Configuration Usage**

```yaml
# extended_config.yaml
agents:
  - id: "main_agent"
    name: "Main Agent"
    provider: "openai"
    model: "gpt-4"

custom_integration:
  enabled: true
  provider: "slack"
  api_endpoint: "https://hooks.slack.com/services/..."
  timeout_seconds: 30
  custom_headers:
    "X-Custom-Header": "value"

monitoring:
  enabled: true
  metrics_endpoint: "http://prometheus:9090"
  alert_webhook: "https://alerts.example.com/webhook"

deployment:
  environment: "production"
  replicas: 3
  resource_limits:
    cpu: "2"
    memory: "4Gi"
```

```python
# Load extended configuration
from langswarm.core.config.loaders import ConfigurationLoader

loader = ConfigurationLoader(config_class=ExtendedLangSwarmConfig)
config = loader.load("extended_config.yaml")

# Access custom configuration
if config.custom_integration.enabled:
    print(f"Integration: {config.custom_integration.provider}")
    print(f"Endpoint: {config.custom_integration.api_endpoint}")

# Validate extended configuration
is_valid, issues = config.validate()
if not is_valid:
    for issue in issues:
        print(f"{issue.severity}: {issue.message}")
```

---

## ✅ Custom Validation Rules

### **Domain-Specific Validation**

```python
from langswarm.core.config.validation import ConfigurationValidator, ValidationIssue

class CustomConfigurationValidator(ConfigurationValidator):
    """Extended validator with custom rules"""
    
    def __init__(self):
        super().__init__()
        self.custom_rules = []
    
    def add_custom_rule(self, rule_func):
        """Add custom validation rule"""
        self.custom_rules.append(rule_func)
    
    def validate(self, config: LangSwarmConfig) -> Tuple[bool, List[ValidationIssue]]:
        """Extended validation with custom rules"""
        # Run standard validation
        is_valid, issues = super().validate(config)
        
        # Run custom rules
        custom_issues = []
        for rule in self.custom_rules:
            try:
                rule_issues = rule(config)
                custom_issues.extend(rule_issues)
            except Exception as e:
                custom_issues.append(ValidationIssue(
                    severity="ERROR",
                    message=f"Custom validation rule failed: {str(e)}",
                    component="custom_validation",
                    suggestion="Check custom validation rule implementation",
                    category="validation"
                ))
        
        # Combine results
        all_issues = issues + custom_issues
        overall_valid = is_valid and not any(
            issue.severity == "ERROR" for issue in custom_issues
        )
        
        return overall_valid, all_issues

# Custom validation rules
def validate_production_requirements(config: LangSwarmConfig) -> List[ValidationIssue]:
    """Validate production environment requirements"""
    issues = []
    
    # Check for production-required settings
    if hasattr(config, 'deployment') and config.deployment.environment == "production":
        # Require specific agent models for production
        for agent in config.agents:
            if agent.model in ["gpt-3.5-turbo", "claude-3-haiku-20240307"]:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    message=f"Agent '{agent.id}' uses development model in production",
                    component=f"agents[{agent.id}].model",
                    suggestion="Use production-grade model (gpt-4, claude-3-sonnet)",
                    category="production"
                ))
        
        # Require Redis for production memory
        if config.memory.default_backend == MemoryBackend.SQLITE:
            issues.append(ValidationIssue(
                severity="ERROR",
                message="SQLite memory backend not recommended for production",
                component="memory.default_backend",
                suggestion="Use Redis or another distributed backend for production",
                category="production"
            ))
        
        # Require rate limiting
        if not config.security.rate_limiting_enabled:
            issues.append(ValidationIssue(
                severity="ERROR",
                message="Rate limiting required for production deployment",
                component="security.rate_limiting_enabled", 
                suggestion="Enable rate limiting for production security",
                category="security"
            ))
    
    return issues

def validate_cost_optimization(config: LangSwarmConfig) -> List[ValidationIssue]:
    """Validate cost optimization opportunities"""
    issues = []
    
    # Check for expensive model usage
    expensive_models = ["gpt-4", "claude-3-opus-20240229"]
    for agent in config.agents:
        if agent.model in expensive_models:
            issues.append(ValidationIssue(
                severity="INFO",
                message=f"Agent '{agent.id}' uses expensive model '{agent.model}'",
                component=f"agents[{agent.id}].model",
                suggestion="Consider gpt-3.5-turbo or claude-3-sonnet for cost optimization",
                category="cost"
            ))
    
    # Check for inefficient memory backends
    if config.memory.default_backend == MemoryBackend.BIGQUERY:
        issues.append(ValidationIssue(
            severity="INFO",
            message="BigQuery memory backend may incur higher costs",
            component="memory.default_backend",
            suggestion="Consider Redis or SQLite for cost optimization",
            category="cost"
        ))
    
    return issues

# Usage
validator = CustomConfigurationValidator()
validator.add_custom_rule(validate_production_requirements)
validator.add_custom_rule(validate_cost_optimization)

# Validate with custom rules
is_valid, issues = validator.validate(config)

# Filter issues by category
production_issues = [i for i in issues if i.category == "production"]
cost_issues = [i for i in issues if i.category == "cost"]

print(f"Production issues: {len(production_issues)}")
print(f"Cost optimization opportunities: {len(cost_issues)}")
```

### **Custom Environment Validation**

```python
def validate_custom_environment(config: LangSwarmConfig) -> List[ValidationIssue]:
    """Validate custom environment requirements"""
    issues = []
    
    # Check for custom environment variables
    required_vars = {
        "CUSTOM_API_KEY": "Custom integration API key",
        "MONITORING_TOKEN": "Monitoring service token", 
        "DEPLOYMENT_ENV": "Deployment environment identifier"
    }
    
    for var_name, description in required_vars.items():
        if var_name not in os.environ:
            issues.append(ValidationIssue(
                severity="ERROR",
                message=f"Required environment variable '{var_name}' not set",
                component="environment",
                suggestion=f"Set {var_name} environment variable for {description}",
                category="environment"
            ))
    
    # Validate environment-specific settings
    deployment_env = os.getenv("DEPLOYMENT_ENV", "development")
    if deployment_env == "production":
        # Production-specific validations
        if os.getenv("DEBUG", "false").lower() == "true":
            issues.append(ValidationIssue(
                severity="WARNING",
                message="Debug mode enabled in production environment",
                component="environment.DEBUG",
                suggestion="Set DEBUG=false for production",
                category="security"
            ))
    
    return issues

# Add to validator
validator.add_custom_rule(validate_custom_environment)
```

---

## 📁 Custom Configuration Loaders

### **Custom File Format Support**

```python
import json
import toml
from pathlib import Path
from langswarm.core.config.loaders import ConfigurationLoader

class ExtendedConfigurationLoader(ConfigurationLoader):
    """Extended loader supporting additional formats"""
    
    def __init__(self, config_class=LangSwarmConfig):
        super().__init__(config_class)
        self.format_loaders = {
            '.yaml': self._load_yaml,
            '.yml': self._load_yaml,
            '.json': self._load_json,
            '.toml': self._load_toml,
            '.env': self._load_env_format
        }
    
    def load(self, path: Union[str, Path], **kwargs) -> LangSwarmConfig:
        """Load configuration from various formats"""
        path = Path(path)
        
        if path.suffix not in self.format_loaders:
            raise ConfigurationError(f"Unsupported format: {path.suffix}")
        
        # Load using appropriate loader
        loader_func = self.format_loaders[path.suffix]
        data = loader_func(path)
        
        # Apply environment substitution
        if kwargs.get('environment_substitution', True):
            data = self._substitute_environment_variables(data)
        
        # Create configuration object
        config = self.config_class.from_dict(data)
        
        # Validate if requested
        if kwargs.get('validate', True):
            is_valid, issues = config.validate()
            if not is_valid:
                error_issues = [i for i in issues if i.severity == "ERROR"]
                if error_issues:
                    raise ValidationError(f"Configuration validation failed: {error_issues}")
        
        return config
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _load_toml(self, path: Path) -> Dict[str, Any]:
        """Load TOML configuration"""
        return toml.load(path)
    
    def _load_env_format(self, path: Path) -> Dict[str, Any]:
        """Load environment-style configuration"""
        config_data = {"agents": [], "tools": [], "workflows": []}
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # Parse hierarchical keys (e.g., AGENT_MAIN_PROVIDER=openai)
                    self._set_nested_value(config_data, key, value)
        
        return config_data
    
    def _set_nested_value(self, data: Dict, key: str, value: str):
        """Set nested configuration value from flat key"""
        parts = key.lower().split('_')
        
        if parts[0] == 'agent':
            # Handle agent configuration
            agent_id = parts[1] if len(parts) > 1 else 'default'
            field = parts[2] if len(parts) > 2 else 'name'
            
            # Find or create agent
            agent = next((a for a in data['agents'] if a.get('id') == agent_id), None)
            if not agent:
                agent = {'id': agent_id, 'name': agent_id.title()}
                data['agents'].append(agent)
            
            agent[field] = value
        
        elif parts[0] == 'tool':
            # Handle tool configuration
            tool_id = parts[1] if len(parts) > 1 else 'default'
            field = parts[2] if len(parts) > 2 else 'name'
            
            # Find or create tool
            tool = next((t for t in data['tools'] if t.get('id') == tool_id), None)
            if not tool:
                tool = {'id': tool_id, 'name': tool_id.title()}
                data['tools'].append(tool)
            
            tool[field] = value
```

### **Database Configuration Loader**

```python
class DatabaseConfigurationLoader:
    """Load configuration from database"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection = self._connect(db_connection_string)
    
    def load_configuration(self, config_id: str) -> LangSwarmConfig:
        """Load configuration from database"""
        # Load configuration data from database
        config_data = self._load_from_db(config_id)
        
        # Convert to LangSwarm configuration
        config = LangSwarmConfig.from_dict(config_data)
        
        return config
    
    def save_configuration(self, config: LangSwarmConfig, config_id: str):
        """Save configuration to database"""
        config_data = config.to_dict()
        self._save_to_db(config_id, config_data)
    
    def list_configurations(self) -> List[str]:
        """List available configuration IDs"""
        return self._list_configs_from_db()
    
    def _connect(self, connection_string: str):
        """Connect to database"""
        # Implementation depends on database type
        pass
    
    def _load_from_db(self, config_id: str) -> Dict[str, Any]:
        """Load configuration data from database"""
        # Database-specific implementation
        pass
    
    def _save_to_db(self, config_id: str, config_data: Dict[str, Any]):
        """Save configuration data to database"""
        # Database-specific implementation
        pass

# Usage
db_loader = DatabaseConfigurationLoader("postgresql://user:pass@host/db")
config = db_loader.load_configuration("production_config_v1")
```

### **Remote Configuration Loader**

```python
import requests
from urllib.parse import urljoin

class RemoteConfigurationLoader:
    """Load configuration from remote HTTP source"""
    
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.session = requests.Session()
        
        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}'
            })
    
    def load_configuration(self, config_name: str) -> LangSwarmConfig:
        """Load configuration from remote source"""
        url = urljoin(self.base_url, f"configurations/{config_name}")
        
        response = self.session.get(url)
        response.raise_for_status()
        
        config_data = response.json()
        return LangSwarmConfig.from_dict(config_data)
    
    def save_configuration(self, config: LangSwarmConfig, config_name: str):
        """Save configuration to remote source"""
        url = urljoin(self.base_url, f"configurations/{config_name}")
        
        config_data = config.to_dict()
        response = self.session.put(url, json=config_data)
        response.raise_for_status()
    
    def list_configurations(self) -> List[str]:
        """List available configurations"""
        url = urljoin(self.base_url, "configurations")
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json().get('configurations', [])

# Usage
remote_loader = RemoteConfigurationLoader(
    "https://config.example.com/api/v1/",
    auth_token="your_token"
)

config = remote_loader.load_configuration("team_production_config")
```

---

## 📝 Custom Templates

### **Creating Custom Templates**

```python
from langswarm.core.config.schema import *

class CustomTemplateBuilder:
    """Build custom configuration templates"""
    
    @staticmethod
    def build_ml_research_template() -> LangSwarmConfig:
        """Template for ML research workflows"""
        return LangSwarmConfig(
            agents=[
                AgentConfig(
                    id="researcher",
                    name="ML Researcher",
                    provider=LLMProvider.OPENAI,
                    model="gpt-4",
                    system_prompt="You are an ML research assistant specializing in paper analysis and experimental design.",
                    temperature=0.3,
                    max_tokens=4096
                ),
                AgentConfig(
                    id="coder",
                    name="ML Coder",
                    provider=LLMProvider.ANTHROPIC,
                    model="claude-3-sonnet-20240229",
                    system_prompt="You are an expert ML engineer who writes clean, efficient research code.",
                    temperature=0.2,
                    max_tokens=8192
                ),
                AgentConfig(
                    id="reviewer",
                    name="Code Reviewer",
                    provider=LLMProvider.OPENAI,
                    model="gpt-4",
                    system_prompt="You are a senior ML engineer who reviews code for correctness and best practices.",
                    temperature=0.1,
                    max_tokens=4096
                )
            ],
            tools=[
                ToolConfig(
                    id="arxiv_search",
                    name="ArXiv Paper Search",
                    type=ToolType.MCP,
                    server_config={
                        "command": "python",
                        "args": ["-m", "langswarm.mcp.tools.arxiv"]
                    }
                ),
                ToolConfig(
                    id="code_executor",
                    name="Code Execution Environment",
                    type=ToolType.MCP,
                    server_config={
                        "command": "python",
                        "args": ["-m", "langswarm.mcp.tools.code_executor"]
                    }
                ),
                ToolConfig(
                    id="research_memory",
                    name="Research Memory",
                    type=ToolType.MEMORY,
                    backend=MemoryBackend.CHROMADB,
                    connection_params={
                        "persist_directory": "./research_memory",
                        "collection_name": "ml_research"
                    }
                )
            ],
            workflows=[
                WorkflowConfig(
                    id="paper_analysis",
                    name="Paper Analysis Workflow",
                    agent_id="researcher",
                    tool_ids=["arxiv_search", "research_memory"],
                    max_iterations=5
                ),
                WorkflowConfig(
                    id="code_development",
                    name="Code Development Workflow",
                    agent_id="coder",
                    tool_ids=["code_executor", "research_memory"],
                    max_iterations=10
                ),
                WorkflowConfig(
                    id="code_review",
                    name="Code Review Workflow",
                    agent_id="reviewer",
                    tool_ids=["code_executor"],
                    max_iterations=3
                )
            ],
            memory=MemoryConfig(
                default_backend=MemoryBackend.CHROMADB,
                backends={
                    "chromadb": {
                        "persist_directory": "./research_memory",
                        "collection_name": "ml_research"
                    }
                }
            ),
            observability=ObservabilityConfig(
                logging=LoggingConfig(level="INFO", format="detailed"),
                tracing=TracingConfig(enabled=True, output_file="research_traces.jsonl")
            )
        )
    
    @staticmethod
    def build_customer_support_template() -> LangSwarmConfig:
        """Template for customer support system"""
        return LangSwarmConfig(
            agents=[
                AgentConfig(
                    id="support_agent",
                    name="Customer Support Agent",
                    provider=LLMProvider.OPENAI,
                    model="gpt-3.5-turbo",
                    system_prompt="You are a helpful customer support agent. Be empathetic and solution-focused.",
                    temperature=0.7,
                    max_tokens=2048
                ),
                AgentConfig(
                    id="escalation_agent",
                    name="Escalation Specialist",
                    provider=LLMProvider.ANTHROPIC,
                    model="claude-3-sonnet-20240229",
                    system_prompt="You handle complex customer issues that require specialized knowledge.",
                    temperature=0.3,
                    max_tokens=4096
                )
            ],
            tools=[
                ToolConfig(
                    id="knowledge_base",
                    name="Support Knowledge Base",
                    type=ToolType.MEMORY,
                    backend=MemoryBackend.ELASTICSEARCH,
                    connection_params={
                        "host": "localhost",
                        "port": 9200,
                        "index": "support_kb"
                    }
                ),
                ToolConfig(
                    id="ticket_system",
                    name="Ticketing System",
                    type=ToolType.MCP,
                    server_config={
                        "command": "python",
                        "args": ["-m", "langswarm.mcp.tools.ticketing"]
                    }
                ),
                ToolConfig(
                    id="notification",
                    name="Customer Notification",
                    type=ToolType.PLUGIN,
                    plugin_config={
                        "module_path": "langswarm.plugins.notification",
                        "provider": "email"
                    }
                )
            ],
            workflows=[
                WorkflowConfig(
                    id="initial_support",
                    name="Initial Support Response",
                    agent_id="support_agent",
                    tool_ids=["knowledge_base", "ticket_system"],
                    max_iterations=3
                ),
                WorkflowConfig(
                    id="escalated_support",
                    name="Escalated Support Handling",
                    agent_id="escalation_agent",
                    tool_ids=["knowledge_base", "ticket_system", "notification"],
                    max_iterations=5
                )
            ],
            security=SecurityConfig(
                rate_limiting_enabled=True,
                requests_per_minute=30,
                require_authentication=True
            )
        )

# Register custom templates
from langswarm.core.config import register_template

register_template("ml_research", CustomTemplateBuilder.build_ml_research_template)
register_template("customer_support", CustomTemplateBuilder.build_customer_support_template)

# Use custom templates
research_config = load_template("ml_research")
support_config = load_template("customer_support")
```

### **Template with Parameters**

```python
class ParameterizedTemplateBuilder:
    """Build templates with parameters"""
    
    @staticmethod
    def build_scalable_api_template(
        environment: str = "development",
        replicas: int = 1,
        memory_backend: str = "sqlite",
        enable_monitoring: bool = False
    ) -> LangSwarmConfig:
        """Scalable API template with parameters"""
        
        # Choose models based on environment
        if environment == "production":
            primary_model = "gpt-4"
            fallback_model = "gpt-3.5-turbo"
        else:
            primary_model = "gpt-3.5-turbo"
            fallback_model = "gpt-3.5-turbo"
        
        # Configure memory backend
        memory_config = MemoryConfig(default_backend=MemoryBackend.from_string(memory_backend))
        
        if memory_backend == "redis":
            memory_config.backends = {
                "redis": {
                    "host": "${REDIS_HOST:localhost}",
                    "port": "${REDIS_PORT:6379}",
                    "db": 0
                }
            }
        elif memory_backend == "sqlite":
            memory_config.backends = {
                "sqlite": {
                    "db_path": f"{environment}_memory.db",
                    "enable_wal": True
                }
            }
        
        # Configure observability
        observability_config = ObservabilityConfig()
        if enable_monitoring:
            observability_config.metrics = MetricsConfig(enabled=True)
            observability_config.tracing = TracingConfig(enabled=True)
        
        return LangSwarmConfig(
            agents=[
                AgentConfig(
                    id="primary_agent",
                    name="Primary API Agent",
                    provider=LLMProvider.OPENAI,
                    model=primary_model,
                    temperature=0.3,
                    max_tokens=2048
                ),
                AgentConfig(
                    id="fallback_agent",
                    name="Fallback Agent",
                    provider=LLMProvider.OPENAI,
                    model=fallback_model,
                    temperature=0.3,
                    max_tokens=2048
                )
            ],
            tools=[
                ToolConfig(
                    id="api_memory",
                    name="API Memory",
                    type=ToolType.MEMORY,
                    backend=MemoryBackend.from_string(memory_backend)
                )
            ],
            workflows=[
                WorkflowConfig(
                    id="api_workflow",
                    name="API Request Workflow",
                    agent_id="primary_agent",
                    tool_ids=["api_memory"],
                    max_iterations=5
                )
            ],
            memory=memory_config,
            observability=observability_config,
            server=ServerConfig(
                host="0.0.0.0" if environment == "production" else "localhost",
                port=8000,
                workers=replicas
            ),
            security=SecurityConfig(
                rate_limiting_enabled=(environment == "production"),
                requests_per_minute=100 if environment == "production" else 1000
            )
        )

# Usage with parameters
dev_config = ParameterizedTemplateBuilder.build_scalable_api_template(
    environment="development",
    replicas=1,
    memory_backend="sqlite",
    enable_monitoring=False
)

prod_config = ParameterizedTemplateBuilder.build_scalable_api_template(
    environment="production",
    replicas=3,
    memory_backend="redis",
    enable_monitoring=True
)
```

---

## 🔍 Custom Optimization Rules

### **Cost Optimization Analyzer**

```python
from langswarm.core.config.utils import OptimizationSuggestion

class CustomOptimizationAnalyzer:
    """Custom configuration optimization analysis"""
    
    def analyze_cost_optimization(self, config: LangSwarmConfig) -> List[OptimizationSuggestion]:
        """Analyze cost optimization opportunities"""
        suggestions = []
        
        # Model cost analysis
        model_costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015}
        }
        
        for agent in config.agents:
            if agent.model in model_costs:
                current_cost = model_costs[agent.model]
                
                # Suggest cheaper alternatives
                if agent.model == "gpt-4":
                    suggestions.append(OptimizationSuggestion(
                        category="cost",
                        description=f"Consider using gpt-3.5-turbo for agent '{agent.id}' to reduce costs by 95%",
                        impact="High - 95% cost reduction",
                        effort="Low - change model in configuration",
                        priority="Medium",
                        estimated_savings="$500-2000/month depending on usage"
                    ))
                
                elif agent.model == "claude-3-opus-20240229":
                    suggestions.append(OptimizationSuggestion(
                        category="cost",
                        description=f"Consider using claude-3-sonnet for agent '{agent.id}' to reduce costs by 80%",
                        impact="High - 80% cost reduction",
                        effort="Low - change model in configuration",
                        priority="High",
                        estimated_savings="$200-800/month depending on usage"
                    ))
        
        # Memory backend cost analysis
        if config.memory.default_backend == MemoryBackend.BIGQUERY:
            suggestions.append(OptimizationSuggestion(
                category="cost",
                description="BigQuery memory backend may incur high costs for frequent operations",
                impact="Medium - Variable cost based on usage",
                effort="Medium - migrate to Redis or SQLite",
                priority="Low",
                estimated_savings="$50-500/month depending on query volume"
            ))
        
        return suggestions
    
    def analyze_performance_optimization(self, config: LangSwarmConfig) -> List[OptimizationSuggestion]:
        """Analyze performance optimization opportunities"""
        suggestions = []
        
        # Memory backend performance
        if config.memory.default_backend == MemoryBackend.SQLITE:
            agent_count = len(config.agents)
            if agent_count > 2:
                suggestions.append(OptimizationSuggestion(
                    category="performance",
                    description="SQLite memory backend may become bottleneck with multiple agents",
                    impact="High - 3-5x performance improvement",
                    effort="Medium - configure Redis backend",
                    priority="High",
                    implementation_notes="Use Redis for concurrent access patterns"
                ))
        
        # Agent model performance
        for agent in config.agents:
            if agent.model == "gpt-4" and agent.max_tokens > 4096:
                suggestions.append(OptimizationSuggestion(
                    category="performance",
                    description=f"Agent '{agent.id}' configured with high token limit may be slow",
                    impact="Medium - 2x faster response times",
                    effort="Low - reduce max_tokens to 2048-4096",
                    priority="Medium",
                    implementation_notes="Reduce max_tokens unless long responses required"
                ))
        
        return suggestions
    
    def analyze_security_optimization(self, config: LangSwarmConfig) -> List[OptimizationSuggestion]:
        """Analyze security optimization opportunities"""
        suggestions = []
        
        # Rate limiting
        if not config.security.rate_limiting_enabled:
            suggestions.append(OptimizationSuggestion(
                category="security",
                description="Rate limiting not enabled - vulnerability to abuse",
                impact="High - prevents API abuse",
                effort="Low - enable rate limiting in configuration",
                priority="High",
                implementation_notes="Set appropriate requests_per_minute limit"
            ))
        
        # API key handling
        for agent in config.agents:
            if not agent.api_key_env:
                suggestions.append(OptimizationSuggestion(
                    category="security",
                    description=f"Agent '{agent.id}' API key not configured via environment variable",
                    impact="High - secure API key handling",
                    effort="Low - set api_key_env field",
                    priority="High",
                    implementation_notes="Use environment variables for all API keys"
                ))
        
        return suggestions

# Usage
optimizer = CustomOptimizationAnalyzer()

cost_suggestions = optimizer.analyze_cost_optimization(config)
performance_suggestions = optimizer.analyze_performance_optimization(config)
security_suggestions = optimizer.analyze_security_optimization(config)

print(f"Cost optimization opportunities: {len(cost_suggestions)}")
print(f"Performance optimization opportunities: {len(performance_suggestions)}")
print(f"Security optimization opportunities: {len(security_suggestions)}")

# Combine all suggestions
all_suggestions = {
    "cost": cost_suggestions,
    "performance": performance_suggestions,
    "security": security_suggestions
}

for category, suggestions in all_suggestions.items():
    print(f"\n{category.title()} Optimizations:")
    for suggestion in suggestions:
        print(f"  • {suggestion.description}")
        print(f"    Impact: {suggestion.impact}")
        print(f"    Effort: {suggestion.effort}")
        print(f"    Priority: {suggestion.priority}")
```

---

## 🔗 Integration Hooks

### **Configuration Lifecycle Hooks**

```python
from abc import ABC, abstractmethod
from typing import Optional

class ConfigurationHook(ABC):
    """Base class for configuration lifecycle hooks"""
    
    @abstractmethod
    def before_load(self, path: str) -> Optional[Dict[str, Any]]:
        """Called before configuration is loaded"""
        pass
    
    @abstractmethod
    def after_load(self, config: LangSwarmConfig) -> LangSwarmConfig:
        """Called after configuration is loaded"""
        pass
    
    @abstractmethod
    def before_save(self, config: LangSwarmConfig) -> LangSwarmConfig:
        """Called before configuration is saved"""
        pass
    
    @abstractmethod
    def after_save(self, path: str, config: LangSwarmConfig) -> None:
        """Called after configuration is saved"""
        pass

class AuditingHook(ConfigurationHook):
    """Hook for auditing configuration changes"""
    
    def __init__(self, audit_log_path: str):
        self.audit_log_path = audit_log_path
    
    def before_load(self, path: str) -> Optional[Dict[str, Any]]:
        """Log configuration load"""
        self._log_event("LOAD_START", {"path": path})
        return None
    
    def after_load(self, config: LangSwarmConfig) -> LangSwarmConfig:
        """Log successful load"""
        self._log_event("LOAD_SUCCESS", {
            "agent_count": len(config.agents),
            "tool_count": len(config.tools),
            "workflow_count": len(config.workflows)
        })
        return config
    
    def before_save(self, config: LangSwarmConfig) -> LangSwarmConfig:
        """Log configuration save"""
        self._log_event("SAVE_START", {"config_hash": self._hash_config(config)})
        return config
    
    def after_save(self, path: str, config: LangSwarmConfig) -> None:
        """Log successful save"""
        self._log_event("SAVE_SUCCESS", {"path": path})
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log audit event"""
        import json
        import datetime
        
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def _hash_config(self, config: LangSwarmConfig) -> str:
        """Generate hash of configuration"""
        import hashlib
        import json
        
        config_str = json.dumps(config.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

class EnvironmentInjectionHook(ConfigurationHook):
    """Hook for injecting environment-specific settings"""
    
    def __init__(self, environment: str):
        self.environment = environment
    
    def before_load(self, path: str) -> Optional[Dict[str, Any]]:
        """No pre-load modifications"""
        return None
    
    def after_load(self, config: LangSwarmConfig) -> LangSwarmConfig:
        """Inject environment-specific settings"""
        if self.environment == "production":
            # Production optimizations
            config.security.rate_limiting_enabled = True
            config.security.requests_per_minute = 60
            
            # Use production models
            for agent in config.agents:
                if agent.model == "gpt-3.5-turbo":
                    agent.model = "gpt-4"
            
            # Enable monitoring
            config.observability.metrics.enabled = True
            config.observability.tracing.enabled = True
            config.observability.tracing.sampling_rate = 0.1
        
        elif self.environment == "development":
            # Development optimizations
            config.server.debug = True
            config.observability.logging.level = "DEBUG"
            
            # Use faster models for development
            for agent in config.agents:
                if agent.model == "gpt-4":
                    agent.model = "gpt-3.5-turbo"
        
        return config
    
    def before_save(self, config: LangSwarmConfig) -> LangSwarmConfig:
        """No pre-save modifications"""
        return config
    
    def after_save(self, path: str, config: LangSwarmConfig) -> None:
        """No post-save actions"""
        pass

# Extended loader with hooks
class HookableConfigurationLoader(ConfigurationLoader):
    """Configuration loader with lifecycle hooks"""
    
    def __init__(self, config_class=LangSwarmConfig):
        super().__init__(config_class)
        self.hooks = []
    
    def add_hook(self, hook: ConfigurationHook):
        """Add configuration hook"""
        self.hooks.append(hook)
    
    def load(self, path: Union[str, Path], **kwargs) -> LangSwarmConfig:
        """Load configuration with hooks"""
        path_str = str(path)
        
        # Execute before_load hooks
        for hook in self.hooks:
            override_data = hook.before_load(path_str)
            if override_data:
                # Hook wants to override data
                kwargs['override_data'] = override_data
        
        # Load configuration
        config = super().load(path, **kwargs)
        
        # Execute after_load hooks
        for hook in self.hooks:
            config = hook.after_load(config)
        
        return config
    
    def save(self, config: LangSwarmConfig, path: Union[str, Path], **kwargs):
        """Save configuration with hooks"""
        path_str = str(path)
        
        # Execute before_save hooks
        for hook in self.hooks:
            config = hook.before_save(config)
        
        # Save configuration
        super().save(config, path, **kwargs)
        
        # Execute after_save hooks
        for hook in self.hooks:
            hook.after_save(path_str, config)

# Usage
loader = HookableConfigurationLoader()
loader.add_hook(AuditingHook("config_audit.log"))
loader.add_hook(EnvironmentInjectionHook("production"))

# Load with hooks
config = loader.load("langswarm.yaml")

# Save with hooks
loader.save(config, "production_config.yaml")
```

---

## 📚 Best Practices for Extension

### **Schema Extension Guidelines**
- **Maintain Type Safety**: Always use dataclasses and type hints
- **Provide Validation**: Implement validation methods for custom schemas
- **Documentation**: Document custom fields and their purposes
- **Backward Compatibility**: Consider migration when modifying existing schemas

### **Validation Extension Guidelines**
- **Specific Error Messages**: Provide clear, actionable error messages
- **Categorize Issues**: Use appropriate severity levels and categories
- **Performance Awareness**: Keep validation rules efficient
- **Test Coverage**: Test validation rules thoroughly

### **Loader Extension Guidelines**
- **Error Handling**: Provide clear error messages for loading failures
- **Format Support**: Document supported file formats and limitations
- **Security**: Validate external data sources and handle authentication
- **Caching**: Consider caching for remote or database sources

### **Template Extension Guidelines**
- **Parameterization**: Make templates configurable for different use cases
- **Documentation**: Provide clear documentation for template usage
- **Best Practices**: Include security and performance best practices
- **Validation**: Ensure templates generate valid configurations

---

**LangSwarm V2's configuration system provides comprehensive extension capabilities, allowing developers to customize every aspect of configuration management while maintaining type safety and integration with the core system.**

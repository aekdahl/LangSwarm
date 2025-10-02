# LangSwarm V2 Configuration Examples

**Practical configuration examples for common use cases and deployment scenarios**

## 🎯 Overview

This collection provides real-world configuration examples for LangSwarm V2, demonstrating best practices for different use cases, environments, and deployment scenarios. Each example includes complete configurations, environment setup, and usage instructions.

**Example Categories:**
- **Getting Started**: Simple configurations for learning
- **Development**: Development environment setups
- **Production**: Production-ready configurations
- **Specialized Use Cases**: Domain-specific configurations
- **Integration**: External system integrations
- **Migration**: V1 to V2 migration examples

---

## 🚀 Getting Started Examples

### **1. Simple Chatbot**

**Configuration**: `simple_chatbot.yaml`
```yaml
# Simple chatbot with OpenAI GPT-3.5
agents:
  - id: "chatbot"
    name: "Simple Chatbot"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: "You are a helpful assistant. Be concise and friendly."
    temperature: 0.7
    max_tokens: 1024
    api_key_env: "OPENAI_API_KEY"

tools:
  - id: "filesystem"
    name: "File Access"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]

workflows:
  - id: "chat"
    name: "Chat Workflow"
    agent_id: "chatbot"
    tool_ids: ["filesystem"]
    max_iterations: 5
    timeout_seconds: 120

memory:
  default_backend: "sqlite"
  backends:
    sqlite:
      db_path: "chatbot_memory.db"

server:
  host: "localhost"
  port: 8000
  debug: true

observability:
  logging:
    level: "INFO"
    format: "standard"
```

**Environment**: `.env`
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

**Usage**:
```python
from langswarm.core.config import load_config

# Load configuration
config = load_config("simple_chatbot.yaml")

# Start chatbot
from langswarm.v2 import LangSwarm

app = LangSwarm(config)
response = await app.run_workflow("chat", {"message": "Hello!"})
print(response)
```

### **2. Multi-Agent Setup**

**Configuration**: `multi_agent.yaml`
```yaml
# Multi-agent system with different specializations
agents:
  - id: "researcher"
    name: "Research Agent"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a research specialist. Focus on:
      - Gathering accurate information
      - Analyzing data and trends
      - Providing well-sourced insights
    temperature: 0.3
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"

  - id: "writer"
    name: "Content Writer"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: |
      You are a skilled content writer. Focus on:
      - Clear, engaging writing
      - Adapting tone for audience
      - Structuring information effectively
    temperature: 0.7
    max_tokens: 3000
    api_key_env: "ANTHROPIC_API_KEY"

  - id: "reviewer"
    name: "Quality Reviewer"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a quality reviewer. Focus on:
      - Fact-checking and accuracy
      - Grammar and style
      - Consistency and clarity
    temperature: 0.2
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"

tools:
  - id: "web_search"
    name: "Web Search"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.web_search"]

  - id: "shared_memory"
    name: "Shared Memory"
    type: "memory"
    backend: "sqlite"
    connection_params:
      db_path: "shared_memory.db"

workflows:
  - id: "content_pipeline"
    name: "Content Creation Pipeline"
    steps:
      - agent_id: "researcher"
        tools: ["web_search", "shared_memory"]
        task: "research"
      - agent_id: "writer"
        tools: ["shared_memory"]
        task: "write"
      - agent_id: "reviewer"
        tools: ["shared_memory"]
        task: "review"
    max_iterations: 3
    timeout_seconds: 600
```

**Environment**: `.env`
```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

---

## 💻 Development Environment Examples

### **3. Development Setup**

**Configuration**: `development.yaml`
```yaml
# Development environment with debugging enabled
agents:
  - id: "dev_agent"
    name: "Development Agent"
    provider: "openai"
    model: "gpt-3.5-turbo"  # Faster/cheaper for development
    system_prompt: "You are a development assistant."
    temperature: 0.8        # More creative for experimentation
    max_tokens: 1024
    api_key_env: "OPENAI_API_KEY"

  - id: "test_agent"
    name: "Test Agent"
    provider: "anthropic"
    model: "claude-3-haiku-20240307"  # Fast for testing
    system_prompt: "You help with testing and debugging."
    temperature: 0.5
    max_tokens: 1024
    api_key_env: "ANTHROPIC_API_KEY"

tools:
  - id: "filesystem"
    name: "File System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]
      timeout: 10  # Shorter timeout for development

  - id: "code_executor"
    name: "Code Executor"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.code_executor"]
      env:
        EXECUTION_MODE: "safe"

  - id: "dev_memory"
    name: "Development Memory"
    type: "memory"
    backend: "sqlite"
    connection_params:
      db_path: "./dev_memory.db"
      enable_wal: false  # Simpler for development

workflows:
  - id: "dev_workflow"
    name: "Development Workflow"
    agent_id: "dev_agent"
    tool_ids: ["filesystem", "code_executor", "dev_memory"]
    max_iterations: 10
    timeout_seconds: 300
    error_handling: "continue"  # Continue on errors for debugging

memory:
  default_backend: "sqlite"
  backends:
    sqlite:
      db_path: "./dev_memory.db"
      enable_wal: false

server:
  host: "localhost"
  port: 8000
  debug: true              # Enable debug mode
  reload: true             # Auto-reload on changes
  workers: 1

security:
  rate_limiting_enabled: false  # Disabled for development
  require_authentication: false

observability:
  logging:
    level: "DEBUG"           # Verbose logging
    format: "detailed"       # Detailed format for debugging
    output: "console"
  
  tracing:
    enabled: true            # Enable tracing for debugging
    output_file: "dev_traces.jsonl"
    sampling_rate: 1.0       # Trace everything in development
  
  metrics:
    enabled: false           # Disabled for simplicity
```

**Environment**: `.env.development`
```bash
# Development Environment Variables
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Development-specific settings
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### **4. Testing Configuration**

**Configuration**: `testing.yaml`
```yaml
# Configuration optimized for testing
agents:
  - id: "test_agent"
    name: "Test Agent"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: "You are a test assistant. Provide consistent responses."
    temperature: 0.0         # Deterministic responses for testing
    max_tokens: 512          # Smaller responses for faster tests
    api_key_env: "OPENAI_API_KEY"

tools:
  - id: "mock_tool"
    name: "Mock Tool"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.mock"]
      timeout: 5             # Short timeout for tests

  - id: "test_memory"
    name: "Test Memory"
    type: "memory"
    backend: "memory"        # In-memory for testing
    connection_params: {}

workflows:
  - id: "test_workflow"
    name: "Test Workflow"
    agent_id: "test_agent"
    tool_ids: ["mock_tool", "test_memory"]
    max_iterations: 3        # Limited iterations for tests
    timeout_seconds: 30      # Short timeout for tests

memory:
  default_backend: "memory"  # In-memory backend for testing
  backends:
    memory: {}

server:
  host: "127.0.0.1"
  port: 8001                 # Different port for testing
  debug: false
  workers: 1

observability:
  logging:
    level: "WARNING"         # Minimal logging for tests
    format: "standard"
    output: "console"
  
  tracing:
    enabled: false           # Disabled for performance
  
  metrics:
    enabled: false           # Disabled for simplicity
```

---

## 🏭 Production Environment Examples

### **5. Production Setup**

**Configuration**: `production.yaml`
```yaml
# Production environment with high availability
agents:
  - id: "primary_agent"
    name: "Primary Production Agent"
    provider: "openai"
    model: "gpt-4"           # Best model for production
    system_prompt: "You are a production assistant. Provide accurate, helpful responses."
    temperature: 0.3         # Consistent responses
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"
    timeout_seconds: 30
    retry_count: 3

  - id: "fallback_agent"
    name: "Fallback Agent"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: "You are a backup assistant."
    temperature: 0.3
    max_tokens: 2048
    api_key_env: "ANTHROPIC_API_KEY"
    timeout_seconds: 30
    retry_count: 3

tools:
  - id: "production_filesystem"
    name: "Production File System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]
      timeout: 30
      env:
        FILESYSTEM_ROOT: "/app/data"
        READ_ONLY: "false"

  - id: "redis_memory"
    name: "Redis Memory"
    type: "memory"
    backend: "redis"
    connection_params:
      host: "${REDIS_HOST:redis}"
      port: ${REDIS_PORT:6379}
      password: "${REDIS_PASSWORD}"
      db: 0
      max_connections: 20
      socket_timeout: 5

  - id: "notification_service"
    name: "Notification Service"
    type: "plugin"
    plugin_config:
      module_path: "langswarm.plugins.notification"
      provider: "slack"
      webhook_url: "${SLACK_WEBHOOK_URL}"

workflows:
  - id: "primary_workflow"
    name: "Primary Production Workflow"
    agent_id: "primary_agent"
    tool_ids: ["production_filesystem", "redis_memory"]
    max_iterations: 5
    timeout_seconds: 300
    error_handling: "retry"
    retry_count: 3

  - id: "fallback_workflow"
    name: "Fallback Workflow"
    agent_id: "fallback_agent"
    tool_ids: ["production_filesystem", "redis_memory"]
    max_iterations: 3
    timeout_seconds: 180

memory:
  default_backend: "redis"
  backends:
    redis:
      host: "${REDIS_HOST:redis}"
      port: ${REDIS_PORT:6379}
      password: "${REDIS_PASSWORD}"
      db: 0
      max_connections: 50
      health_check_interval: 30

server:
  host: "0.0.0.0"
  port: ${PORT:8000}
  workers: ${WORKERS:4}      # Multiple workers for production
  debug: false
  max_request_size: 10485760  # 10MB
  request_timeout: 60

security:
  rate_limiting_enabled: true
  requests_per_minute: 100
  burst_size: 20
  require_authentication: true
  allowed_origins: 
    - "https://app.example.com"
    - "https://api.example.com"
  
  api_key_rotation_enabled: true
  api_key_rotation_days: 30
  
  encrypt_at_rest: true
  encrypt_in_transit: true

observability:
  logging:
    level: "INFO"
    format: "json"           # Structured logging for production
    output: "file"
    file_path: "/var/log/langswarm/app.log"
    max_file_size: 104857600  # 100MB
    backup_count: 10
  
  metrics:
    enabled: true
    export_interval: 60
    prometheus_port: 9090
    include_system_metrics: true
  
  tracing:
    enabled: true
    output_file: "/var/log/langswarm/traces.jsonl"
    sampling_rate: 0.1       # Sample 10% of requests
    include_agent_traces: true
    include_tool_traces: true
```

**Environment**: `.env.production`
```bash
# Production Environment Variables
OPENAI_API_KEY=your_production_openai_key
ANTHROPIC_API_KEY=your_production_anthropic_key

# Infrastructure
REDIS_HOST=redis.internal
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Server Configuration
PORT=8000
WORKERS=4
HOST=0.0.0.0

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Security
ENVIRONMENT=production
```

### **6. High-Scale Production**

**Configuration**: `high_scale.yaml`
```yaml
# High-scale production with multiple agent pools
agents:
  # Fast response pool
  - id: "fast_agent_1"
    name: "Fast Agent 1"
    provider: "openai"
    model: "gpt-3.5-turbo"
    temperature: 0.3
    max_tokens: 1024
    api_key_env: "OPENAI_API_KEY"
    
  - id: "fast_agent_2"
    name: "Fast Agent 2"
    provider: "openai"
    model: "gpt-3.5-turbo"
    temperature: 0.3
    max_tokens: 1024
    api_key_env: "OPENAI_API_KEY_2"

  # Quality response pool
  - id: "quality_agent_1"
    name: "Quality Agent 1"
    provider: "openai"
    model: "gpt-4"
    temperature: 0.2
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"
    
  - id: "quality_agent_2"
    name: "Quality Agent 2"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    temperature: 0.2
    max_tokens: 2048
    api_key_env: "ANTHROPIC_API_KEY"

tools:
  - id: "redis_memory_primary"
    name: "Primary Redis Memory"
    type: "memory"
    backend: "redis"
    connection_params:
      host: "${REDIS_PRIMARY_HOST}"
      port: ${REDIS_PRIMARY_PORT:6379}
      password: "${REDIS_PRIMARY_PASSWORD}"

  - id: "redis_memory_secondary"
    name: "Secondary Redis Memory"
    type: "memory"
    backend: "redis"
    connection_params:
      host: "${REDIS_SECONDARY_HOST}"
      port: ${REDIS_SECONDARY_PORT:6379}
      password: "${REDIS_SECONDARY_PASSWORD}"

  - id: "elasticsearch_search"
    name: "Elasticsearch Search"
    type: "memory"
    backend: "elasticsearch"
    connection_params:
      hosts: ["${ES_HOST_1}", "${ES_HOST_2}", "${ES_HOST_3}"]
      index: "langswarm_search"

workflows:
  - id: "fast_workflow"
    name: "Fast Response Workflow"
    agent_pool: ["fast_agent_1", "fast_agent_2"]
    tool_ids: ["redis_memory_primary"]
    max_iterations: 3
    timeout_seconds: 30
    load_balancing: "round_robin"

  - id: "quality_workflow"
    name: "Quality Response Workflow"
    agent_pool: ["quality_agent_1", "quality_agent_2"]
    tool_ids: ["redis_memory_primary", "elasticsearch_search"]
    max_iterations: 5
    timeout_seconds: 120
    load_balancing: "least_loaded"

memory:
  default_backend: "redis"
  backends:
    redis:
      primary:
        host: "${REDIS_PRIMARY_HOST}"
        port: ${REDIS_PRIMARY_PORT:6379}
        password: "${REDIS_PRIMARY_PASSWORD}"
        max_connections: 100
      secondary:
        host: "${REDIS_SECONDARY_HOST}"
        port: ${REDIS_SECONDARY_PORT:6379}
        password: "${REDIS_SECONDARY_PASSWORD}"
        max_connections: 100

server:
  host: "0.0.0.0"
  port: ${PORT:8000}
  workers: ${WORKERS:8}
  
  # Load balancing
  load_balancer:
    strategy: "least_connections"
    health_check_interval: 10
    max_request_queue: 1000

security:
  rate_limiting_enabled: true
  requests_per_minute: 1000
  burst_size: 100
  
  # Advanced rate limiting
  rate_limiting_tiers:
    free: 60
    premium: 300
    enterprise: 1000

observability:
  metrics:
    enabled: true
    detailed_metrics: true
    custom_metrics:
      - agent_response_time
      - tool_execution_time
      - workflow_success_rate
      - queue_length
  
  alerts:
    enabled: true
    alert_rules:
      - name: "high_error_rate"
        condition: "error_rate > 0.05"
        duration: "5m"
        webhook: "${ALERT_WEBHOOK_URL}"
      - name: "high_latency"
        condition: "p95_latency > 5000ms"
        duration: "3m"
        webhook: "${ALERT_WEBHOOK_URL}"
```

---

## 🎯 Specialized Use Case Examples

### **7. Customer Support System**

**Configuration**: `customer_support.yaml`
```yaml
# Customer support automation system
agents:
  - id: "support_l1"
    name: "Level 1 Support"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: |
      You are a Level 1 customer support agent. Be empathetic, helpful, and efficient.
      - Handle common questions and issues
      - Escalate complex problems to Level 2
      - Always maintain a friendly, professional tone
    temperature: 0.7
    max_tokens: 1024

  - id: "support_l2"
    name: "Level 2 Support"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a Level 2 support specialist handling escalated issues.
      - Solve complex technical problems
      - Provide detailed troubleshooting
      - Create internal documentation
    temperature: 0.3
    max_tokens: 2048

  - id: "sentiment_analyzer"
    name: "Sentiment Analyzer"
    provider: "anthropic"
    model: "claude-3-haiku-20240307"
    system_prompt: "Analyze customer sentiment and urgency. Provide brief assessments."
    temperature: 0.1
    max_tokens: 256

tools:
  - id: "knowledge_base"
    name: "Support Knowledge Base"
    type: "memory"
    backend: "elasticsearch"
    connection_params:
      hosts: ["${ELASTICSEARCH_HOST}"]
      index: "support_kb"
      max_results: 10

  - id: "ticket_system"
    name: "Ticket Management"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.ticketing"]
      env:
        TICKET_API_URL: "${TICKET_API_URL}"
        TICKET_API_KEY: "${TICKET_API_KEY}"

  - id: "customer_db"
    name: "Customer Database"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.customer_db"]
      env:
        DB_CONNECTION_STRING: "${CUSTOMER_DB_URL}"

workflows:
  - id: "initial_support"
    name: "Initial Support Triage"
    steps:
      - agent_id: "sentiment_analyzer"
        tools: []
        task: "analyze_sentiment"
      - agent_id: "support_l1"
        tools: ["knowledge_base", "customer_db"]
        task: "provide_support"
    escalation_rules:
      - condition: "sentiment == 'angry'"
        target_workflow: "escalated_support"
      - condition: "complexity == 'high'"
        target_workflow: "escalated_support"

  - id: "escalated_support"
    name: "Escalated Support Handling"
    agent_id: "support_l2"
    tool_ids: ["knowledge_base", "ticket_system", "customer_db"]
    max_iterations: 5
    timeout_seconds: 600

memory:
  default_backend: "elasticsearch"
  backends:
    elasticsearch:
      hosts: ["${ELASTICSEARCH_HOST}"]
      indices:
        support_kb: "support_knowledge_base"
        conversations: "support_conversations"

observability:
  logging:
    level: "INFO"
    custom_fields:
      - customer_id
      - ticket_id
      - support_level
      - resolution_time
  
  metrics:
    enabled: true
    custom_metrics:
      - customer_satisfaction_score
      - first_response_time
      - resolution_rate
      - escalation_rate
```

### **8. Content Creation Pipeline**

**Configuration**: `content_pipeline.yaml`
```yaml
# Content creation and publishing pipeline
agents:
  - id: "researcher"
    name: "Content Researcher"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a content researcher. Your role:
      - Research topics thoroughly
      - Find credible sources
      - Gather current information
      - Identify key insights and trends
    temperature: 0.3
    max_tokens: 3000

  - id: "writer"
    name: "Content Writer"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: |
      You are a professional content writer. Your role:
      - Create engaging, well-structured content
      - Adapt tone for target audience
      - Follow SEO best practices
      - Ensure clarity and readability
    temperature: 0.7
    max_tokens: 4000

  - id: "editor"
    name: "Content Editor"
    provider: "openai"
    model: "gpt-4"
    system_prompt: |
      You are a content editor. Your role:
      - Review content for accuracy and quality
      - Check grammar, style, and consistency
      - Ensure brand voice compliance
      - Suggest improvements
    temperature: 0.2
    max_tokens: 3000

  - id: "seo_optimizer"
    name: "SEO Optimizer"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: |
      You are an SEO specialist. Your role:
      - Optimize content for search engines
      - Suggest keywords and meta descriptions
      - Improve content structure
      - Enhance readability scores
    temperature: 0.4
    max_tokens: 2000

tools:
  - id: "web_research"
    name: "Web Research Tool"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.web_research"]
      env:
        SEARCH_API_KEY: "${SEARCH_API_KEY}"

  - id: "content_storage"
    name: "Content Storage"
    type: "memory"
    backend: "sqlite"
    connection_params:
      db_path: "content_pipeline.db"
      tables:
        drafts: "content_drafts"
        published: "published_content"
        research: "research_data"

  - id: "cms_integration"
    name: "CMS Integration"
    type: "plugin"
    plugin_config:
      module_path: "langswarm.plugins.cms"
      provider: "wordpress"
      api_url: "${CMS_API_URL}"
      api_key: "${CMS_API_KEY}"

  - id: "social_media"
    name: "Social Media Publisher"
    type: "plugin"
    plugin_config:
      module_path: "langswarm.plugins.social_media"
      platforms: ["twitter", "linkedin", "facebook"]

workflows:
  - id: "content_creation"
    name: "Full Content Creation Pipeline"
    steps:
      - agent_id: "researcher"
        tools: ["web_research", "content_storage"]
        task: "research_topic"
        outputs: ["research_data"]
      
      - agent_id: "writer"
        tools: ["content_storage"]
        task: "create_content"
        inputs: ["research_data"]
        outputs: ["draft_content"]
      
      - agent_id: "editor"
        tools: ["content_storage"]
        task: "edit_content"
        inputs: ["draft_content"]
        outputs: ["edited_content"]
      
      - agent_id: "seo_optimizer"
        tools: ["content_storage"]
        task: "optimize_seo"
        inputs: ["edited_content"]
        outputs: ["final_content"]
    
    final_step:
      agent_id: "writer"
      tools: ["cms_integration", "social_media"]
      task: "publish_content"
      inputs: ["final_content"]

  - id: "content_update"
    name: "Content Update Workflow"
    agent_id: "editor"
    tool_ids: ["content_storage", "cms_integration"]
    task: "update_existing_content"
    max_iterations: 3

memory:
  default_backend: "sqlite"
  cleanup_interval: 86400  # Daily cleanup
  max_memory_size: 1000000

observability:
  logging:
    level: "INFO"
    custom_fields:
      - content_type
      - workflow_stage
      - word_count
      - seo_score
  
  metrics:
    enabled: true
    custom_metrics:
      - content_production_rate
      - quality_score
      - time_to_publish
      - engagement_metrics
```

---

## 🔗 Integration Examples

### **9. External API Integration**

**Configuration**: `api_integration.yaml`
```yaml
# Integration with external APIs and services
agents:
  - id: "api_coordinator"
    name: "API Coordination Agent"
    provider: "openai"
    model: "gpt-4"
    system_prompt: "You coordinate API calls and data integration."
    temperature: 0.2
    max_tokens: 2048

tools:
  - id: "crm_integration"
    name: "CRM System"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.crm"]
      env:
        CRM_API_URL: "${CRM_API_URL}"
        CRM_API_KEY: "${CRM_API_KEY}"
        CRM_TIMEOUT: "30"

  - id: "payment_processor"
    name: "Payment Processing"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.payments"]
      env:
        STRIPE_SECRET_KEY: "${STRIPE_SECRET_KEY}"
        STRIPE_WEBHOOK_SECRET: "${STRIPE_WEBHOOK_SECRET}"

  - id: "analytics_api"
    name: "Analytics Service"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.analytics"]
      env:
        ANALYTICS_API_KEY: "${ANALYTICS_API_KEY}"
        ANALYTICS_PROJECT_ID: "${ANALYTICS_PROJECT_ID}"

  - id: "notification_hub"
    name: "Multi-Channel Notifications"
    type: "plugin"
    plugin_config:
      module_path: "langswarm.plugins.notifications"
      channels:
        email:
          provider: "sendgrid"
          api_key: "${SENDGRID_API_KEY}"
        sms:
          provider: "twilio"
          account_sid: "${TWILIO_ACCOUNT_SID}"
          auth_token: "${TWILIO_AUTH_TOKEN}"
        slack:
          webhook_url: "${SLACK_WEBHOOK_URL}"

workflows:
  - id: "customer_onboarding"
    name: "Customer Onboarding Process"
    agent_id: "api_coordinator"
    tool_ids: ["crm_integration", "payment_processor", "notification_hub"]
    steps:
      - task: "create_customer_record"
        tools: ["crm_integration"]
      - task: "setup_payment_method"
        tools: ["payment_processor"]
      - task: "send_welcome_notifications"
        tools: ["notification_hub"]
    max_iterations: 5
    error_handling: "rollback"

  - id: "data_sync"
    name: "Cross-Platform Data Synchronization"
    agent_id: "api_coordinator"
    tool_ids: ["crm_integration", "analytics_api"]
    schedule: "0 */6 * * *"  # Every 6 hours
    task: "sync_customer_data"
    max_iterations: 3

security:
  api_key_rotation_enabled: true
  api_key_rotation_days: 15
  
  # API-specific security
  external_api_security:
    rate_limiting: true
    request_timeout: 30
    retry_with_backoff: true
    max_retries: 3
```

### **10. Database Integration**

**Configuration**: `database_integration.yaml`
```yaml
# Multi-database integration setup
agents:
  - id: "data_agent"
    name: "Data Processing Agent"
    provider: "openai"
    model: "gpt-4"
    system_prompt: "You process and analyze data from multiple sources."
    temperature: 0.1
    max_tokens: 2048

tools:
  - id: "postgres_primary"
    name: "Primary PostgreSQL"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.postgresql"]
      env:
        DATABASE_URL: "${POSTGRES_PRIMARY_URL}"
        POOL_SIZE: "10"
        MAX_OVERFLOW: "20"

  - id: "mysql_analytics"
    name: "MySQL Analytics DB"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.mysql"]
      env:
        MYSQL_HOST: "${MYSQL_HOST}"
        MYSQL_USER: "${MYSQL_USER}"
        MYSQL_PASSWORD: "${MYSQL_PASSWORD}"
        MYSQL_DATABASE: "${MYSQL_DATABASE}"

  - id: "mongodb_logs"
    name: "MongoDB Logs"
    type: "mcp"
    server_config:
      command: "python"
      args: ["-m", "langswarm.mcp.tools.mongodb"]
      env:
        MONGODB_URI: "${MONGODB_URI}"
        MONGODB_DATABASE: "${MONGODB_DATABASE}"

  - id: "redis_cache"
    name: "Redis Cache"
    type: "memory"
    backend: "redis"
    connection_params:
      host: "${REDIS_HOST}"
      port: ${REDIS_PORT:6379}
      password: "${REDIS_PASSWORD}"
      db: 1

workflows:
  - id: "data_processing"
    name: "Multi-Database Processing"
    agent_id: "data_agent"
    tool_ids: ["postgres_primary", "mysql_analytics", "mongodb_logs", "redis_cache"]
    steps:
      - task: "extract_data"
        tools: ["postgres_primary", "mysql_analytics"]
      - task: "process_logs"
        tools: ["mongodb_logs"]
      - task: "cache_results"
        tools: ["redis_cache"]
    max_iterations: 3
    timeout_seconds: 300

memory:
  default_backend: "redis"
  backends:
    redis:
      host: "${REDIS_HOST}"
      port: ${REDIS_PORT:6379}
      password: "${REDIS_PASSWORD}"
      db: 0
      connection_pool: 20

# Database connection monitoring
observability:
  metrics:
    enabled: true
    database_metrics:
      - connection_pool_usage
      - query_execution_time
      - error_rates
      - transaction_counts
  
  alerts:
    database_alerts:
      - name: "connection_pool_exhausted"
        condition: "pool_usage > 0.9"
        duration: "2m"
      - name: "slow_queries"
        condition: "avg_query_time > 1000ms"
        duration: "5m"
```

---

## 🔄 Migration Examples

### **11. V1 to V2 Migration Example**

**V1 Configuration** (Before):
```python
# V1 agents.yaml
- identifier: "main_agent"
  name: "Main Agent"
  llm_provider: "langchain-openai"
  llm_model: "gpt-4"
  system_message: "You are a helpful assistant."
  temperature: 0.7
  max_tokens: 2048
  api_key: "${OPENAI_API_KEY}"

# V1 tools.yaml
- identifier: "filesystem_tool"
  name: "File System"
  tool_type: "mcp_tool"
  mcp_server:
    command: "python"
    args: ["-m", "langswarm.mcp.tools.filesystem"]

# V1 workflows.yaml
- identifier: "main_workflow"
  name: "Main Workflow"
  agent_identifier: "main_agent"
  tool_identifiers: ["filesystem_tool"]
  execution_settings:
    max_iterations: 10
    timeout: 300
```

**V2 Configuration** (After Migration):
```yaml
# V2 langswarm.yaml (migrated)
agents:
  - id: "main_agent"                    # identifier → id
    name: "Main Agent"
    provider: "openai"                  # langchain-openai → openai
    model: "gpt-4"                      # llm_model → model
    system_prompt: "You are a helpful assistant."  # system_message → system_prompt
    temperature: 0.7
    max_tokens: 2048
    api_key_env: "OPENAI_API_KEY"       # Secure environment variable handling

tools:
  - id: "filesystem_tool"              # identifier → id
    name: "File System"
    type: "mcp"                        # mcp_tool → mcp
    server_config:                     # mcp_server → server_config
      command: "python"
      args: ["-m", "langswarm.mcp.tools.filesystem"]

workflows:
  - id: "main_workflow"               # identifier → id
    name: "Main Workflow"
    agent_id: "main_agent"            # agent_identifier → agent_id
    tool_ids: ["filesystem_tool"]     # tool_identifiers → tool_ids
    max_iterations: 10               # Flattened from execution_settings
    timeout_seconds: 300             # timeout → timeout_seconds

# Added V2 enhancements
memory:
  default_backend: "sqlite"
  backends:
    sqlite:
      db_path: "memory.db"

server:
  host: "localhost"
  port: 8000

observability:
  logging:
    level: "INFO"
    format: "standard"
```

**Migration Command**:
```python
from langswarm.core.config import migrate_v1_config

# Migrate V1 to V2
config, warnings = migrate_v1_config(
    v1_config_path="./old_config",
    output_path="langswarm.yaml"
)

print(f"Migration completed with {len(warnings)} warnings")
for warning in warnings:
    print(f"⚠️  {warning.category}: {warning.message}")
```

---

## 📋 Configuration Template Usage

### **Loading Templates**

```python
from langswarm.core.config import load_template, save_config

# Load pre-built templates
simple_config = load_template("simple_chatbot")
dev_config = load_template("development_setup")
prod_config = load_template("production_setup")

# Customize template
dev_config.server.port = 8001
dev_config.observability.logging.level = "DEBUG"

# Save customized configuration
save_config(dev_config, "my_dev_config.yaml", include_comments=True)
```

### **Environment-Specific Setup**

```bash
#!/bin/bash
# setup_environment.sh

ENVIRONMENT=${1:-development}

case $ENVIRONMENT in
  "development")
    cp examples/development.yaml langswarm.yaml
    cp .env.development .env
    echo "Development environment configured"
    ;;
  "production")
    cp examples/production.yaml langswarm.yaml
    cp .env.production .env
    echo "Production environment configured"
    ;;
  "testing")
    cp examples/testing.yaml langswarm.yaml
    cp .env.testing .env
    echo "Testing environment configured"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Available: development, production, testing"
    exit 1
    ;;
esac

# Validate configuration
python -c "
from langswarm.core.config import load_config, validate_config
config = load_config('langswarm.yaml')
is_valid, report = validate_config(config)
if is_valid:
    print('✅ Configuration is valid')
else:
    print('❌ Configuration has issues:')
    for issue in report.issues:
        print(f'  {issue.severity}: {issue.message}')
"
```

---

**These examples provide practical, real-world configurations for various LangSwarm V2 use cases, demonstrating best practices for development, production, and specialized deployments.**

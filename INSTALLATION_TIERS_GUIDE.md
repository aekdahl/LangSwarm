# LangSwarm Installation Tiers Guide

## 🏃 Minimal Installation: `pip install langswarm`

### What You Get (9 core dependencies):
- **pyyaml** - Configuration file parsing
- **nest-asyncio** - Async/await support  
- **pydantic** - Data validation and schemas
- **tiktoken** - Token counting for cost estimation
- **requests** - HTTP client for API calls
- **aiohttp** - Async HTTP client
- **websockets** - WebSocket support for real-time features
- **jinja2** - Template rendering
- **openai** - OpenAI API client (GPT models)

### What Works:
✅ **Configuration System** - Full YAML configuration parsing  
✅ **Core Framework** - Agent interfaces, error handling, validation  
✅ **OpenAI Provider** - GPT-4o, GPT-4, GPT-3.5-turbo support  
✅ **SQLite Memory** - Local conversation storage and retrieval  
✅ **Workflow Engine** - Multi-agent orchestration logic  
✅ **Session Management** - Conversation state tracking  
✅ **Template System** - Dynamic prompt generation  
✅ **Error Handling** - Rich error messages and debugging  
✅ **Function Calling** - Tool integration with OpenAI models  

### What You Can Do:
- **Create GPT-powered agents** - Immediate access to OpenAI models
- **Build multi-agent workflows** - Orchestrate multiple AI agents
- **Store conversations locally** - SQLite-based conversation memory
- **Use function calling** - Integrate tools with GPT models
- **Template-based prompts** - Dynamic prompt generation
- **Cost tracking** - Monitor token usage and costs
- **Stream responses** - Real-time AI responses

### What's Missing:
❌ **Other AI Providers** - Only OpenAI included (no Anthropic, Google, etc.)  
❌ **Cloud Memory** - Only SQLite available  
❌ **Communication Platforms** - No Discord, Slack, etc.  
❌ **Web Frameworks** - No FastAPI, Flask servers  

### Perfect For:
- **Getting Started** - Immediate access to powerful AI with minimal setup
- **Prototyping** - Quick experiments with GPT models
- **Learning LangSwarm** - Full AI capabilities without complexity
- **Simple Applications** - Single-provider solutions
- **Development/Testing** - Fast CI/CD with core AI functionality

---

## 🚀 Additional Providers: `pip install langswarm[providers]`

### Additional Dependencies:
- **anthropic** - Claude API client
- **google-generativeai** - Gemini API client  
- **cohere** - Cohere API client
- **mistralai** - Mistral API client

### What This Adds:
✅ **Claude Models** - Anthropic's Claude 3 Opus, Sonnet, Haiku  
✅ **Gemini Models** - Google's Gemini Pro and Ultra  
✅ **Cohere Models** - Command and embedding models  
✅ **Mistral Models** - Mistral 7B, Mixtral, and large models  
✅ **Provider Redundancy** - Fallback between different providers  
✅ **Cost Optimization** - Choose optimal provider per request  

### Perfect For:
- **Production Systems** - Multiple provider redundancy
- **Cost Optimization** - Use cheapest/best model per task
- **Feature Diversity** - Different models for different capabilities

---

## 🎯 Essential Setup: `pip install langswarm[essential]`

### What's Included:
```python
essential = ["anthropic", "google-generativeai", "cohere", "mistralai", "redis", "aioredis", "fastapi", "uvicorn"]
```

### Additional Capabilities:
✅ **All AI Providers** - OpenAI + Anthropic + Google + Cohere + Mistral  
✅ **Redis Memory** - Fast, scalable conversation storage  
✅ **FastAPI Web Framework** - REST APIs and webhooks  
✅ **Async Redis** - High-performance async memory operations  
✅ **Production Web Server** - Uvicorn ASGI server  
✅ **Provider Fallback** - Automatic failover between providers  

### What This Enables:
- **Web APIs** - HTTP endpoints for your agents
- **Scalable Memory** - Redis for production conversation storage
- **Webhook Support** - Integration with external services
- **Real-time Applications** - WebSocket support with FastAPI
- **Multi-user Systems** - Session management with Redis

### Perfect For:
- **Development Projects** - Full-featured development environment
- **Small Production Apps** - Single-provider production deployments
- **API Services** - Building agent APIs and webhooks
- **Team Development** - Shared Redis for collaboration

---

## 🏭 Production Setup: `pip install langswarm[production]`

### What's Included:
```python
production = [
    "anthropic",        # Claude models (+ OpenAI included by default)
    "redis",            # Redis memory backend
    "aioredis",         # Async Redis support
    "fastapi",          # Web framework
    "uvicorn",          # ASGI server
    "google-cloud-bigquery"  # Analytics-ready storage
]
```

### Production Features:
✅ **Key AI Providers** - OpenAI + Anthropic for reliability  
✅ **Redis Memory** - Production-grade conversation storage  
✅ **BigQuery Integration** - Analytics and data warehousing  
✅ **Web Framework** - Full REST API capabilities  
✅ **Provider Redundancy** - Fallback between OpenAI and Anthropic  
✅ **Enterprise Memory** - Cloud-scale conversation analytics  

### What This Enables:
- **High Availability** - Multiple provider fallback
- **Data Analytics** - Conversation analytics with BigQuery
- **Enterprise Integration** - Google Cloud ecosystem
- **Scalable APIs** - Production web services
- **Cost Optimization** - Choose optimal provider per request
- **Compliance** - BigQuery for data governance

### Perfect For:
- **Production Applications** - Customer-facing services
- **Enterprise Deployments** - Business-critical systems
- **Analytics Platforms** - Data-driven AI applications
- **Multi-tenant SaaS** - Cloud-native applications

---

## 🌟 Full Installation: `pip install langswarm[all]`

### Everything Included:
- **All AI Providers** - OpenAI, Anthropic, Google, Cohere, Mistral
- **All Memory Backends** - Redis, ChromaDB, Qdrant, Pinecone, BigQuery, PostgreSQL
- **All Communication Platforms** - Discord, Telegram, Slack, Twilio
- **All Web Frameworks** - FastAPI, Flask
- **All Cloud Services** - Google Cloud, AWS
- **ML Frameworks** - LangChain, LlamaIndex, Transformers
- **Multimodal Support** - Image and audio processing
- **Development Tools** - Jupyter, IPython
- **Infrastructure** - Docker, Cloud Functions

### What This Enables:
✅ **Every Feature** - Complete LangSwarm functionality  
✅ **Platform Integrations** - Discord bots, Slack apps, etc.  
✅ **Advanced AI** - Multimodal, vision, audio capabilities  
✅ **Enterprise Cloud** - Full cloud platform integration  
✅ **Development Suite** - All development and debugging tools  

### Perfect For:
- **Exploration** - Trying all LangSwarm features
- **Large Organizations** - Teams with diverse needs
- **Platform Development** - Building on top of LangSwarm
- **Research Projects** - Academic and experimental work

---

## Comparison Matrix

| Feature | Minimal | OpenAI | Essential | Production | Full |
|---------|---------|--------|-----------|------------|------|
| **Install Size** | ~20MB | ~40MB | ~80MB | ~120MB | ~300MB+ |
| **Dependencies** | 9 | 13 | 17 | 15 | 50+ |
| **AI Providers** | OpenAI | All Providers | All Providers | OpenAI + Anthropic | All |
| **Memory Backends** | SQLite | SQLite | SQLite + Redis | Redis + BigQuery | All |
| **Web Framework** | None | None | FastAPI | FastAPI | All |
| **Platforms** | None | None | None | None | All |
| **Cloud Integration** | None | None | None | BigQuery | All |
| **Use Case** | Learning | Prototyping | Development | Production | Everything |

---

## Migration Path

### Start Small, Scale Up:
```bash
# 1. Learn the framework
pip install langswarm

# 2. Add AI capabilities  
pip install langswarm[openai]

# 3. Scale to production
pip install langswarm[production] 

# 4. Add specific features as needed
pip install langswarm[platforms]  # Discord, Slack, etc.
pip install langswarm[memory]     # Vector stores
```

### Check What You Have:
```bash
python -m langswarm.cli.deps check
```

This tiered approach lets users start minimal and add capabilities as their needs grow, avoiding the "kitchen sink" problem while maintaining full functionality when needed.
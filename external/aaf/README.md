# AAF Backend

A LangSwarm-powered chatbot backend designed for company websites, featuring BigQuery memory storage and WebSocket support.

## Features

- **LangSwarm Integration**: Full LangSwarm agent system with conversation memory
- **BigQuery Memory**: Persistent conversation storage in Google BigQuery
- **WebSocket Support**: Real-time chat interface with streaming responses
- **REST API**: Complete HTTP API for chat and management
- **Management API**: Configuration management and agent control
- **Website Demo**: Reproduce customer websites with integrated chat UI
- **AI-Powered Design**: Auto-generate chat UI designs based on website analysis
- **Smart Prompts**: AI-generated personalized system prompts for each company
- **Chat Widget**: Customizable chat widget with multiple themes and positions
- **Production Widget**: Embeddable React chat widget with CDN delivery and tenant configuration
- **Multi-Tool System**: Multiple instances of web scrapers and Vector Search RAG tools from various sources
- **Cloud Run Ready**: Optimized for Google Cloud Run deployment

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with BigQuery enabled
- OpenAI API key

### Environment Setup

1. Copy the environment template:
```bash
cp env.example .env
```

2. Edit `.env` with your configuration:
```bash
# Required Variables
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-secret-key-for-jwt-tokens
MANAGEMENT_API_SECRET=your-management-api-secret-key
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID for BigQuery | `my-project-123` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `SECRET_KEY` | Secret key for JWT tokens | `your-secret-key` |
| `MANAGEMENT_API_SECRET` | Management API authentication | `your-mgmt-secret` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGSWARM_CONFIG_PATH` | `/app/config/langswarm.yaml` | Path to LangSwarm config |
| `LOG_LEVEL` | `INFO` | Logging level |
| `BIGQUERY_DATASET_ID` | `aaf_chatbot_memory` | BigQuery dataset |
| `BIGQUERY_TABLE_ID` | `conversations` | BigQuery table |
| `SESSION_BACKEND` | `bigquery` | Session storage backend |
| `SESSION_TTL` | `3600` | Session timeout in seconds |
| `APP_HOST` | `0.0.0.0` | Application host |
| `APP_PORT` | `8000` | Application port |
| `PORT` | `8080` | Cloud Run port |
| `DEFAULT_AGENT_MODEL` | `gpt-4` | Default LLM model |
| `DEFAULT_AGENT_BEHAVIOR` | `helpful` | Default agent behavior |
| `MEMORY_ENABLED` | `true` | Enable conversation memory |
| `MEMORY_BACKEND` | `bigquery` | Memory storage backend |

### Google Cloud Configuration

For BigQuery integration, you need:

1. **Service Account**: Create a service account with BigQuery permissions
2. **Credentials**: Set `GOOGLE_APPLICATION_CREDENTIALS` to the service account JSON file path
3. **Project Setup**: Ensure the GCP project has BigQuery API enabled

## API Endpoints

### Chat API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/` | Send chat message |
| `POST` | `/api/chat/stream` | Stream chat response |
| `GET` | `/api/chat/agents` | List available agents |
| `GET` | `/api/chat/agents/{id}` | Get agent information |
| `POST` | `/api/chat/sessions/{id}/reset` | Reset session |
| `GET` | `/api/chat/sessions/{id}` | Get session info |
| `GET` | `/api/chat/sessions` | List active sessions |
| `GET` | `/api/chat/sessions/stats` | Session statistics |

### WebSocket API

| Endpoint | Description |
|----------|-------------|
| `WS` | `/api/ws` | WebSocket chat interface |
| `GET` | `/api/ws/stats` | WebSocket statistics |

### Management API

All management endpoints require authentication via `Authorization: Bearer <MANAGEMENT_API_SECRET>`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/management/config` | Get configuration |
| `PUT` | `/api/management/config` | Update configuration |
| `POST` | `/api/management/agents` | Create/update agent |
| `GET` | `/api/management/agents` | List agents |
| `GET` | `/api/management/agents/{id}` | Get agent config |
| `PUT` | `/api/management/agents/{id}` | Update agent |
| `DELETE` | `/api/management/agents/{id}` | Delete agent |
| `POST` | `/api/management/restart` | Restart application |
| `GET` | `/api/management/health` | Management health check |

### Configuration Editor API

Frontend-friendly endpoints for visual configuration editing:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config-editor/current` | Get current config (frontend format) |
| `POST` | `/api/config-editor/validate` | Validate configuration |
| `PUT` | `/api/config-editor/update` | Update config with workflow |
| `GET` | `/api/config-editor/schema` | Get JSON schema for forms |
| `GET` | `/api/config-editor/templates` | Get configuration templates |
| `GET` | `/api/config-editor/agents` | Get agents (frontend format) |
| `POST` | `/api/config-editor/agents` | Create/update single agent |
| `DELETE` | `/api/config-editor/agents/{id}` | Delete agent |

## Usage Examples

### Chat via REST API

```bash
curl -X POST "http://localhost:8000/api/chat/" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hello, how can you help me?",
       "session_id": "user-123"
     }'
```

### WebSocket Chat (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.onopen = () => {
  // Send chat message
  ws.send(JSON.stringify({
    type: 'chat',
    data: {
      message: 'Hello!',
      stream: true
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Management API

```bash
# List agents
curl -X GET "http://localhost:8000/api/management/agents" \
     -H "Authorization: Bearer your-management-api-secret"

# Update configuration
curl -X PUT "http://localhost:8000/api/management/config" \
     -H "Authorization: Bearer your-management-api-secret" \
     -H "Content-Type: application/json" \
     -d '{"config": {...}}'
```

### Configuration Editor API

```bash
# Get current configuration (frontend format)
curl -X GET "http://localhost:8000/api/config-editor/current" \
     -H "Authorization: Bearer your-management-api-secret"

# Validate configuration
curl -X POST "http://localhost:8000/api/config-editor/validate" \
     -H "Authorization: Bearer your-management-api-secret" \
     -H "Content-Type: application/json" \
     -d '{
       "version": "1.0",
       "agents": [{"id": "test", "model": "gpt-4", "behavior": "helpful"}]
     }'

# Update configuration with workflow
curl -X PUT "http://localhost:8000/api/config-editor/update" \
     -H "Authorization: Bearer your-management-api-secret" \
     -H "Content-Type: application/json" \
     -d '{
       "config": {...},
       "validate_only": false,
       "backup_current": true,
       "restart_agents": true
     }'

# Get JSON schema for frontend forms
curl -X GET "http://localhost:8000/api/config-editor/schema" \
     -H "Authorization: Bearer your-management-api-secret"
```

### Demo API

The Demo API allows reproduction of customer websites with integrated chat UI for testing and showcasing:

```bash
# Reproduce website with chat widget
curl -X POST "http://localhost:8000/api/demo/website" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com",
       "chat_position": "bottom-right",
       "chat_theme": "light",
       "chat_title": "Chat with us",
       "enable_branding": false
     }'

# Simple website demo
curl "http://localhost:8000/api/demo/website-simple?url=https://example.com&chat_theme=dark"

# Chat widget preview
curl "http://localhost:8000/api/demo/preview"

# Generate embed code
curl "http://localhost:8000/api/demo/embed?chat_title=Support&chat_theme=brand"

# Get test URLs
curl "http://localhost:8000/api/demo/test-urls"

# AI-powered website analysis and design
curl -X POST "http://localhost:8000/api/demo/ai-analyze?url=https://example.com"

# Generate demo with AI design
curl -X POST "http://localhost:8000/api/demo/website" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com",
       "use_ai_design": true,
       "use_ai_prompt": true
     }'
```

**Demo Features:**
- 🤖 **AI-Powered Design**: Automatically matches website branding and style
- 💬 **Smart Prompts**: Generates personalized agent prompts for each company
- 🎨 **Multiple Themes**: Light, dark, brand, and AI-generated custom themes
- 📍 **Flexible Positioning**: Four corner positions with AI optimization
- 📱 **Mobile Responsive**: Automatic mobile optimization
- 🎯 **Custom Styling**: CSS customization support
- ⚡ **Real-time Chat**: Live integration with AAF agents
- 🔒 **Secure Rendering**: Safe website reproduction
- 🌍 **Multi-Language**: Automatic language detection and localization

### Production Widget API

The unified widget architecture provides tenant-based configuration and JWT authentication:

```bash
# Get tenant UI configuration
curl "http://localhost:8000/api/tenants/demo/ui-config"

# Create authenticated session
curl -X POST "http://localhost:8000/api/tenants/session" \
     -H "Content-Type: application/json" \
     -d '{
       "tenant_id": "demo",
       "user_id": "user123",
       "metadata": {"source": "website"}
     }'

# Send chat message (authenticated)
curl -X POST "http://localhost:8000/api/chat/send" \
     -H "Authorization: Bearer <jwt_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "sess_demo_abc123",
       "message": "Hello!"
     }'

# Upload file attachment
curl -X POST "http://localhost:8000/api/uploads/" \
     -H "Authorization: Bearer <jwt_token>" \
     -F "file=@document.pdf"
```

**Widget Integration:**
```html
<!-- Simple embed -->
<script
  src="https://cdn.algorithma.dev/aaf/aaf.js"
  async
  data-tenant="your_tenant_id"
  data-env="prod"
  data-mount="#aaf-chat"
></script>
<div id="aaf-chat"></div>
```

**Widget Features:**
- 🎯 **Tenant-Specific**: Runtime configuration per customer
- 🔐 **JWT Authentication**: Secure session-based authentication
- 📎 **File Uploads**: Secure file attachment support
- 🌐 **WebSocket + HTTP**: Real-time and fallback communication
- 🎨 **AI-Themed**: Automatic brand matching with website analysis
- 📱 **Mobile First**: Responsive design with accessibility compliance
- 🏗️ **Lovable-Generated**: Template-based React components via CI

### Custom Tools API

AAF includes integrated tools for enhanced agent capabilities:

```bash
# List available tools
curl "http://localhost:8000/api/tools/"

# Web scraping with crawl4ai MCP
curl -X POST "http://localhost:8000/api/tools/web-scraper/scrape" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com",
       "extract_text": true,
       "extract_metadata": true,
       "remove_ads": true
     }'

# Load documents for semantic search
curl -X POST "http://localhost:8000/api/tools/vector-rag/load" \
     -H "Content-Type: application/json" \
     -d '{
       "source_type": "file",
       "source_path": "/path/to/document.txt",
       "collection_name": "knowledge_base",
       "title": "Product Documentation"
     }'

# Semantic search with natural language
curl -X POST "http://localhost:8000/api/tools/vector-rag/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "How do I configure the payment gateway?",
       "collection_name": "knowledge_base",
       "limit": 5
     }'
```

**Multi-Tool Features:**
- 🔧 **Multiple Tool Instances**: Configure multiple scrapers and RAG tools
- 🎯 **Smart Tool Selection**: Automatic selection based on tags and priorities
- 🏷️ **Tag-Based Routing**: Route requests to specialized tools (news, ecommerce, etc.)
- 🔄 **High Availability**: Failover between primary and backup tools
- 📁 **Flexible Configuration**: Environment, file, and API-based configuration
- 🌐 **Web Scraping**: Remote crawl4ai MCP integration for content extraction
- 🧠 **Vector Search RAG**: BigQuery Vector Search with semantic similarity
- 🔍 **Natural Language Search**: No SQL required - use plain English queries
- 📚 **Document Collections**: Organize knowledge by topic or source
- ⚡ **Auto-Embedding**: Automatic text chunking and embedding generation
- 🤖 **LangSwarm Integration**: Tools automatically available to all agents
- 📈 **Batch Processing**: Handle multiple URLs or large documents efficiently
- 🛡️ **Error Handling**: Robust error handling with detailed responses

### Multi-Tool API Examples

```bash
# List all available tools
curl "http://localhost:8000/api/multi-tools/"

# Get tools by type
curl "http://localhost:8000/api/multi-tools/by-type/web_scraper"

# Get tools by tag (e.g., news-specialized scrapers)
curl "http://localhost:8000/api/multi-tools/by-tag/news"

# Smart web scraping (automatically selects best scraper)
curl -X POST "http://localhost:8000/api/multi-tools/web-scraper/scrape" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://news.example.com/article",
       "prefer_tags": ["news", "specialized"],
       "extract_text": true
     }'

# Smart vector search (automatically selects best RAG tool)
curl -X POST "http://localhost:8000/api/multi-tools/vector-rag/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "How do I reset my password?",
       "prefer_tags": ["customer_support"],
       "limit": 5
     }'

# Call specific tool by ID
curl -X POST "http://localhost:8000/api/multi-tools/call" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_id": "customer_support_rag",
       "function_name": "search_documents",
       "arguments": {
         "query": "billing questions",
         "limit": 3
       }
     }'

# Load documents into specific RAG tool
curl -X POST "http://localhost:8000/api/multi-tools/vector-rag/load" \
     -H "Content-Type: application/json" \
     -d '{
       "source_type": "file",
       "source_path": "/docs/api-guide.md",
       "collection_name": "api_docs",
       "prefer_tags": ["developer", "api"],
       "title": "API Developer Guide"
     }'
```

**Configuration Example:**
```yaml
# config/tools/specialized_tools.yaml
source:
  source_id: "specialized_config"

tools:
  - tool_id: "news_scraper"
    tool_type: "web_scraper"
    name: "News-Optimized Scraper"
    tags: ["news", "media", "specialized"]
    priority: 9
    config:
      mcp_server_url: "https://news-scraper.company.com"
      api_key: "${NEWS_SCRAPER_API_KEY}"

  - tool_id: "support_rag"
    tool_type: "vector_search_rag"
    name: "Customer Support Knowledge Base"
    tags: ["customer_support", "faq"]
    priority: 10
    config:
      project_id: "${GOOGLE_CLOUD_PROJECT}"
      dataset_id: "support_vectors"
```

## Cloud Run Deployment

### Build and Deploy

1. Set up Google Cloud CLI and authenticate
2. Build and push container:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/aaf-backend
```

3. Deploy to Cloud Run:

```bash
gcloud run deploy aaf-backend \
  --image gcr.io/YOUR_PROJECT/aaf-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT \
  --set-env-vars OPENAI_API_KEY=your-key \
  --set-env-vars SECRET_KEY=your-secret \
  --set-env-vars MANAGEMENT_API_SECRET=your-mgmt-secret
```

### Cloud Run Environment

The application automatically detects Cloud Run environment (`K_SERVICE` env var) and adjusts behavior accordingly:

- Uses Cloud Run port (`PORT` env var)
- Graceful shutdown handling
- Container restart capability via management API

## Memory and Storage

### BigQuery Memory

Conversations are automatically stored in BigQuery with the following schema:

- `key`: Unique message identifier
- `text`: Message content
- `metadata`: Additional message metadata
- `timestamp`: Message timestamp
- `session_id`: Conversation session ID
- `agent_id`: Agent that handled the message
- `user_input`: User message content
- `agent_response`: Agent response content

### Session Management

Sessions are managed via BigQuery and include:
- Session persistence across container restarts
- Conversation history tracking in BigQuery tables
- Session timeout handling with automatic cleanup
- Cross-agent session sharing
- Integrated analytics and session statistics

## Development

### Project Structure

```
aaf/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models
│   │   ├── chat.py             # Chat endpoints
│   │   ├── websocket.py        # WebSocket endpoints
│   │   └── management.py       # Management endpoints
│   └── core/
│       ├── __init__.py
│       ├── config.py           # Configuration management
│       └── langswarm_manager.py # LangSwarm integration
├── config/
│   └── langswarm.yaml          # LangSwarm configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml         # Local development
├── env.example                 # Environment template
└── README.md                   # This file
```

### Testing

1. Install development dependencies:
```bash
pip install pytest pytest-asyncio
```

2. Run tests:
```bash
pytest
```

### Logging

The application uses structured logging with configurable levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning conditions
- `ERROR`: Error conditions

Logs are output to stdout and can be collected by Cloud Run logging.

## Troubleshooting

### Common Issues

1. **BigQuery Authentication Error**
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account JSON
   - Verify service account has BigQuery permissions

2. **LangSwarm Initialization Failed**
   - Check that all required environment variables are set
   - Verify LangSwarm configuration syntax

3. **WebSocket Connection Issues**
   - Ensure CORS settings allow WebSocket connections
   - Check firewall/proxy WebSocket support

### Logs and Monitoring

- Application logs: Check stdout/stderr output
- Health checks: `GET /health` endpoint
- Management health: `GET /api/management/health` endpoint
- WebSocket stats: `GET /api/ws/stats` endpoint

## Security

### Authentication

- Management API requires Bearer token authentication
- Environment variables for sensitive configuration
- No hardcoded secrets in code

### Network Security

- CORS configuration for cross-origin requests
- Rate limiting (configurable)
- Input validation via Pydantic models

### Cloud Security

- Non-root container user
- Minimal container surface area
- Cloud Run managed security
- Service account least-privilege access

## Support

For issues related to:
- **LangSwarm**: Check the main LangSwarm documentation
- **BigQuery**: Google Cloud BigQuery documentation
- **Cloud Run**: Google Cloud Run documentation
- **This Application**: Create an issue in the project repository

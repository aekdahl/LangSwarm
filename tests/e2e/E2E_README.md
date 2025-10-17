# LangSwarm End-to-End Testing Framework

Comprehensive E2E testing system for LangSwarm with real API integrations, cloud resources, and multi-agent workflows.

## 🚀 Quick Start

### 1. Run Interactive Setup (Recommended)
```bash
# From LangSwarm root directory
cd tests/e2e
make interactive-setup
```

The interactive setup will:
- ✅ Check existing configuration
- ✅ Prompt for missing API keys
- ✅ Let you update any values
- ✅ Validate connections
- ✅ Save to .env automatically

### 2. Run Tests
```bash
# Run all tests
make test

# Or run basic tests only
make test-basic
```

## 📋 Setup Options

### Option 1: Interactive Setup (Recommended)
```bash
make interactive-setup
```
- ✅ Interactive prompts for all configuration
- ✅ Shows current values and lets you update
- ✅ Validates API keys as you enter them
- ✅ Saves everything to .env automatically
- ✅ Option to set up GCP resources

### Option 2: Quick Setup
```bash
./quick_setup.sh
```
- ✅ Installs Python dependencies
- ✅ Checks system requirements
- ✅ Creates configuration templates
- ✅ Validates environment

### Option 3: Comprehensive Setup
```bash
python3 setup_e2e_environment.py
```
- ✅ Everything from quick setup
- ✅ Sets up GCP service accounts
- ✅ Creates BigQuery datasets
- ✅ Configures cloud resources
- ✅ Full validation

### Option 4: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GCP_PROJECT="your-project"

# Run tests
python runner.py
```

## 🧪 Running Tests

### Using Makefile (Recommended)
```bash
# Show all available commands
make help

# Run all tests
make test

# Run specific categories
make test-orchestration  # Multi-agent workflows
make test-memory        # Memory backends
make test-integration   # Full stack tests

# Run with filters
make test PROVIDERS=openai MAX_COST=0.50
make test CATEGORY=basic PARALLEL=false
```

### Using Runner Directly
```bash
# Run all tests
python runner.py

# Filter by cost
python runner.py --max-cost 0.10

# Filter by providers
python runner.py --providers openai anthropic

# Filter by category
python runner.py --category memory

# Dry run (show what would execute)
python runner.py --dry-run

# Sequential execution
python runner.py --sequential
```

## 🏗️ Test Categories

### 📊 Orchestration Tests
Test multi-agent workflows and coordination:

- **BasicOrchestrationTest**: Two-agent workflow (researcher → summarizer)
- **MultiProviderOrchestrationTest**: Cross-provider workflows (OpenAI + Anthropic)
- **ParallelOrchestrationTest**: Multiple agents executing in parallel
- **ErrorRecoveryOrchestrationTest**: Error handling and recovery

**Cost**: ~$0.02-$0.15 per test  
**Requirements**: AI provider API keys

### 🧠 Memory Tests
Test memory backends and vector search:

- **SQLiteMemoryTest**: Local file-based memory operations
- **ChromaDBMemoryTest**: Vector database with embeddings
- **RedisMemoryTest**: Redis caching and search capabilities
- **BigQueryMemoryTest**: Cloud-scale vector search

**Cost**: $0.00-$0.05 per test  
**Requirements**: Database services, embedding APIs

### 🔗 Integration Tests
Test complete system integration:

- **FullStackIntegrationTest**: Config + orchestration + memory + workflows
- **ErrorHandlingIntegrationTest**: Cross-system error validation

**Cost**: ~$0.15-$0.25 per test  
**Requirements**: Multiple providers, cloud services

## 🛠️ Configuration

### Environment Variables
```bash
# Required: At least one AI provider
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Additional providers
GOOGLE_API_KEY=your-google-key
COHERE_API_KEY=your-cohere-key
MISTRAL_API_KEY=your-mistral-key

# GCP (for BigQuery tests)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_PROJECT=your-gcp-project-id

# Database services
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://localhost:5432/langswarm_test
```

## 📁 Framework Structure

```
tests/e2e/
├── setup_e2e_environment.py  # Comprehensive setup script
├── quick_setup.sh            # Quick setup script
├── runner.py                 # Test execution engine
├── Makefile                  # Easy commands
├── requirements.txt          # Python dependencies
├── 
├── framework/               # Testing framework
│   └── base.py             # BaseE2ETest, TestEnvironment
├── 
├── tests/                  # Test implementations
│   ├── orchestration_tests.py  # Multi-agent workflows
│   ├── memory_tests.py         # Memory backends
│   └── integration_tests.py    # Full stack tests
├── 
├── debug/                  # Monitoring and debugging
│   └── monitor.py         # SystemMonitor, RealTimeDebugger
├── 
├── config/                # Configuration files
├── credentials/           # Service account keys
├── results/              # Test results and reports
└── artifacts/            # Test logs and debugging data
```

## 🔧 Troubleshooting

### Common Issues

**1. Missing API Keys**
```bash
# Check current environment
make env-check

# Set missing keys
export OPENAI_API_KEY="your-key"
```

**2. GCP Authentication**
```bash
# Install and authenticate gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**3. Redis Connection**
```bash
# Start Redis locally
redis-server

# Or use Docker
make docker-redis
```

**4. Import Errors**
```bash
# Install missing dependencies
make install-deps

# Check what's available
make check-deps
```

---

**Happy Testing! 🚀**
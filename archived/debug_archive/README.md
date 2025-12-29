# LangSwarm Debug System

A comprehensive debugging system organized by scenarios for testing and debugging different aspects of LangSwarm with real data and live services.

## 🎯 Philosophy

This debug system is designed for **real-world debugging scenarios** with:
- **Actual API keys and credentials**
- **Live data and real database connections**
- **Production-like testing environments**
- **Real cost implications and performance measurement**

**Not for:** Mock data, unit tests, or simulated environments.

## 🏗️ Structure

```
debug/
├── Makefile                     # Main interface for all debug scenarios
├── credentials_template.env     # Template for real credentials
├── README.md                   # This file
│
├── bigquery_vector_search/     # BigQuery vector search debugging
│   ├── debug_bigquery.py       # Specialized BigQuery debugger
│   ├── config.yaml            # BigQuery debug configuration
│   └── README.md              # BigQuery-specific documentation
│
├── workflows/                  # Workflow execution debugging (coming soon)
├── agents/                     # Agent behavior debugging (coming soon)
├── tools/                      # Tool integration debugging (coming soon)
├── memory/                     # Memory system debugging (coming soon)
└── core/                       # Core system debugging (coming soon)
```

## 🚀 Quick Start

### 1. Initial Setup
```bash
cd debug
make setup
```

This will:
- Create `.env` template in debug folder
- Set up debug directories
- Check Python dependencies

### 2. Configure Credentials
Edit the `.env` file with your real credentials:
```bash
# Edit with your actual API keys
nano .env
```

### 3. Validate Environment
```bash
make check-env
```

### 4. Run Debug Scenarios
```bash
# List available scenarios
make list-scenarios

# Debug BigQuery vector search
make debug-bigquery

# Custom query
make debug-bigquery QUERY="your search query"

# Performance benchmark
make debug-bigquery-benchmark
```

## 📋 Available Scenarios

### ✅ BigQuery Vector Search
**Status:** Fully implemented and tested
**Purpose:** Debug vector similarity search operations

```bash
make debug-bigquery
make debug-bigquery QUERY="custom search query"
make debug-bigquery-benchmark
```

**What it tests:**
- BigQuery connectivity and authentication
- Table schema validation
- Vector embedding generation
- Similarity search performance
- Query optimization

### 🚧 Workflows (Coming Soon)
**Purpose:** Debug workflow execution with real LLM calls

```bash
make debug-workflows
```

### 🚧 Agents (Coming Soon)
**Purpose:** Debug agent behavior and responses

```bash
make debug-agents
```

### 🚧 Tools (Coming Soon)
**Purpose:** Debug tool integration and execution

```bash
make debug-tools
```

### 🚧 Memory (Coming Soon)
**Purpose:** Debug memory systems and persistence

```bash
make debug-memory
```

## 🔐 Credential Management

### Required Credentials
- **OPENAI_API_KEY** - OpenAI API key for embeddings and LLM operations
- **GOOGLE_CLOUD_PROJECT** - Google Cloud project for BigQuery access

### Optional Credentials
- **ANTHROPIC_API_KEY** - For Claude model debugging
- **GOOGLE_APPLICATION_CREDENTIALS** - Service account file path

### Security Best Practices
1. Never commit `.env` file to version control
2. Use environment variables in production
3. Rotate API keys regularly
4. Monitor API usage and costs
5. Limit permissions to minimum required

## 🛠️ Makefile Commands

### Setup and Validation
```bash
make setup          # Initial setup and credential template
make check-env       # Validate environment and credentials
make status          # Show current debug system status
```

### Scenario Execution
```bash
make debug-bigquery                    # Debug BigQuery vector search
make debug-bigquery QUERY="test"       # Custom query
make debug-bigquery-benchmark          # Performance benchmark
make debug-bigquery VERBOSE=1          # Verbose output
```

### Maintenance
```bash
make list-scenarios  # List all available debug scenarios
make clean          # Clean up debug traces and cache files
make help           # Show all available commands
```

### Advanced Options
```bash
# Environment variables for customization
QUERY="custom search query"    # Custom search query
VERBOSE=1                      # Enable verbose output
DRY_RUN=1                     # Show what would be done
```

## 📊 Current Status

### Implemented Scenarios: 1/6
- ✅ **BigQuery Vector Search** - Fully functional with real data testing
- 🚧 **Workflows** - Planned
- 🚧 **Agents** - Planned
- 🚧 **Tools** - Planned  
- 🚧 **Memory** - Planned
- 🚧 **Core** - Planned

### Test Results (BigQuery)
```
🗄️  Testing Real BigQuery Vector Search
========================================
✅ Table found: 31 rows, 4 columns
✅ Schema validation: embedding column detected
✅ Vector search: 5 results in 1.23s
✅ Performance: 2.1 queries/second
```

## 💰 Cost Awareness

This system makes real API calls that incur costs:

### OpenAI Costs
- Embedding generation: ~$0.0001 per query
- Credential validation: ~$0.001 per test
- LLM operations: Standard OpenAI pricing

### Google Cloud Costs
- BigQuery queries: Based on data processed
- Minimal costs for typical debug sessions

### Cost Control
- Use small test datasets
- Limit query frequency
- Monitor usage dashboards
- Set billing alerts

## 🐛 Troubleshooting

### Common Issues

**Authentication Problems**
```bash
# Google Cloud
gcloud auth application-default login
gcloud config set project your-project-id

# Check BigQuery access
bq ls your-dataset
```

**Missing Dependencies**
```bash
pip install google-cloud-bigquery openai pyyaml
```

**Environment Variables**
```bash
# Check .env file
cat ../.env

# Validate environment
make check-env
```

### Debug Output
All debug sessions create trace files:
```
debug_traces/bigquery_debug_YYYYMMDD_HHMMSS.json
```

Use these for:
- Performance analysis
- Error investigation
- Query optimization
- Integration debugging

## 🔮 Roadmap

### Phase 1: Core Scenarios (Current)
- ✅ BigQuery Vector Search
- 🚧 Workflow Execution
- 🚧 Agent Behavior

### Phase 2: Advanced Scenarios
- Tool Integration Debugging
- Memory System Validation
- Core System Testing

### Phase 3: Performance & Scale
- Load testing capabilities
- Performance benchmarking
- Optimization recommendations

### Phase 4: Automation
- Automated regression testing
- CI/CD integration
- Continuous monitoring

## 🎉 Benefits

**For Developers:**
- **Real-world feedback** from actual services
- **Production readiness** validation
- **Performance insights** with real data
- **Cost awareness** during development

**For Operations:**
- **End-to-end validation** of deployments
- **Troubleshooting tools** for production issues
- **Performance monitoring** capabilities
- **Cost optimization** insights

**For Users:**
- **Confidence** in system reliability
- **Transparent debugging** process
- **Real performance** expectations
- **Production-ready** workflows

The LangSwarm Debug System provides comprehensive, scenario-based debugging capabilities for production-ready LangSwarm deployments! 🚀

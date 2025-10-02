# LangSwarm Debug System - Quick Reference

## 🚀 **Main Commands**

### **Setup & Environment**
```bash
make setup              # Set up credentials and environment (.env file)
make check-env          # Check environment variables and credentials
make status             # Show current debug system status
make clean              # Clean up debug traces and temporary files
```

### **V2 System Testing** ⭐ **NEW**
```bash
make debug-v2           # Comprehensive V2 system test (all providers & tools)
```

### **Individual V2 Component Tests** 🔍 **NEW**
```bash
make debug-v2-registry          # V2 tool registry auto-discovery test
make debug-v2-openai-provider   # V2 OpenAI provider and tool integration test
make debug-v2-analytics         # V2 analytics and monitoring system test
make debug-v2-bigquery-tool     # V2 BigQuery tool specific test
make debug-v2-sql-tool          # V2 SQL database tool specific test
```

### **Individual BigQuery Tests** 🔍 **RECOMMENDED** *(Interactive)*
```bash
make debug-bigquery-knowledge-search      # BigQuery knowledge base search test (prompts for query)
make debug-bigquery-workflow-integration  # BigQuery LangSwarm workflow integration test (prompts for query)
make debug-bigquery-legacy-debug          # BigQuery comprehensive legacy debug test

# Or provide query directly:
make debug-bigquery-knowledge-search QUERY="Vad är Pingday?"
make debug-bigquery-workflow-integration QUERY="How does the platform work?"
```

### **Individual SQL Tests** 🗄️ **RECOMMENDED** *(Interactive)*
```bash
make debug-sql-data-analysis               # SQL data analysis and operations test
make debug-sql-workflow-integration        # SQL LangSwarm workflow integration test (prompts for query)
make debug-sql-performance                 # SQL performance and optimization test

# Or provide query directly:
make debug-sql-workflow-integration QUERY="Show me all employees in Engineering"
```

### **Legacy Combined Scenarios** (Use individual tests above instead)
```bash
make debug-bigquery                    # BigQuery vector search (V2 auto-injection)
make debug-bigquery-workflow           # BigQuery LangSwarm workflow integration
make debug-bigquery-legacy             # Legacy BigQuery debug (1074 lines)
make debug-bigquery-benchmark          # Performance testing
make debug-sql                         # SQL data analysis scenario
make debug-sql-workflow                # SQL database workflow integration
```

### **Help & Information**
```bash
make help                              # Main help (comprehensive overview)
make list-scenarios                    # List all available debug scenarios
make help-setup                        # Detailed setup instructions
make help-bigquery                     # BigQuery debugging help
make help-troubleshoot                 # Troubleshooting guide
make help-all                          # Complete help index
```

---

## 🎯 **Quick Start**

### **First Time Setup**
```bash
make setup              # Create .env file and directories
# Edit .env with your API keys
make check-env          # Validate setup
make debug-v2           # Test everything!
```

## 🎯 **Interactive Query Features** *(NEW)*

Many debug scenarios now **prompt you to select or enter queries**:

### **🔍 BigQuery Tests**
- **Pre-written options**: 5 common queries about Pingday platform
- **Custom input**: Enter your own search query
- **Command-line**: `make debug-bigquery-knowledge-search QUERY="your query"`

### **🗄️ SQL Tests**  
- **Pre-written options**: 5 common SQL analysis queries
- **Custom input**: Enter your own natural language SQL query
- **Command-line**: `make debug-sql-workflow-integration QUERY="your query"`

### **💡 Benefits**
- **Real testing** with your actual queries
- **Quick defaults** for fast debugging  
- **Flexible input** via command line or interactive prompts

### **Daily Usage**
```bash
make debug-v2           # Test V2 system (recommended)
make debug-bigquery     # Test BigQuery tools
make debug-sql          # Test SQL tools
```

---

## 🔧 **Command Options**

### **Available Options**
```bash
QUERY='your query'      # Custom search query
VERBOSE=1               # Enable verbose output
DRY_RUN=1               # Show what would be done without executing
```

### **Example Usage**
```bash
make debug-bigquery QUERY='AI workflows'           # Custom query
make debug-bigquery VERBOSE=1                      # Verbose output
make debug-bigquery QUERY='test' VERBOSE=1         # Both options
make debug-v2 DRY_RUN=1                            # Show commands only
```

---

## 📊 **Scenario Details**

### **🆕 V2 System Test** (`make debug-v2`) 
**Tests the complete enhanced V2 system:**
- ✅ All 6 LLM providers (OpenAI, Anthropic, Gemini, Cohere, Mistral, HuggingFace)
- ✅ Auto-discovery of 13+ MCP tools  
- ✅ Tool integration across providers
- ✅ Real-time analytics and monitoring
- ✅ Error handling and observability

**Output:** Comprehensive system status report

### **BigQuery Vector Search** (`make debug-bigquery`)
**Tests BigQuery vector similarity search:**
- ✅ V2 agent with automatic tool injection
- ✅ BigQuery connectivity and authentication
- ✅ Vector embedding generation (OpenAI)
- ✅ Similarity search performance

**Requirements:** BigQuery table with embeddings, OpenAI API key

### **SQL Database** (`make debug-sql`)
**Tests SQL database operations:**
- ✅ Creates temporary SQLite database
- ✅ SQL query execution and analysis
- ✅ V2 tool integration
- ✅ Workflow system testing

**Requirements:** None (uses SQLite)

---

## 🛠️ **Environment Setup**

### **Required Environment Variables**
```bash
# OpenAI (Required for most scenarios)
OPENAI_API_KEY=sk-your-openai-key

# BigQuery (Required for BigQuery scenarios)
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET_ID=your-dataset
BIGQUERY_TABLE_NAME=your-table
EMBEDDING_MODEL=text-embedding-3-small

# Optional Provider Keys
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-gemini-key
COHERE_API_KEY=your-cohere-key
MISTRAL_API_KEY=your-mistral-key
```

### **Google Cloud Authentication**
```bash
# One-time setup
gcloud auth application-default login
gcloud config set project your-project-id

# Verify access
bq ls --project_id=your-project
```

---

## 📈 **What Each Scenario Tests**

| Scenario | V2 System | Tools | Providers | Analytics | Real Data |
|----------|-----------|-------|-----------|-----------|-----------|
| `debug-v2` | ✅ Full | ✅ All 13 | ✅ All 6 | ✅ Yes | ✅ Yes |
| `debug-bigquery` | ✅ Partial | ✅ BigQuery | ✅ OpenAI | ❌ No | ✅ Yes |
| `debug-sql` | ✅ Partial | ✅ SQL | ✅ OpenAI | ❌ No | ✅ Yes |
| `debug-bigquery-legacy` | ❌ No | ❌ Manual | ✅ OpenAI | ❌ No | ✅ Yes |

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Authentication Failed**
```bash
gcloud auth application-default login
gcloud config set project your-project-id
```

#### **Environment Variables Missing**
```bash
make setup              # Create .env template
# Edit .env with real values
make check-env         # Validate
```

#### **BigQuery Table Not Found**
- Verify project/dataset/table names in .env
- Check BigQuery permissions
- Ensure table has 'embedding' column (ARRAY<FLOAT64>)

#### **OpenAI API Errors**
- Check API key format (starts with sk-)
- Verify account has credits
- Check rate limits

#### **Provider Package Missing**
```bash
# Install additional providers
pip install anthropic google-generativeai cohere mistralai transformers
```

### **Debug Output Locations**
- **Console**: Real-time progress and results
- **debug_traces/**: Detailed execution logs
- **Debug folder**: Configuration and setup files

---

## 🎯 **Recommended Workflow**

### **For V2 Development**
```bash
make debug-v2           # Test entire V2 system
```

### **For BigQuery Development**
```bash
make debug-bigquery     # Test BigQuery integration
```

### **For SQL Development**
```bash
make debug-sql          # Test SQL database tools
```

### **For Troubleshooting**
```bash
make check-env          # Verify environment
make debug-v2 VERBOSE=1 # Detailed V2 system check
make clean              # Clean up and start fresh
```

---

## 📚 **Additional Resources**

- **Setup Help**: `make help-setup`
- **BigQuery Help**: `make help-bigquery`  
- **Troubleshooting**: `make help-troubleshoot`
- **Complete Help**: `make help-all`
- **V2 Documentation**: `/docs/v2-tool-system.md`
- **Status Report**: `debug/V2_DEBUG_STATUS.md`

---

## ⚡ **Quick Reference Card**

```bash
# Essential Commands
make setup && make check-env           # Initial setup
make debug-v2                          # Test everything
make debug-bigquery                    # Test BigQuery
make clean                             # Clean up

# With Options
make debug-v2 VERBOSE=1                # Detailed output
make debug-bigquery QUERY='custom'     # Custom search
make help                              # Get help
```

**Happy Debugging! 🚀**

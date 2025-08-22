# 🏗️ BigQuery Memory Backend Setup Guide

## 📋 **Overview**

BigQuery is Google Cloud's fully-managed, serverless data warehouse that provides unlimited scale for analytics. When used as a LangSwarm memory backend, it offers:

- **Unlimited Scale**: Store millions of conversations
- **Analytics-Ready**: Built-in SQL analytics on all your agent data
- **Time-Series Analysis**: Powerful time-based queries and insights
- **Real-time Analytics**: Query conversation patterns as they happen
- **Enterprise-Grade**: 99.99% availability SLA

---

## 🚀 **Quick Setup (Auto-Detection)**

LangSwarm can **automatically detect and configure BigQuery** when you set up Google Cloud credentials:

### **Step 1: Set Environment Variables**
```bash
# Set up service account (required)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### **Step 2: Use Simple Configuration**
```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: "analytics-assistant"
    model: "gpt-4o"
    behavior: "helpful"
    memory: production  # ← Automatically detects BigQuery!
```

**That's it!** LangSwarm will automatically:
- ✅ Detect your Google Cloud credentials
- ✅ Select BigQuery as the optimal backend
- ✅ Create the dataset and tables if they don't exist
- ✅ Configure all necessary settings

---

## 🔧 **Detailed Setup Guide**

### **Step 1: Google Cloud Project Setup**

#### **1.1 Create or Select a Project**
```bash
# Install Google Cloud CLI (if not already installed)
# macOS:
brew install google-cloud-sdk

# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create your-langswarm-project
gcloud config set project your-langswarm-project

# Enable BigQuery API
gcloud services enable bigquery.googleapis.com
```

#### **1.2 Create Service Account**
```bash
# Create service account
gcloud iam service-accounts create langswarm-bigquery \
    --description="LangSwarm BigQuery Service Account" \
    --display-name="LangSwarm BigQuery"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-langswarm-project \
    --member="serviceAccount:langswarm-bigquery@your-langswarm-project.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"

# Create and download the key file
gcloud iam service-accounts keys create ~/langswarm-bigquery-key.json \
    --iam-account=langswarm-bigquery@your-langswarm-project.iam.gserviceaccount.com
```

### **Step 2: Install Dependencies**
```bash
# Install BigQuery client library
pip install google-cloud-bigquery

# Verify installation
python -c "from google.cloud import bigquery; print('✅ BigQuery client installed')"
```

### **Step 3: Set Environment Variables**
```bash
# Add to your ~/.bashrc, ~/.zshrc, or .env file
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/langswarm-bigquery-key.json"
export GOOGLE_CLOUD_PROJECT="your-langswarm-project"

# Reload your shell or run:
source ~/.bashrc  # or ~/.zshrc
```

### **Step 4: Test BigQuery Connection**
```python
# test_bigquery_connection.py
from google.cloud import bigquery

try:
    client = bigquery.Client()
    query = "SELECT 1 as test"
    result = client.query(query).result()
    print("✅ BigQuery connection successful!")
    for row in result:
        print(f"Test result: {row.test}")
except Exception as e:
    print(f"❌ BigQuery connection failed: {e}")
```

---

## 🎯 **Configuration Options**

### **Option 1: Auto-Detection (Recommended)**
```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: "assistant"
    model: "gpt-4o"
    memory: production  # Automatically uses BigQuery when detected
```

### **Option 2: Explicit BigQuery Configuration**
```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: "assistant"
    model: "gpt-4o"
    memory:
      backend: "bigquery"
      settings:
        project_id: "your-langswarm-project"
        dataset_id: "langswarm_memory"
        table_id: "agent_conversations"
        location: "US"  # or "EU", "asia-northeast1", etc.
```

### **Option 3: Advanced Configuration**
```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: "analytics-assistant"
    model: "gpt-4o"
    memory:
      backend: "bigquery"
      settings:
        project_id: "your-analytics-project"
        dataset_id: "langswarm_analytics"
        table_id: "ai_conversations"
        location: "US"
        
        # Advanced options
        retention_days: 365
        partitioning: "timestamp"
        clustering: ["agent_id", "session_id"]
        max_memory_size: "50GB"
```

---

## 📊 **BigQuery Schema**

LangSwarm automatically creates a table with this schema:

```sql
CREATE TABLE `your-project.langswarm_memory.agent_conversations` (
  key STRING NOT NULL,
  text STRING NOT NULL,
  metadata JSON,
  timestamp TIMESTAMP NOT NULL,
  session_id STRING,
  agent_id STRING,
  user_input STRING,
  agent_response STRING
);
```

### **Field Descriptions:**
- **`key`**: Unique identifier for each memory
- **`text`**: The raw conversation text or memory content
- **`metadata`**: Additional structured data (JSON)
- **`timestamp`**: When the memory was created
- **`session_id`**: Conversation session identifier
- **`agent_id`**: Which agent created this memory
- **`user_input`**: User's input (extracted from conversation)
- **`agent_response`**: Agent's response (extracted from conversation)

---

## 🔍 **Using BigQuery Analytics**

### **Query Examples**
```sql
-- Most active conversation sessions
SELECT 
  session_id,
  COUNT(*) as message_count,
  MIN(timestamp) as session_start,
  MAX(timestamp) as session_end
FROM `your-project.langswarm_memory.agent_conversations`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY session_id
ORDER BY message_count DESC
LIMIT 10;

-- Agent performance analytics
SELECT 
  agent_id,
  COUNT(*) as total_interactions,
  AVG(LENGTH(agent_response)) as avg_response_length,
  COUNT(DISTINCT session_id) as unique_sessions
FROM `your-project.langswarm_memory.agent_conversations`
WHERE agent_response IS NOT NULL
GROUP BY agent_id;

-- Conversation topics analysis
SELECT 
  EXTRACT(DATE FROM timestamp) as date,
  COUNT(*) as daily_messages,
  COUNT(DISTINCT session_id) as daily_sessions
FROM `your-project.langswarm_memory.agent_conversations`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date;
```

### **Python Analytics**
```python
from langswarm.memory.adapters._langswarm.bigquery.main import BigQueryAdapter

# Initialize adapter
adapter = BigQueryAdapter(
    identifier="analytics",
    project_id="your-project",
    dataset_id="langswarm_memory",
    table_id="agent_conversations"
)

# Get conversation summary
summary = adapter.get_conversation_summary(days=7)
print(f"Total messages: {summary['total_messages']}")
print(f"Unique sessions: {summary['unique_sessions']}")

# Custom analytics query
results = adapter.get_analytics("""
    SELECT agent_id, COUNT(*) as interactions
    FROM `your-project.langswarm_memory.agent_conversations`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    GROUP BY agent_id
""")

for row in results:
    print(f"Agent {row['agent_id']}: {row['interactions']} interactions")
```

---

## 🧪 **Testing Your Setup**

### **Quick Test Script**
```python
# test_bigquery_memory.py
import os
from langswarm.core.agents.simple import create_chat_agent
from langswarm.core.config import MemoryConfig

def test_bigquery_memory():
    print("🧪 Testing BigQuery Memory Setup...")
    
    # Test 1: Check environment variables
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("❌ GOOGLE_CLOUD_PROJECT not set")
        return False
    
    print("✅ Environment variables configured")
    
    # Test 2: Test memory configuration
    try:
        config = MemoryConfig.setup_memory("production")
        print(f"✅ Memory backend detected: {config.backend}")
        
        if config.backend == "bigquery":
            print("✅ BigQuery automatically selected!")
        else:
            print(f"ℹ️ Using {config.backend} (BigQuery not auto-detected)")
    
    except Exception as e:
        print(f"❌ Memory configuration failed: {e}")
        return False
    
    # Test 3: Create agent with BigQuery memory
    try:
        agent = create_chat_agent(
            "test-agent",
            memory_config={
                "backend": "bigquery",
                "settings": {
                    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
                    "dataset_id": "langswarm_memory_test",
                    "table_id": "test_conversations"
                }
            }
        )
        print("✅ Agent with BigQuery memory created")
        
        # Test memory storage
        response = agent.chat("Hello! This is a test message for BigQuery memory.")
        print(f"✅ Memory test completed: {len(response)} chars response")
        
        agent.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Agent creation or memory test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_bigquery_memory()
    if success:
        print("\n🎉 BigQuery memory setup successful!")
    else:
        print("\n❌ BigQuery memory setup needs attention")
```

---

## 💰 **Cost Considerations**

### **BigQuery Pricing (as of 2024)**
- **Storage**: $0.02 per GB per month
- **Queries**: $5 per TB processed
- **Free Tier**: 1 TB queries + 10 GB storage per month

### **Cost Optimization Tips**
1. **Use partitioning** by timestamp to reduce query costs
2. **Set retention policies** to automatically delete old data
3. **Use clustering** on frequently queried fields
4. **Monitor query costs** in Google Cloud Console

### **Example Costs**
```
Typical LangSwarm Usage:
- 10,000 conversations/month (~100 MB storage)
- 100 analytics queries/month (~1 GB processed)

Monthly Cost: ~$0.50-$1.00 (well within free tier)
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Authentication Error**
```
Error: Could not automatically determine credentials
```
**Solution:**
```bash
# Check if credentials file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth application-default login
```

#### **2. Project Not Found**
```
Error: Project not found or access denied
```
**Solution:**
```bash
# Verify project exists and you have access
gcloud projects list
gcloud config set project your-correct-project-id
```

#### **3. BigQuery API Not Enabled**
```
Error: BigQuery API has not been used in project
```
**Solution:**
```bash
# Enable BigQuery API
gcloud services enable bigquery.googleapis.com
```

#### **4. Permission Denied**
```
Error: User does not have permission to access dataset
```
**Solution:**
```bash
# Grant BigQuery admin role
gcloud projects add-iam-policy-binding your-project \
    --member="serviceAccount:your-service-account@your-project.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"
```

### **Debug Mode**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your BigQuery setup code here
# Detailed logs will show connection attempts and errors
```

---

## 🎯 **Best Practices**

### **Security**
- ✅ Use service accounts with minimal required permissions
- ✅ Store credentials securely (never in code)
- ✅ Rotate service account keys regularly
- ✅ Use IAM conditions to restrict access by IP/time

### **Performance**
- ✅ Use partitioning for large datasets
- ✅ Cluster frequently queried fields
- ✅ Set appropriate retention policies
- ✅ Monitor and optimize query patterns

### **Cost Management**
- ✅ Set up billing alerts
- ✅ Use dataset/table expiration
- ✅ Monitor query costs regularly
- ✅ Consider query caching for repeated analytics

### **Data Management**
- ✅ Implement backup strategies
- ✅ Use descriptive dataset/table names
- ✅ Document your schema and conventions
- ✅ Set up monitoring and alerting

---

## 🚀 **Next Steps**

1. **Start Simple**: Use `memory: production` for auto-detection
2. **Add Analytics**: Build dashboards with Google Data Studio
3. **Scale Up**: Implement data pipelines with Cloud Functions
4. **Monitor**: Set up alerts for usage and costs
5. **Optimize**: Fine-tune partitioning and clustering based on usage

**Your BigQuery memory backend is now ready for enterprise-scale AI agent deployments!** 🎉
# 📦 LangSwarm V2 Installation Guide

**Complete installation instructions for all environments and use cases.**

## 🎯 **Quick Installation**

### **Standard Installation**
```bash
pip install langswarm
```

### **Development Installation**
```bash
# Clone the repository
git clone https://github.com/aekdahl/langswarm.git
cd langswarm

# Install in development mode
pip install -e .
```

## 🔧 **System Requirements**

### **Python Version**
- **Python 3.8+** (recommended: Python 3.10+)
- **Operating Systems**: Windows, macOS, Linux

### **Dependencies**
LangSwarm V2 automatically installs all required dependencies:
- `openai>=1.79.0` - OpenAI API client
- `pydantic>=2.11.4` - Data validation
- `pyyaml>=6.0.2` - Configuration parsing
- `aiohttp>=3.11.18` - Async HTTP client
- `fastapi>=0.115.12` - Web framework (optional)

## 🚀 **Installation Options**

### **1. Basic Installation**
For most users who want to get started quickly:
```bash
pip install langswarm
```

### **2. Full Installation (Recommended)**
Includes all optional dependencies for maximum functionality:
```bash
pip install langswarm[all]
```

### **3. Specific Provider Installation**
Install only the providers you need:
```bash
# OpenAI only
pip install langswarm[openai]

# Anthropic only  
pip install langswarm[anthropic]

# Google (Gemini) only
pip install langswarm[google]

# Multiple providers
pip install langswarm[openai,anthropic,google]
```

### **4. Development Installation**
For contributors and advanced users:
```bash
git clone https://github.com/aekdahl/langswarm.git
cd langswarm
pip install -e .[dev,test]
```

## 🔑 **API Key Setup**

### **Required API Keys**
You'll need at least one LLM provider API key:

#### **OpenAI (Recommended)**
```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
```

#### **Anthropic**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
```

#### **Google (Gemini)**
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

### **Environment File Setup**
Create a `.env` file in your project directory:
```bash
# .env
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key
```

## 🐳 **Docker Installation**

### **Using Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  langswarm:
    image: langswarm/langswarm:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    ports:
      - "8000:8000"
```

Run with:
```bash
docker-compose up -d
```

### **Direct Docker Run**
```bash
docker run -d \
  --name langswarm \
  -e OPENAI_API_KEY="your-key" \
  -v $(pwd)/config:/app/config \
  -p 8000:8000 \
  langswarm/langswarm:latest
```

## ☁️ **Cloud Installation**

### **Google Cloud Platform**
```bash
# Install with GCP support
pip install langswarm[gcp]

# Set up authentication
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### **AWS**
```bash
# Install with AWS support
pip install langswarm[aws]

# Configure AWS credentials
aws configure
```

### **Azure**
```bash
# Install with Azure support
pip install langswarm[azure]

# Set up Azure authentication
az login
```

## ✅ **Verify Installation**

### **Basic Verification**
```python
import langswarm
print(f"LangSwarm version: {langswarm.__version__}")
```

### **Complete Verification**
```python
from langswarm.core.config import load_config
from langswarm.core.agents import create_openai_agent

# Test configuration loading
try:
    config = load_config()
    print("✅ Configuration system working")
except Exception as e:
    print(f"❌ Configuration error: {e}")

# Test agent creation
try:
    agent = create_openai_agent(model="gpt-3.5-turbo")
    print("✅ Agent system working")
except Exception as e:
    print(f"❌ Agent error: {e}")
```

### **Run Verification Script**
```bash
python -c "
from langswarm.core.agents import create_openai_agent
import asyncio

async def test():
    agent = create_openai_agent(model='gpt-3.5-turbo')
    response = await agent.chat('Hello!')
    print(f'✅ LangSwarm working! Response: {response.content[:50]}...')

asyncio.run(test())
"
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Import Errors**
```bash
# If you get import errors, try reinstalling
pip uninstall langswarm
pip install langswarm --no-cache-dir
```

#### **API Key Issues**
```bash
# Verify your API key is set
echo $OPENAI_API_KEY

# Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### **Permission Errors**
```bash
# Use user installation if you get permission errors
pip install --user langswarm
```

#### **Version Conflicts**
```bash
# Create a virtual environment to avoid conflicts
python -m venv langswarm-env
source langswarm-env/bin/activate  # On Windows: langswarm-env\Scripts\activate
pip install langswarm
```

### **Getting Help**
- **[Common Issues](../../troubleshooting/common-issues/README.md)** - Detailed troubleshooting
- **[FAQ](../../troubleshooting/faq/README.md)** - Frequently asked questions
- **[Community Support](../../community/support/README.md)** - Get help from the community

## 🎯 **Next Steps**

After successful installation:
1. **[Quickstart Guide](../quickstart/README.md)** - Get running in 30 seconds
2. **[First Project](../first-project/README.md)** - Build your first project
3. **[Configuration Guide](../../user-guides/configuration/README.md)** - Learn configuration

---

**🎉 Installation complete! Ready to build powerful AI systems with LangSwarm V2.**

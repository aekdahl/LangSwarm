# LangSwarm Clean Installation Strategy

## 🎯 **Philosophy: Install What You Need**

LangSwarm now follows a clean dependency approach:
- **Minimal core** - Only essential framework dependencies (8 packages)
- **User installs what they need** - Add providers/backends as required
- **Helpful error messages** - Clear guidance when dependencies are missing
- **Full option available** - For those who want everything pre-installed

## ✅ **Two Simple Options**

### 1. **Default: `pip install langswarm`**
**What you get:**
- Core LangSwarm framework (8 dependencies)
- Configuration system
- Workflow engine
- Session management
- Error handling with helpful messages

**You install what you need:**
```bash
# Need OpenAI? Install it:
pip install openai

# Need Redis? Install it:
pip install redis aioredis

# Need FastAPI? Install it:
pip install fastapi uvicorn
```

**When to use:** 
- You know what you need
- Want minimal dependencies
- Production environments with specific requirements
- Docker containers with controlled dependencies

### 2. **Full: `pip install langswarm[full]`**
**What you get:**
- Everything pre-installed
- All providers (OpenAI, Anthropic, Google, etc.)
- All memory backends (Redis, ChromaDB, etc.)
- All platforms (Discord, Slack, etc.)
- All frameworks (FastAPI, Flask, etc.)

**When to use:**
- Exploring LangSwarm capabilities
- Development environments
- Don't want to think about dependencies
- Trying different features

## 📊 **Comparison**

| Aspect | `langswarm` | `langswarm[full]` |
|--------|-------------|-------------------|
| **Dependencies** | 8 core | 50+ everything |
| **Download Size** | ~10MB | ~300MB+ |
| **Philosophy** | Add what you need | Everything included |
| **Best For** | Production, Docker | Development, Exploration |

## 🔧 **How It Works**

### **With Helpful Error Messages**

When you use a feature without its dependency:

```python
from langswarm import create_agent

# If OpenAI not installed:
agent = create_agent("gpt-4")
```

**You get:**
```
❌ Provider 'openai' requires missing dependencies: ['openai']

📦 To use OpenAI models, install the required package:
   pip install openai

💡 Or install all providers:
   pip install langswarm[full]

📚 See https://docs.langswarm.ai/providers/openai for setup guide
```

### **Examples of Helpful Errors**

**Missing Redis:**
```
❌ Redis memory backend requires: ['redis', 'aioredis']

📦 Install with:
   pip install redis aioredis

💡 Alternatively, use SQLite (built-in) or install all backends:
   pip install langswarm[full]
```

**Missing FastAPI:**
```
❌ Web API features require: ['fastapi', 'uvicorn']

📦 Install with:
   pip install fastapi uvicorn

💡 See https://docs.langswarm.ai/web-api for examples
```

## 🚀 **Common Installation Patterns**

### **For OpenAI Users**
```bash
pip install langswarm openai
export OPENAI_API_KEY="your-key"
```

### **For Multi-Provider Setup**
```bash
pip install langswarm openai anthropic google-generativeai
```

### **For Web APIs**
```bash
pip install langswarm openai fastapi uvicorn
```

### **For Production with Redis**
```bash
pip install langswarm openai redis aioredis
```

### **For Discord Bots**
```bash
pip install langswarm openai discord-py
```

## 💡 **Benefits of This Approach**

### ✅ **You Control Your Dependencies**
- Install only what you actually use
- No bloat from unused packages
- Explicit about what's in your environment

### ✅ **Smaller Attack Surface**
- Fewer dependencies = fewer security concerns
- Only audit packages you actually use
- Easier compliance for enterprise

### ✅ **Faster CI/CD**
- Minimal installs = faster builds
- Cache only what you need
- Reduced download times

### ✅ **Clear Error Messages**
- Know exactly what's missing
- Get installation commands
- Links to documentation

### ✅ **Flexibility**
- Mix and match components
- Different deps for different environments
- Easy to test with minimal setup

## 📖 **Migration Guide**

### **From Old Installation**
If you were using grouped installations:

| Old | New |
|-----|-----|
| `langswarm[openai]` | `pip install langswarm openai` |
| `langswarm[providers]` | `pip install langswarm openai anthropic google-generativeai` |
| `langswarm[essential]` | `pip install langswarm[full]` or install specific packages |

### **Docker Best Practice**
```dockerfile
# Minimal production image
FROM python:3.11-slim
RUN pip install langswarm openai redis aioredis
# Only what you need!
```

## 🎯 **Decision Tree**

```
Do you know exactly what providers/backends you need?
├─ YES → pip install langswarm + your specific dependencies
└─ NO → pip install langswarm[full]
        └─ Later: identify what you use and switch to minimal
```

## 📝 **Summary**

**Default (`langswarm`)**: 
- Clean, minimal installation
- You add what you need
- Best for production and experienced users

**Full (`langswarm[full]`)**: 
- Everything included
- Best for exploration and development
- Easy transition to minimal later

With our enhanced error messages, even the minimal installation provides a smooth experience by guiding you to install exactly what you need, when you need it.
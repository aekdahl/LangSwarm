# Custom Backend Integration Overview

## 🎯 **What This Is**
Your existing AI backend can be adopted by the orchestrator for **simple prompt management**. No complex features needed - just basic prompt control.

## ✅ **What You Get**
- **Centralized prompt management** across all your AI services
- **Web UI** for updating prompts without code deployments  
- **API integration** with the orchestrator system
- **Simple adoption process** - your service stays exactly as it is

## ❌ **What You DON'T Need**
- **Demo management** - no website demos or chat widgets
- **Knowledge base** - no web scraping or vector search  
- **Multi-tools** - no complex tool integrations
- **Complex configuration** - just simple prompt updates

## 🔧 **Requirements Summary**
To be adopted, your backend needs **4 simple endpoints**:

1. **Health check** (`/health`) - for service validation
2. **Prompt schema** (`/api/prompts/schema`) - defines what can be configured
3. **Get prompts** (`/api/prompts`) - returns current prompt values
4. **Update prompts** (`PUT /api/prompts`) - accepts new prompt values

## 📋 **Capabilities**
- ✅ **Can be adopted** for prompt management
- ✅ **Can be removed** from orchestrator tracking  
- ✅ **Can update prompts** via web UI
- ❌ **Cannot be created** by orchestrator (must already exist)
- ❌ **Cannot be deleted** by orchestrator (manual Cloud Run management only)

## 📚 **Next Steps**
1. Read `02_ENDPOINTS.md` - Required API endpoints
2. Read `03_IMPLEMENTATION.md` - Code examples
3. Read `04_ADOPTION.md` - How to register with orchestrator
4. Read `05_TROUBLESHOOTING.md` - Common issues and fixes

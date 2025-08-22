# Orchestrator Documentation

## 📚 **Documentation Structure**

### **🎨 Frontend Team**
Short, focused guides for implementing the orchestrator frontend:

- [`01_OVERVIEW.md`](frontend/01_OVERVIEW.md) - Backend types and feature differences
- [`02_BACKEND_TEMPLATES.md`](frontend/02_BACKEND_TEMPLATES.md) - Configuration structure  
- [`03_UI_CONDITIONALS.md`](frontend/03_UI_CONDITIONALS.md) - Feature-based UI implementation
- [`04_API_INTEGRATION.md`](frontend/04_API_INTEGRATION.md) - Orchestrator API calls
- [`05_PROMPT_EDITOR.md`](frontend/05_PROMPT_EDITOR.md) - Universal prompt management UI

### **🔧 Custom Backend Team**  
Step-by-step guides for integrating existing backends:

- [`01_OVERVIEW.md`](custom_backend/01_OVERVIEW.md) - What integration provides
- [`02_ENDPOINTS.md`](custom_backend/02_ENDPOINTS.md) - Required API endpoints
- [`03_IMPLEMENTATION.md`](custom_backend/03_IMPLEMENTATION.md) - Code examples
- [`04_ADOPTION.md`](custom_backend/04_ADOPTION.md) - Registration process
- [`05_TROUBLESHOOTING.md`](custom_backend/05_TROUBLESHOOTING.md) - Common issues

### **📖 Reference Documents**
- [`CUSTOM_BACKEND_REQUIREMENTS.md`](CUSTOM_BACKEND_REQUIREMENTS.md) - Full technical requirements
- [`README_UNIFIED_ORCHESTRATOR.md`](README_UNIFIED_ORCHESTRATOR.md) - Complete system overview

## 🎯 **Quick Start**

### **For Frontend Developers**
1. Start with [`frontend/01_OVERVIEW.md`](frontend/01_OVERVIEW.md)
2. Understand backend types and feature differences
3. Implement feature-based UI conditionals
4. Build the universal prompt editor

### **For Backend Developers**  
1. Start with [`custom_backend/01_OVERVIEW.md`](custom_backend/01_OVERVIEW.md)
2. Implement the 4 required endpoints
3. Test your integration
4. Adopt your backend via orchestrator API

## 📋 **Backend Feature Matrix**

| Feature | AAF Backend | Custom Backend |
|---------|-------------|----------------|
| **Prompt Management** | ✅ | ✅ |
| **Demo Management** | ✅ | ❌ |
| **Knowledge Base** | ✅ | ❌ |
| **Multi-Tools** | ✅ | ❌ |
| **Create/Deploy** | ✅ | ❌ |
| **Delete** | ✅ | ❌ |
| **Adopt Existing** | ✅ | ✅ |

## 🔧 **Key Concepts**

### **AAF Backend (Full Featured)**
- Complete AI chatbot platform with all features
- Deployable, manageable, deletable via orchestrator
- Includes demos, knowledge base, multi-tools

### **Custom Backend (Prompt Only)**
- Your existing AI service with simple prompt management
- Adoption-only (cannot create/delete via orchestrator)  
- **Only prompt management** - no complex features needed

### **Universal Prompt Management**
- Both backend types support prompt configuration
- Same API pattern: schema → get → update
- Frontend shows appropriate features based on backend type

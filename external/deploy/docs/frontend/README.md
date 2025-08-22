# Frontend Implementation Guide

## 📚 **Reading Order**

1. **[Overview](01_OVERVIEW.md)** - Start here to understand backend types and feature differences
2. **[Backend Templates](02_BACKEND_TEMPLATES.md)** - Learn the configuration structure that drives your UI
3. **[UI Conditionals](03_UI_CONDITIONALS.md)** - Implement feature-based UI components  
4. **[API Integration](04_API_INTEGRATION.md)** - Connect to the orchestrator API
5. **[Prompt Editor](05_PROMPT_EDITOR.md)** - Build the universal prompt management interface

## 🎯 **Key Implementation Points**

### **Feature-Based UI**
```javascript
const features = BACKEND_TEMPLATES[backend.type].features;

// AAF backend - show everything
if (features.demo_management) showDemoSection();
if (features.knowledge_base) showKnowledgeSection();

// Custom backend - only prompts  
if (features.prompt_management) showPromptEditor();
```

### **Backend Capabilities**
```javascript
const capabilities = BACKEND_TEMPLATES[backend.type].capabilities;

// Show action buttons based on what's allowed
if (capabilities.create) showCreateButton();
if (capabilities.delete) showDeleteButton(); 
if (capabilities.remove_from_admin) showRemoveButton();
```

### **Universal Prompt Editor**
Every backend type supports prompt management - this is the core shared feature. The prompt editor component should work with both AAF and custom backends.

## ⚡ **Quick Reference**

### **AAF Backend Features**
- ✅ Demo Management
- ✅ Knowledge Base  
- ✅ Multi-Tools
- ✅ Prompt Management
- ✅ Config Editor
- ✅ WebSocket Chat

### **Custom Backend Features**  
- ❌ Demo Management
- ❌ Knowledge Base
- ❌ Multi-Tools  
- ✅ Prompt Management (ONLY this)

### **API Endpoints**
```javascript
GET /api/backend-templates  // Get feature definitions
GET /api/backends          // List all backends
POST /api/backends         // Create backend (AAF only)
POST /api/backends/adopt   // Adopt backend (Custom only)
PUT /api/backends/:id/prompts  // Update prompts (Both)
DELETE /api/backends/:id   // Delete backend (AAF only)
```

## 🔧 **Implementation Strategy**

1. **Start with backend templates** - understand the feature matrix
2. **Build conditional components** - show/hide based on features
3. **Implement prompt editor** - works for all backend types
4. **Add AAF-specific features** - demos, knowledge base, tools
5. **Test with both backend types** - ensure UI adapts correctly

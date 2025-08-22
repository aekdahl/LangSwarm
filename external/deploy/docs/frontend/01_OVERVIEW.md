# Frontend Integration Overview

## 🎯 **Purpose**
The orchestrator manages two types of AI backends with different feature sets. Your frontend needs to adapt the UI based on backend capabilities.

## 📋 **Backend Types**

### **AAF Backend (Full Featured)**
```javascript
features: {
  demo_management: true,
  knowledge_base: true, 
  multi_tools: true,
  prompt_management: true,
  config_editor: true,
  websocket_chat: true
}
```

### **Custom Backend (Prompt Only)**
```javascript
features: {
  demo_management: false,
  knowledge_base: false,
  multi_tools: false,
  prompt_management: true  // ONLY this feature
}
```

## 🔧 **Key Concept**
Use the `features` object from backend templates to show/hide UI sections:

```javascript
import { BACKEND_TEMPLATES } from './config/backend_templates';

const backend = getSelectedBackend();
const features = BACKEND_TEMPLATES[backend.type].features;

// Show sections based on features
if (features.demo_management) showDemoSection();
if (features.knowledge_base) showKnowledgeSection();
if (features.prompt_management) showPromptEditor(); // Always shown
```

## 📚 **Next Steps**
1. Read `02_BACKEND_TEMPLATES.md` - Understanding the configuration
2. Read `03_UI_CONDITIONALS.md` - Implementing feature-based UI  
3. Read `04_API_INTEGRATION.md` - Connecting to orchestrator
4. Read `05_PROMPT_EDITOR.md` - Building the prompt management UI

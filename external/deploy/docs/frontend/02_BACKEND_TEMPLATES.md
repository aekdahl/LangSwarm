# Backend Templates Configuration

## 📋 **Template Structure**
Each backend type has a template defining its capabilities and features:

```javascript
// config/backend_templates.js
export const BACKEND_TEMPLATES = {
  "aaf": {
    name: "AAF Backend",
    description: "LangSwarm-powered chatbot backend with full lifecycle management",
    capabilities: {
      create: true,    // Can deploy new instances
      adopt: true,     // Can adopt existing instances  
      delete: true,    // Can delete instances
      update_prompts: true,
      remove_from_admin: false
    },
    features: {
      demo_management: true,
      knowledge_base: true,
      multi_tools: true,
      prompt_management: true,
      config_editor: true,
      websocket_chat: true
    }
  },
  "custom": {
    name: "Custom Backend", 
    description: "Existing custom AI backend with prompt management only",
    capabilities: {
      create: false,   // Cannot create (must exist)
      adopt: true,     // Can adopt existing
      delete: false,   // Cannot delete (manual only)
      update_prompts: true,
      remove_from_admin: true
    },
    features: {
      demo_management: false,
      knowledge_base: false, 
      multi_tools: false,
      prompt_management: true  // ONLY this
    }
  }
};
```

## 🔧 **Usage in Components**

```javascript
// Get template for current backend
const getBackendTemplate = (backendType) => {
  return BACKEND_TEMPLATES[backendType] || BACKEND_TEMPLATES.custom;
};

// Check if feature is available
const hasFeature = (backendType, feature) => {
  const template = getBackendTemplate(backendType);
  return template.features[feature] === true;
};

// Check if action is allowed
const canPerformAction = (backendType, action) => {
  const template = getBackendTemplate(backendType);
  return template.capabilities[action] === true;
};
```

## 📤 **API Integration**
The orchestrator `/api/backend-templates` endpoint returns this exact structure for dynamic UI generation.

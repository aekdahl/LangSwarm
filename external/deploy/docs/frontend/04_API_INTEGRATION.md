# Orchestrator API Integration

## 🔌 **Base Endpoints**

```javascript
const ORCHESTRATOR_BASE = process.env.ORCHESTRATOR_URL || 'http://localhost:8000';

// Core endpoints
const API = {
  backends: `${ORCHESTRATOR_BASE}/api/backends`,
  templates: `${ORCHESTRATOR_BASE}/api/backend-templates`,
  health: `${ORCHESTRATOR_BASE}/health`
};
```

## 📋 **Key API Calls**

### **1. Get Backend Templates**
```javascript
// Get available backend types and their features
const getBackendTemplates = async () => {
  const response = await fetch(`${API.templates}`);
  return response.json();
  // Returns: { aaf: {...}, custom: {...} }
};
```

### **2. List Backends**
```javascript
// Get all managed backends
const getBackends = async () => {
  const response = await fetch(`${API.backends}`);
  return response.json();
  // Returns: { backends: [...] }
};
```

### **3. Create Backend (AAF only)**
```javascript
const createBackend = async (config) => {
  const response = await fetch(`${API.backends}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  return response.json();
};
```

### **4. Adopt Backend (Custom)**
```javascript
const adoptBackend = async (config) => {
  const response = await fetch(`${API.backends}/adopt`, {
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  return response.json();
};
```

### **5. Update Prompts**
```javascript
const updatePrompts = async (backendId, prompts) => {
  const response = await fetch(`${API.backends}/${backendId}/prompts`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(prompts)
  });
  return response.json();
};
```

### **6. Delete Backend (AAF only)**
```javascript
const deleteBackend = async (backendId) => {
  const response = await fetch(`${API.backends}/${backendId}`, {
    method: 'DELETE'
  });
  return response.json();
};
```

## 🔄 **Error Handling**

```javascript
const apiCall = async (url, options = {}) => {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

## 📊 **Response Examples**

### **Backend List Response**
```json
{
  "backends": [
    {
      "id": "aaf-instance-123",
      "name": "Customer Support Bot", 
      "type": "aaf",
      "status": "running",
      "url": "https://...",
      "prompts": {
        "system_prompt": "You are a helpful support agent..."
      }
    }
  ]
}
```

### **Backend Templates Response**
```json
{
  "aaf": {
    "name": "AAF Backend",
    "features": {
      "demo_management": true,
      "knowledge_base": true,
      "multi_tools": true,
      "prompt_management": true
    }
  },
  "custom": {
    "name": "Custom Backend", 
    "features": {
      "prompt_management": true
    }
  }
}
```

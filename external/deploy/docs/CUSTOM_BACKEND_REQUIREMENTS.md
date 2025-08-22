# Custom Backend Requirements for Orchestrator Integration

This document outlines the requirements for custom backend instances to be compatible with the orchestrator's adoption and prompt management features.

## 🎯 **Overview**

Custom backends are **existing Cloud Run services** that can be adopted into the orchestrator for **simple prompt management only**. Unlike AAF backends, custom backends:

- ✅ **Cannot be created** by the orchestrator (must already exist)
- ✅ **Cannot be deleted** by the orchestrator (must be manually removed from Cloud Run)
- ✅ **Can be adopted** for prompt management
- ✅ **Can be removed** from orchestrator tracking (without affecting the actual service)

### **Simplified Scope**
Custom backends support **only prompt management**. They do NOT need:
- ❌ Demo management system
- ❌ Knowledge base integration
- ❌ Multi-tools functionality
- ❌ Complex configuration management

This keeps custom backend integration simple and focused.

## 📋 **Mandatory Requirements**

### **1. Health Endpoint**
Your custom backend MUST expose a health/status endpoint:

```http
GET /health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "custom-backend",
  "version": "1.0.0",
  "backend_type": "custom",
  "prompt_management": {
    "enabled": true,
    "method": "env_vars" | "api" | "config_file"
  }
}
```

**Required Fields:**
- `status`: Must be "healthy" for adoption
- `backend_type`: Must be "custom" 
- `prompt_management.enabled`: Must be `true`
- `prompt_management.method`: Indicates how prompts are managed

### **2. Prompt Management Endpoint**
Your backend MUST support ONE of these prompt update methods:

#### **Option A: API-Based (Recommended)**
```http
PUT /api/prompts
Content-Type: application/json

{
  "main_prompt": "You are a helpful assistant...",
  "assistant_name": "AI Helper",
  "response_style": "professional"
}
```

**Expected Response:**
```json
{
  "success": true,
  "updated_prompts": ["main_prompt", "assistant_name", "response_style"],
  "restart_required": false
}
```

#### **Option B: Environment Variables**
If your backend uses environment variables for prompts, ensure they follow this pattern:
```bash
CUSTOM_PROMPT_MAIN="Your main system prompt"
CUSTOM_PROMPT_ASSISTANT_NAME="AI Helper"
CUSTOM_PROMPT_RESPONSE_STYLE="professional"
```

The orchestrator will update these via Cloud Run service updates.

#### **Option C: Configuration File**
If using config files, expose an endpoint to reload configuration:
```http
POST /api/config/reload
```

### **3. Prompt Schema Endpoint**
Expose your prompt configuration schema:

```http
GET /api/prompts/schema
```

**Expected Response:**
```json
{
  "fields": [
    {
      "name": "main_prompt",
      "label": "Main System Prompt",
      "type": "textarea",
      "required": true,
      "description": "The primary system prompt for the AI"
    },
    {
      "name": "assistant_name",
      "label": "Assistant Name",
      "type": "text",
      "default": "AI Assistant",
      "description": "How the AI introduces itself"
    },
    {
      "name": "response_style",
      "label": "Response Style",
      "type": "select",
      "options": ["professional", "casual", "technical", "friendly"],
      "default": "professional"
    }
  ]
}
```

### **4. Current Prompts Endpoint**
Allow retrieval of current prompt values:

```http
GET /api/prompts
```

**Expected Response:**
```json
{
  "main_prompt": "You are a helpful assistant...",
  "assistant_name": "AI Helper", 
  "response_style": "professional",
  "last_updated": "2025-08-21T12:00:00Z"
}
```

## 🏷️ **Service Identification**

### **Cloud Run Labels**
Your Cloud Run service SHOULD have these labels for easy identification:

```yaml
metadata:
  labels:
    backend-type: "custom"
    orchestrator-compatible: "true"
    prompt-management: "enabled"
    version: "1.0.0"
```

### **Environment Variables (Optional)**
For additional identification:
```bash
BACKEND_TYPE=custom
ORCHESTRATOR_COMPATIBLE=true
SERVICE_VERSION=1.0.0
```

## 🔐 **Authentication & Security**

### **Option 1: No Authentication (Simple)**
If your backend runs in a secure environment, no authentication is required.

### **Option 2: API Key Authentication**
```http
PUT /api/prompts
Authorization: Bearer <api-key>
```

The orchestrator will store and use the API key for all requests.

### **Option 3: Service Account**
Use Cloud Run service account authentication for secure access between services.

## 📝 **Implementation Examples**

### **Express.js Example (Simple Prompt Management)**
```javascript
const express = require('express');
const app = express();

// Simple prompt storage (in production, use a database)
let currentPrompts = {
  system_prompt: "You are a helpful assistant.",
  assistant_name: "AI Helper",
  response_style: "professional"
};

// Health endpoint - required for adoption
app.get('/health', (req, res) => {
  res.json({
    status: "healthy",
    service: "my-custom-backend",
    version: "1.0.0",
    backend_type: "custom",
    prompt_management: {
      enabled: true,
      method: "api"
    }
  });
});

// Prompt schema - defines what can be configured
app.get('/api/prompts/schema', (req, res) => {
  res.json({
    fields: [
      {
        name: "system_prompt",
        label: "System Prompt",
        type: "textarea",
        required: true,
        description: "Main AI behavior prompt"
      },
      {
        name: "assistant_name",
        label: "Assistant Name",
        type: "text",
        default: "AI Assistant",
        description: "How the AI identifies itself"
      },
      {
        name: "response_style",
        label: "Response Style",
        type: "select",
        options: ["professional", "casual", "technical"],
        default: "professional"
      }
    ]
  });
});

// Get current prompt values
app.get('/api/prompts', (req, res) => {
  res.json(currentPrompts);
});

// Update prompts - the main management feature
app.put('/api/prompts', (req, res) => {
  const updatedFields = [];
  
  for (const [key, value] of Object.entries(req.body)) {
    if (currentPrompts.hasOwnProperty(key)) {
      currentPrompts[key] = value;
      updatedFields.push(key);
      
      // Here you would apply the prompt to your AI system
      applyPromptToAI(key, value);
    }
  }
  
  res.json({
    success: true,
    updated_prompts: updatedFields,
    restart_required: false // No restart needed for prompt updates
  });
});

// Your AI logic uses the prompts
function applyPromptToAI(promptKey, promptValue) {
  // Update your AI system with the new prompt
  console.log(`Updated ${promptKey}: ${promptValue}`);
}
```

### **FastAPI Example**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

current_prompts = {
    "main_prompt": "You are a helpful assistant.",
    "assistant_name": "AI Helper",
    "response_style": "professional"
}

class PromptUpdate(BaseModel):
    main_prompt: str = None
    assistant_name: str = None
    response_style: str = None

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "my-custom-backend",
        "version": "1.0.0",
        "backend_type": "custom",
        "prompt_management": {
            "enabled": True,
            "method": "api"
        }
    }

@app.get("/api/prompts/schema")
async def prompt_schema():
    return {
        "fields": [
            {
                "name": "main_prompt",
                "label": "Main System Prompt",
                "type": "textarea",
                "required": True
            },
            {
                "name": "assistant_name", 
                "label": "Assistant Name",
                "type": "text",
                "default": "AI Assistant"
            }
        ]
    }

@app.get("/api/prompts")
async def get_prompts():
    return current_prompts

@app.put("/api/prompts")
async def update_prompts(prompts: PromptUpdate):
    updated_fields = []
    
    for field, value in prompts.dict(exclude_unset=True).items():
        if field in current_prompts:
            current_prompts[field] = value
            updated_fields.append(field)
    
    return {
        "success": True,
        "updated_prompts": updated_fields,
        "restart_required": False
    }
```

## 🧪 **Testing Compatibility**

Test your backend compatibility with these commands:

```bash
# Check health endpoint
curl https://your-service.run.app/health

# Get prompt schema
curl https://your-service.run.app/api/prompts/schema

# Get current prompts
curl https://your-service.run.app/api/prompts

# Update prompts
curl -X PUT https://your-service.run.app/api/prompts \
  -H "Content-Type: application/json" \
  -d '{"main_prompt": "You are a test assistant."}'
```

## ⚠️ **Migration Guide**

### **If Your Backend Doesn't Meet Requirements:**

1. **Add health endpoint** returning the required format
2. **Implement prompt management** (choose API, env vars, or config file method)
3. **Add prompt schema endpoint** describing your configurable prompts
4. **Add current prompts endpoint** for reading existing values
5. **Add Cloud Run labels** for easy identification
6. **Test all endpoints** before adoption

### **Minimal Implementation:**
If you can only implement one method, choose **API-based prompt management** as it's the most flexible and doesn't require service restarts.

## 🚀 **Next Steps**

Once your custom backend meets these requirements:

1. **Deploy your updated backend** to Cloud Run
2. **Verify compatibility** using the test commands above
3. **Use the orchestrator** to adopt your service
4. **Manage prompts** through the unified interface

The orchestrator will handle service discovery, validation, and provide a unified interface for prompt management across all your backend types.

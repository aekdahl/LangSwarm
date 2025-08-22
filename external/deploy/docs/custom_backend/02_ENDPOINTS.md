# Required API Endpoints

## 🔍 **1. Health Endpoint (Required)**

### **Endpoint:** `GET /health`
**Purpose:** Validates your service for adoption

```json
{
  "status": "healthy",
  "service": "my-custom-backend",
  "version": "1.0.0",
  "backend_type": "custom",
  "prompt_management": {
    "enabled": true,
    "method": "api"
  }
}
```

### **Required Fields:**
- `status`: Must be `"healthy"`
- `backend_type`: Must be `"custom"`  
- `prompt_management.enabled`: Must be `true`
- `prompt_management.method`: Must be `"api"`

---

## 📋 **2. Prompt Schema Endpoint (Required)**

### **Endpoint:** `GET /api/prompts/schema`
**Purpose:** Defines what prompts can be configured

```json
{
  "fields": [
    {
      "name": "system_prompt",
      "label": "System Prompt",
      "type": "textarea", 
      "required": true,
      "placeholder": "You are a helpful assistant...",
      "description": "Main AI behavior prompt"
    },
    {
      "name": "assistant_name",
      "label": "Assistant Name",
      "type": "text",
      "default": "AI Assistant",
      "description": "How the AI identifies itself"
    },
    {
      "name": "response_style",
      "label": "Response Style", 
      "type": "select",
      "options": ["professional", "casual", "technical"],
      "default": "professional"
    }
  ]
}
```

### **Field Types:**
- `text`: Single-line text input
- `textarea`: Multi-line text input  
- `select`: Dropdown with predefined options
- `number`: Numeric input
- `password`: Hidden text input

---

## 📖 **3. Get Prompts Endpoint (Required)**

### **Endpoint:** `GET /api/prompts`
**Purpose:** Returns current prompt values

```json
{
  "system_prompt": "You are a helpful customer service assistant...",
  "assistant_name": "CustomerBot",
  "response_style": "professional"
}
```

**Note:** Must return all fields defined in schema with their current values.

---

## ✏️ **4. Update Prompts Endpoint (Required)**

### **Endpoint:** `PUT /api/prompts`
**Purpose:** Updates prompt values

### **Request Body:**
```json
{
  "system_prompt": "You are a helpful technical support assistant...",
  "response_style": "technical"
}
```

### **Response:**
```json
{
  "success": true,
  "updated_prompts": ["system_prompt", "response_style"],
  "restart_required": false,
  "message": "Prompts updated successfully"
}
```

### **Required Response Fields:**
- `success`: Boolean indicating success/failure
- `updated_prompts`: Array of field names that were updated
- `restart_required`: Boolean (should be `false` for prompt updates)

---

## 🔐 **Authentication (Optional)**

If your backend requires authentication, support one of these methods:

### **API Key Header:**
```
Authorization: Bearer your-api-key
```

### **Custom Header:**
```
X-API-Key: your-api-key  
```

### **Basic Auth:**
```
Authorization: Basic base64(username:password)
```

The orchestrator will include the authentication in all requests if configured during adoption.

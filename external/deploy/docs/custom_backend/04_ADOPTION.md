# Adopting Your Custom Backend

## 🚀 **Adoption Process**

### **1. Deploy Your Backend** 
Deploy your custom backend to Cloud Run with the required endpoints implemented.

### **2. Test Your Endpoints**
Verify all endpoints work correctly:

```bash
# Test health endpoint
curl https://your-backend-url.run.app/health

# Test prompt schema 
curl https://your-backend-url.run.app/api/prompts/schema

# Test get prompts
curl https://your-backend-url.run.app/api/prompts

# Test update prompts
curl -X PUT https://your-backend-url.run.app/api/prompts \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "You are a test assistant."}'
```

### **3. Adopt via Orchestrator API**
Call the orchestrator adoption endpoint:

```bash
curl -X POST https://orchestrator-url.run.app/api/backends/adopt \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Backend",
    "backend_type": "custom",
    "cloud_run_service": "my-custom-service",
    "region": "us-central1",
    "project_id": "my-project",
    "service_url": "https://my-custom-service-hash-uc.a.run.app"
  }'
```

### **4. Verify Adoption**
Check that your backend appears in the orchestrator:

```bash
curl https://orchestrator-url.run.app/api/backends
```

---

## 📋 **Adoption Request Format**

### **Required Fields:**
```json
{
  "name": "My Custom Backend",
  "backend_type": "custom", 
  "cloud_run_service": "my-custom-service",
  "region": "us-central1",
  "project_id": "my-project",
  "service_url": "https://my-custom-service-hash-uc.a.run.app"
}
```

### **Optional Fields:**
```json
{
  "description": "Customer support chatbot backend",
  "authentication": {
    "type": "api_key",
    "api_key": "your-secret-key"
  },
  "health_endpoint": "/health",
  "prompts_endpoint": "/api/prompts"
}
```

---

## 🔐 **Authentication Options**

### **No Authentication**
```json
{
  "name": "Public Backend",
  "backend_type": "custom",
  "service_url": "https://backend.run.app"
}
```

### **API Key Authentication**
```json
{
  "name": "Secured Backend",
  "backend_type": "custom", 
  "service_url": "https://backend.run.app",
  "authentication": {
    "type": "api_key",
    "api_key": "your-secret-api-key"
  }
}
```

### **Basic Authentication**
```json
{
  "name": "Basic Auth Backend",
  "backend_type": "custom",
  "service_url": "https://backend.run.app", 
  "authentication": {
    "type": "basic",
    "username": "admin",
    "password": "secret"
  }
}
```

---

## ✅ **Successful Adoption Response**

```json
{
  "success": true,
  "backend_id": "custom-backend-abc123",
  "message": "Backend adopted successfully",
  "backend": {
    "id": "custom-backend-abc123",
    "name": "My Custom Backend",
    "type": "custom",
    "status": "running",
    "url": "https://my-custom-service-hash-uc.a.run.app",
    "prompt_fields": [
      {
        "name": "system_prompt",
        "label": "System Prompt",
        "type": "textarea"
      }
    ]
  }
}
```

---

## 🔧 **Frontend Integration**

Once adopted, your backend will appear in the orchestrator frontend with:

- ✅ **Basic backend information**
- ✅ **Prompt editor** (based on your schema)
- ✅ **Remove from admin** button
- ❌ **No demo management** (custom backends don't support this)
- ❌ **No knowledge base** (custom backends don't support this)
- ❌ **No delete button** (custom backends must be manually deleted)

The frontend will only show **prompt management features** for your custom backend.

# Unified Backend Orchestrator

A comprehensive orchestrator supporting multiple backend types with unified management and prompt control.

## 🎯 **Overview**

The Unified Orchestrator manages both **AAF (LangSwarm)** and **Custom** backends through a single API, providing:

- ✅ **Multi-backend support** - AAF and Custom backends in one interface
- ✅ **Lifecycle management** - Create, adopt, manage, and delete instances
- ✅ **Unified prompt management** - Update prompts across all backend types
- ✅ **Service discovery** - Find and adopt orphaned services
- ✅ **Validation** - Ensure compatibility before adoption

## 🏗️ **Architecture**

```
Unified Orchestrator (main_v3.py)
├── AAF Backend Manager     → Create, deploy, manage AAF instances
├── Custom Backend Manager  → Adopt, manage existing custom services
├── Base Backend           → Shared interface and utilities
└── Configuration Templates → Frontend form definitions
```

## 🚀 **Quick Start**

### **1. Start the Orchestrator**
```bash
cd external/deploy/orchestrator
python main_v3.py
```

### **2. Test Basic Functionality**
```bash
# Test health
curl http://localhost:8080/health

# List supported backends
curl http://localhost:8080/api/v1/backends
```

### **3. Run Comprehensive Tests**
```bash
python test_unified_orchestrator.py production-pingday
```

## 📋 **Backend Types**

### **AAF Backend (Full Featured)**
- **Capabilities:** Create ✅ | Adopt ✅ | Delete ✅ | Update Prompts ✅
- **Features:** Demo Management ✅ | Knowledge Base ✅ | Multi-Tools ✅ | Config Editor ✅
- **Description:** LangSwarm-powered chatbot backend with complete feature set
- **Use Case:** New AI chatbot deployments requiring full functionality

### **Custom Backend (Prompt Management Only)**  
- **Capabilities:** Create ❌ | Adopt ✅ | Delete ❌ | Update Prompts ✅
- **Features:** Demo Management ❌ | Knowledge Base ❌ | Multi-Tools ❌ | Prompt Management ✅
- **Description:** Existing custom AI backend with simple prompt management
- **Use Case:** Bring existing AI services under unified prompt control (no complex features needed)

## 🔧 **API Endpoints**

### **Backend Management**

#### List Supported Backends
```http
GET /api/v1/backends
```

#### Create New Instance (AAF Only)
```http
POST /api/v1/{backend_type}/instances
Content-Type: application/json

{
  "backend_type": "aaf",
  "project_id": "my-project",
  "region": "europe-west1",
  "configuration": {
    "instance_name": "my-aaf-instance",
    "openai_api_key": "sk-...",
    "bigquery_dataset_id": "aaf_sessions"
  }
}
```

#### Adopt Existing Instance
```http
POST /api/v1/{backend_type}/instances/adopt
Content-Type: application/json

{
  "backend_type": "custom",
  "project_id": "my-project", 
  "service_name": "existing-service-name"
}
```

#### List Instances
```http
GET /api/v1/{backend_type}/instances?project_id=my-project
```

#### Delete Instance (AAF Only)
```http
DELETE /api/v1/aaf/instances/{instance_id}?project_id=my-project
```

#### Remove from Admin (Custom Only)
```http
DELETE /api/v1/custom/instances/{instance_id}/admin?project_id=my-project
```

### **Prompt Management**

#### Get Prompt Schema
```http
GET /api/v1/{backend_type}/instances/{instance_id}/prompts/schema?project_id=my-project
```

#### Get Current Prompts
```http
GET /api/v1/{backend_type}/instances/{instance_id}/prompts?project_id=my-project
```

#### Update Prompts
```http
PUT /api/v1/{backend_type}/instances/{instance_id}/prompts?project_id=my-project
Content-Type: application/json

{
  "prompts": {
    "system_prompt": "You are a helpful assistant...",
    "model": "gpt-4o",
    "temperature": "0.7"
  }
}
```

### **Discovery & Validation**

#### Find Orphaned Services (Custom)
```http
GET /api/v1/custom/orphaned-services?project_id=my-project
```

#### Validate Service Compatibility
```http
POST /api/v1/{backend_type}/validate-service
Content-Type: application/json

{
  "backend_type": "custom",
  "project_id": "my-project",
  "service_name": "potential-service"
}
```

## 🎨 **Frontend Integration**

### **Backend Templates**
Use the configuration templates for frontend forms:

```javascript
import { BACKEND_TEMPLATES } from './config/backend_templates.py';

// Get template for specific backend
const aafTemplate = BACKEND_TEMPLATES.aaf;
const customTemplate = BACKEND_TEMPLATES.custom;

// Build forms dynamically
const configFields = aafTemplate.configuration_fields;
const promptFields = aafTemplate.prompt_fields;
```

### **Unified Workflow**
```javascript
// 1. Let user choose backend type
const backendType = await selectBackendType();

// 2. Different flows based on capabilities
if (BACKEND_TEMPLATES[backendType].capabilities.create) {
  // Show creation form
  await showCreationForm(backendType);
} else {
  // Show adoption form
  await showAdoptionForm(backendType);
}

// 3. Unified management afterwards
await manageInstance(backendType, instanceId);
```

### **Prompt Editor**
```javascript
// Get schema and current values
const schema = await fetch(`/api/v1/${backendType}/instances/${instanceId}/prompts/schema`);
const currentPrompts = await fetch(`/api/v1/${backendType}/instances/${instanceId}/prompts`);

// Build dynamic form
buildPromptEditor(schema, currentPrompts);

// Save changes
await fetch(`/api/v1/${backendType}/instances/${instanceId}/prompts`, {
  method: 'PUT',
  body: JSON.stringify({ prompts: updatedPrompts })
});
```

## 🛠️ **Custom Backend Requirements**

For your custom backend to be compatible, it must implement:

### **Required Endpoints**

#### Health Check
```http
GET /health
Response: {
  "status": "healthy",
  "backend_type": "custom",
  "prompt_management": {"enabled": true, "method": "api"}
}
```

#### Prompt Schema
```http
GET /api/prompts/schema
Response: {
  "fields": [
    {"name": "main_prompt", "label": "Main Prompt", "type": "textarea", "required": true}
  ]
}
```

#### Current Prompts
```http
GET /api/prompts
Response: {
  "main_prompt": "You are a helpful assistant..."
}
```

#### Update Prompts
```http
PUT /api/prompts
Body: {"main_prompt": "Updated prompt..."}
Response: {"success": true, "updated_prompts": ["main_prompt"]}
```

See [Custom Backend Requirements](docs/CUSTOM_BACKEND_REQUIREMENTS.md) for detailed implementation guide.

## 🧪 **Testing**

### **Unit Tests**
```bash
# Test individual backend managers
python -m pytest backends/test_aaf_backend.py
python -m pytest backends/test_custom_backend.py
```

### **Integration Tests**
```bash
# Test full orchestrator functionality
python test_unified_orchestrator.py <project_id> [orchestrator_url]
```

### **Manual Testing**
```bash
# Test specific functionality
curl -X POST http://localhost:8080/api/v1/custom/instances/adopt \
  -H "Content-Type: application/json" \
  -d '{"backend_type": "custom", "project_id": "test-project", "service_name": "test-service"}'
```

## 📁 **File Structure**

```
external/deploy/orchestrator/
├── main_v3.py                 # Unified orchestrator main application
├── backends/
│   ├── __init__.py
│   ├── base_backend.py        # Abstract base for all backends
│   ├── aaf_backend.py         # AAF/LangSwarm backend manager
│   └── custom_backend.py      # Custom backend manager
├── config/
│   └── backend_templates.py   # Frontend configuration templates
├── docs/
│   └── CUSTOM_BACKEND_REQUIREMENTS.md
├── test_unified_orchestrator.py
└── README_UNIFIED_ORCHESTRATOR.md
```

## 🔄 **Migration from v2**

### **API Changes**
- **New:** `/api/v1/{backend_type}/` prefix for all endpoints
- **New:** Backend type in URL path
- **New:** Adoption-specific endpoints for custom backends
- **Changed:** Configuration format includes backend type

### **Backwards Compatibility**
The v2 orchestrator (`main_v2.py`) remains functional for existing AAF deployments. The v3 orchestrator is additive and doesn't break existing functionality.

## 🚀 **Deployment**

### **Development**
```bash
cd external/deploy/orchestrator
python main_v3.py
```

### **Production**
```bash
# Docker deployment
docker build -t unified-orchestrator .
docker run -p 8080:8080 unified-orchestrator

# Or Cloud Run
gcloud run deploy unified-orchestrator \
  --source . \
  --project my-project \
  --region europe-west1
```

## 🎯 **Next Steps**

1. **Database Integration** - Replace in-memory storage with persistent database
2. **Authentication** - Add proper authentication and authorization
3. **Monitoring** - Add metrics and logging for production use
4. **Frontend Implementation** - Build React/Vue components using the templates
5. **Additional Backends** - Extend to support more backend types

## 🆘 **Troubleshooting**

### **Common Issues**

#### "Backend type not supported"
- Check that the backend type is in `BACKEND_TEMPLATES`
- Verify the backend manager is properly imported

#### "Service validation failed"
- Ensure the custom backend implements required endpoints
- Check that the service is running and accessible
- Verify health endpoint returns correct format

#### "Adoption failed"
- Confirm the service exists in the specified project/region
- Check that the service hasn't already been adopted
- Verify Cloud Run service permissions

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main_v3.py
```

This unified orchestrator provides a solid foundation for managing multiple backend types while maintaining clean separation of concerns and extensibility for future backend types!

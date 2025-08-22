# AAF Orchestrator API Specification

## Base URL
```
https://aaf-orchestrator-3um3v34a6q-ew.a.run.app
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

---

## 1. Import Existing GCP Project

### Endpoint
```
POST /projects/import
```

### Description
Import an existing GCP project into AAF management system without creating a new project.

### Request Headers
```
Content-Type: application/json
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Request Body
```json
{
  "projectId": "string",          // Required: GCP project ID to import
  "name": "string",               // Optional: Display name (defaults to projectId)
  "description": "string",        // Optional: Project description
  "region": "string",             // Optional: Default region (defaults to "europe-west1")
  "billingAccount": "string"      // Optional: Billing account ID
}
```

### Response (Success - 200)
```json
{
  "success": true,
  "project": {
    "id": "proj-abc12345",                    // Generated AAF project ID
    "name": "Production Environment",         // Project display name
    "projectId": "my-existing-project-12345", // GCP project ID
    "billingAccount": "ABCD-1234-5678",      // Billing account (if provided)
    "region": "europe-west1",                 // Default region
    "status": "active",                       // Project status
    "created": "2024-01-15T10:30:00.000Z",  // Import timestamp
    "description": "Project description...",  // Description (if provided)
    "instanceCount": 0,                       // Number of AAF instances
    "metadata": {
      "gcp_project_number": "123456789",     // GCP project number
      "gcp_project_state": "ACTIVE",         // GCP project state
      "gcp_display_name": "My Project"       // Original GCP display name
    }
  }
}
```

### Error Responses

#### 404 - Project Not Found
```json
{
  "detail": "GCP_PROJECT_NOT_FOUND"
}
```

#### 409 - Project Already Exists
```json
{
  "detail": "PROJECT_ALREADY_EXISTS"
}
```

#### 403 - Access Denied
```json
{
  "detail": "PROJECT_ACCESS_DENIED: {error_details}"
}
```

#### 500 - Server Error
```json
{
  "detail": "Failed to import project: {error_details}"
}
```

---

## 2. Deploy AAF to Any Project

### Endpoint
```
POST /projects/deploy
```

### Description
Deploy an AAF instance to any existing GCP project. The project doesn't need to be imported first.

### Request Headers
```
Content-Type: application/json
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Request Body
```json
{
  "project_id": "string",        // Required: GCP project ID
  "project_name": "string",      // Required: Display name for the project
  "customer_info": {             // Required: Customer information
    "email": "string",           // Customer email
    "company": "string",         // Company name
    "contact": "string"          // Optional: Contact info
  },
  "aaf_config": {                // Optional: AAF configuration
    "memory": "string",          // Memory allocation (default: "2Gi")
    "max_instances": "number",   // Max instances (default: 5)
    "region": "string",          // Deployment region (default: "europe-west1")
    "env_vars": {                // Optional: Environment variables
      "OPENAI_API_KEY": "string",
      "CUSTOM_VAR": "string"
    }
  }
}
```

### Response (Success - 200)
```json
{
  "success": true,
  "project_id": "my-existing-project",
  "project_name": "My Project",
  "service_url": "https://aaf-instance-abc12345-xyz.europe-west1.run.app",
  "service_name": "aaf-instance-abc12345",
  "management_api_secret": "aaf-secret-token",
  "status": "deployed"
}
```

### Error Responses

#### 404 - Project Not Found
```json
{
  "detail": "GCP project {project_id} not found or not accessible"
}
```

#### 500 - Deployment Failed
```json
{
  "detail": "Failed to deploy AAF instance: {error_details}"
}
```

---

## 3. Create Project + Deploy AAF

### Endpoint
```
POST /projects/create
```

### Description
Create a new GCP project and deploy AAF instance in one operation.

### Request Headers
```
Content-Type: application/json
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Request Body
```json
{
  "project_name": "string",      // Required: Project display name
  "project_id": "string",        // Optional: Custom project ID
  "customer_info": {             // Required: Customer information
    "email": "string",
    "company": "string",
    "contact": "string"
  },
  "aaf_config": {                // Required: AAF configuration
    "memory": "string",          // Memory allocation
    "max_instances": "number",   // Max instances
    "env_vars": {                // Environment variables
      "OPENAI_API_KEY": "string"
    }
  }
}
```

### Response (Success - 200)
```json
{
  "success": true,
  "project_id": "aaf-customer-abc12345",
  "project_name": "New Customer Project",
  "customer_id": "customer-123",
  "status": "created"
}
```

### Error Responses

#### 500 - Creation Failed
```json
{
  "detail": "Project creation failed"
}
```

#### 503 - Service Unavailable
```json
{
  "detail": "Project creator service unavailable"
}
```

---

## 4. List All Projects

### Endpoint
```
GET /projects
```

### Description
Retrieve all AAF projects and instances.

### Request Headers
```
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Response (Success - 200)
```json
{
  "projects": [
    {
      "project_id": "project-123",
      "project_name": "Production Environment",
      "customer_info": {
        "email": "customer@example.com",
        "company": "Example Corp"
      },
      "service_url": "https://aaf-instance-xyz.europe-west1.run.app",
      "status": "active",
      "created_at": "2024-01-15T10:30:00.000Z",
      "health_status": "healthy",
      "last_health_check": "2024-01-15T11:00:00.000Z"
    }
  ],
  "count": 1
}
```

---

## 5. Get Specific Project

### Endpoint
```
GET /projects/{project_id}
```

### Description
Retrieve detailed information about a specific project.

### Request Headers
```
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Path Parameters
- `project_id` (string): The GCP project ID

### Response (Success - 200)
```json
{
  "project_id": "project-123",
  "project_name": "Production Environment",
  "customer_info": {
    "email": "customer@example.com",
    "company": "Example Corp"
  },
  "service_url": "https://aaf-instance-xyz.europe-west1.run.app",
  "management_api_secret": "aaf-secret-token",
  "status": "active",
  "created_at": "2024-01-15T10:30:00.000Z",
  "last_updated": "2024-01-15T10:30:00.000Z",
  "health_status": "healthy",
  "last_health_check": "2024-01-15T11:00:00.000Z"
}
```

### Error Responses

#### 404 - Project Not Found
```json
{
  "detail": "Project not found"
}
```

---

## 6. Delete Project

### Endpoint
```
DELETE /projects/{project_id}
```

### Description
Mark a project as inactive (soft delete).

### Request Headers
```
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Response (Success - 200)
```json
{
  "message": "Project {project_id} deletion initiated"
}
```

---

## 7. Health Check

### Endpoint
```
GET /health
```

### Description
Check orchestrator service health (no authentication required).

### Response (Success - 200)
```json
{
  "status": "healthy",
  "service": "aaf-orchestrator",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## 8. Check Project Health

### Endpoint
```
GET /projects/{project_id}/health
```

### Description
Check health of a specific AAF instance.

### Request Headers
```
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
```

### Response (Success - 200)
```json
{
  "status": "healthy",
  "service": "aaf-instance",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Proxy Endpoints

### Endpoint
```
GET|POST|PUT|DELETE /proxy/{project_id}/{path}
```

### Description
Proxy requests to specific AAF instances.

### Request Headers
```
Authorization: Bearer {ORCHESTRATOR_API_SECRET}
Content-Type: application/json (for POST/PUT)
```

### Example
```
POST /proxy/my-project/api/chat
```

Proxies to: `https://aaf-instance-xyz.run.app/api/chat`

---

## Error Handling

### Common HTTP Status Codes
- `200` - Success
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (access denied)
- `404` - Not found
- `409` - Conflict (resource already exists)
- `500` - Internal server error
- `503` - Service unavailable

### Error Response Format
```json
{
  "detail": "Error description"
}
```

---

## Rate Limiting
- No explicit rate limiting currently implemented
- Monitor for 429 responses in future versions

---

## SDKs and Examples

### JavaScript/TypeScript Example
```typescript
const AAF_API_BASE = 'https://aaf-orchestrator-3um3v34a6q-ew.a.run.app';
const API_SECRET = 'your-orchestrator-api-secret';

// Import existing project
async function importProject(projectData) {
  const response = await fetch(`${AAF_API_BASE}/projects/import`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_SECRET}`
    },
    body: JSON.stringify(projectData)
  });
  
  return response.json();
}

// Deploy AAF to project
async function deployAAF(deploymentData) {
  const response = await fetch(`${AAF_API_BASE}/projects/deploy`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_SECRET}`
    },
    body: JSON.stringify(deploymentData)
  });
  
  return response.json();
}

// List projects
async function listProjects() {
  const response = await fetch(`${AAF_API_BASE}/projects`, {
    headers: {
      'Authorization': `Bearer ${API_SECRET}`
    }
  });
  
  return response.json();
}
```

### cURL Examples
```bash
# Import project
curl -X POST "${AAF_API_BASE}/projects/import" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_SECRET}" \
  -d '{
    "projectId": "my-existing-project",
    "name": "Production Environment",
    "region": "europe-west1"
  }'

# Deploy AAF
curl -X POST "${AAF_API_BASE}/projects/deploy" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_SECRET}" \
  -d '{
    "project_id": "my-project",
    "project_name": "My Project",
    "customer_info": {
      "email": "customer@example.com",
      "company": "Example Corp"
    },
    "aaf_config": {
      "memory": "2Gi",
      "max_instances": 3
    }
  }'

# List projects
curl "${AAF_API_BASE}/projects" \
  -H "Authorization: Bearer ${API_SECRET}"
```

---

## Configuration

### Environment Variables
The orchestrator expects these environment variables:
- `ORCHESTRATOR_API_SECRET` - API authentication secret
- `REGISTRY_PROJECT_ID` - GCP project for registry (enkl-saas)
- `PROJECT_CREATOR_FUNCTION_URL` - Cloud Function URL for project creation
- `FIRESTORE_DATABASE` - Firestore database name
- `FIRESTORE_COLLECTION` - Collection name for project registry

### Current Deployment
- **Base URL**: `https://aaf-orchestrator-3um3v34a6q-ew.a.run.app`
- **Region**: `europe-west1`
- **Backend Image**: `gcr.io/enkl-saas/aaf-backend:latest`

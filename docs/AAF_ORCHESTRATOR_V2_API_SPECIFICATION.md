# AAF Orchestrator v2 API Specification

## 🎯 **Overview**

The AAF Orchestrator v2 properly separates **Projects** and **Instances**:

- **Project**: A customer's GCP project that can contain multiple AAF instances
- **Instance**: A single AAF deployment (Cloud Run service) within a project

## 🏗️ **Architecture**

```
Project (production-pingday)
├── Instance 1 (aaf-prod-web)      ← Chat for website
├── Instance 2 (aaf-prod-support)  ← Support chatbot  
└── Instance 3 (aaf-prod-sales)    ← Sales assistant
```

## 🔧 **Base URL**

```
https://aaf-orchestrator-631341022010.europe-west1.run.app
```

## 🔑 **Authentication**

All requests require Bearer token authentication:

```javascript
headers: {
  'Authorization': 'Bearer 7212793a2d7821d52e296809bf71a9be6d18fc69739b030b4d25cee75dd2ed39',
  'Content-Type': 'application/json'
}
```

---

## 📋 **PROJECT ENDPOINTS**

### **Create Project**

**Endpoint:** `POST /projects`

**Description:** Create a new customer project that can hold multiple AAF instances.

**Request Body:**
```javascript
{
  "project_id": "customer-prod-123",           // Required: GCP project ID
  "project_name": "Customer Production",      // Optional: Display name
  "customer_info": {                          // Optional: Customer details
    "company": "Customer Corp",
    "email": "admin@customer.com",
    "domain": "customer.com"
  },
  "region": "europe-west1",                   // Optional: Default region
  "billing_account": "ABCD-1234-5678"        // Optional: Billing account
}
```

**Response:**
```javascript
{
  "success": true,
  "project_id": "customer-prod-123",
  "message": "Project customer-prod-123 created successfully"
}
```

### **List Projects**

**Endpoint:** `GET /projects?status=active`

**Query Parameters:**
- `status`: `active` (default), `deleted`, `all`

**Response:**
```javascript
{
  "projects": [
    {
      "project_id": "customer-prod-123",
      "project_name": "Customer Production",
      "customer_info": {...},
      "region": "europe-west1",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "total_instances": 3,
      "active_instances": 2,
      "instances": {
        "instance-1": {...},
        "instance-2": {...}
      }
    }
  ],
  "count": 1,
  "status_filter": "active"
}
```

### **Get Project**

**Endpoint:** `GET /projects/{project_id}`

**Response:**
```javascript
{
  "project_id": "customer-prod-123",
  "project_name": "Customer Production",
  "customer_info": {...},
  "status": "active",
  "total_instances": 3,
  "active_instances": 2,
  "instances": {
    "instance-1": {
      "instance_id": "instance-1",
      "service_name": "aaf-prod-web",
      "service_url": "https://aaf-prod-web.run.app",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

### **Update Project**

**Endpoint:** `PATCH /projects/{project_id}`

**Request Body:**
```javascript
{
  "project_name": "Updated Project Name",    // Optional
  "customer_info": {...},                   // Optional
  "status": "active"                        // Optional
}
```

### **Delete Project**

**Endpoint:** `DELETE /projects/{project_id}?hard_delete=false&delete_instances=true`

**Query Parameters:**
- `hard_delete`: `false` (soft delete), `true` (permanent)
- `delete_instances`: `true` (delete all instances), `false` (keep instances)

**Response:**
```javascript
{
  "success": true,
  "project_id": "customer-prod-123",
  "message": "Project customer-prod-123 marked as deleted",
  "instances_deleted": true
}
```

---

## 🚀 **INSTANCE ENDPOINTS**

### **Create Instance**

**Endpoint:** `POST /projects/{project_id}/instances`

**Description:** Deploy a new AAF instance within a project.

**Request Body:**
```javascript
{
  "instance_name": "Support Chat",           // Optional: Display name
  "aaf_config": {                           // Optional: AAF configuration
    "env_vars": {
      "OPENAI_API_KEY": "sk-...",
      "CRAWL4AI_BASE_URL": "https://crawl4ai.run.app"
    }
  },
  "region": "europe-west1",                 // Optional: Inherits from project
  "memory": "2Gi",                          // Optional: Memory allocation
  "cpu": "2"                                // Optional: CPU allocation
}
```

**Response:**
```javascript
{
  "success": true,
  "project_id": "customer-prod-123",
  "service_name": "aaf-instance-1755538474",
  "message": "AAF instance deployment started for project customer-prod-123",
  "deployment_started": true
}
```

### **List Instances**

**Endpoint:** `GET /projects/{project_id}/instances?status=active`

**Query Parameters:**
- `status`: `active` (default), `deleted`, `all`

**Response:**
```javascript
{
  "project_id": "customer-prod-123",
  "instances": [
    {
      "instance_id": "aaf-instance-1755538474",
      "service_name": "aaf-instance-1755538474",
      "service_url": "https://aaf-instance-1755538474.run.app",
      "region": "europe-west1",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "aaf_config": {
        "env_vars": {
          "OPENAI_API_KEY": "sk-...",
          "CRAWL4AI_BASE_URL": "https://crawl4ai.run.app"
        }
      }
    }
  ],
  "count": 1,
  "status_filter": "active"
}
```

### **Get Instance**

**Endpoint:** `GET /projects/{project_id}/instances/{instance_id}`

**Response:**
```javascript
{
  "instance_id": "aaf-instance-1755538474",
  "service_name": "aaf-instance-1755538474",
  "service_url": "https://aaf-instance-1755538474.run.app",
  "region": "europe-west1",
  "status": "active",
  "health_status": "healthy",
  "created_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T11:00:00Z",
  "aaf_config": {...},
  "management_api_secret": "mgmt-abc123"
}
```

### **Update Instance**

**Endpoint:** `PATCH /projects/{project_id}/instances/{instance_id}`

**Request Body:**
```javascript
{
  "aaf_config": {                          // Optional: Updated configuration
    "env_vars": {
      "CRAWL4AI_BASE_URL": "https://new-crawl4ai.run.app"
    }
  },
  "status": "active"                       // Optional: Status update
}
```

### **Delete Instance**

**Endpoint:** `DELETE /projects/{project_id}/instances/{instance_id}?hard_delete=false&delete_service=true`

**Query Parameters:**
- `hard_delete`: `false` (soft delete), `true` (permanent)
- `delete_service`: `true` (delete Cloud Run service), `false` (registry only)

**Response:**
```javascript
{
  "success": true,
  "project_id": "customer-prod-123",
  "instance_id": "aaf-instance-1755538474",
  "message": "Instance aaf-instance-1755538474 marked as deleted",
  "service_deleted": true
}
```

---

## 🔧 **Frontend Integration Examples**

### **Complete Project Management Flow**

```javascript
class AAFProjectManager {
  constructor(orchestratorUrl, authToken) {
    this.baseUrl = orchestratorUrl;
    this.authToken = authToken;
  }

  // Create new customer project
  async createProject(projectData) {
    const response = await fetch(`${this.baseUrl}/projects`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(projectData)
    });
    return response.json();
  }

  // Create AAF instance in project
  async createInstance(projectId, instanceConfig) {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/instances`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(instanceConfig)
    });
    return response.json();
  }

  // List all instances in a project
  async listInstances(projectId) {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/instances`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    return response.json();
  }

  // Delete specific instance (NOT the whole project)
  async deleteInstance(projectId, instanceId) {
    const response = await fetch(
      `${this.baseUrl}/projects/${projectId}/instances/${instanceId}?delete_service=true`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.authToken}`
        }
      }
    );
    return response.json();
  }

  // Delete entire project and all instances
  async deleteProject(projectId) {
    const response = await fetch(
      `${this.baseUrl}/projects/${projectId}?delete_instances=true`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.authToken}`
        }
      }
    );
    return response.json();
  }
}
```

### **Usage Examples**

```javascript
const manager = new AAFProjectManager(
  'https://aaf-orchestrator-631341022010.europe-west1.run.app',
  'your-auth-token'
);

// 1. Create a new customer project
const project = await manager.createProject({
  project_id: 'customer-prod-123',
  project_name: 'Customer Production Environment',
  customer_info: {
    company: 'Customer Corp',
    email: 'admin@customer.com'
  }
});

// 2. Create multiple instances in the project
const webInstance = await manager.createInstance('customer-prod-123', {
  instance_name: 'Website Chat',
  aaf_config: {
    env_vars: {
      OPENAI_API_KEY: 'sk-...',
      CRAWL4AI_BASE_URL: 'https://crawl4ai.run.app'
    }
  }
});

const supportInstance = await manager.createInstance('customer-prod-123', {
  instance_name: 'Support Chat',
  aaf_config: {
    env_vars: {
      OPENAI_API_KEY: 'sk-...',
      CRAWL4AI_BASE_URL: 'https://crawl4ai.run.app'
    }
  }
});

// 3. List all instances
const instances = await manager.listInstances('customer-prod-123');
console.log(`Project has ${instances.count} instances`);

// 4. Delete specific instance (keeps project and other instances)
await manager.deleteInstance('customer-prod-123', webInstance.service_name);

// 5. Delete entire project (removes all instances)
await manager.deleteProject('customer-prod-123');
```

---

## 🎯 **Key Changes from v1**

### **✅ Fixed Issues:**
1. **Proper separation**: Projects ≠ Instances
2. **Correct deletion**: Deleting instance doesn't delete project
3. **Multiple instances**: One project can have many AAF instances
4. **Clear hierarchy**: `/projects/{id}/instances/{id}` structure

### **🔄 Migration Notes:**
- **Old v1 data** has been automatically migrated to v2 format
- **Existing projects** are preserved with their instances
- **API endpoints** follow RESTful patterns
- **Backward compatibility** maintained where possible

### **📱 Frontend Benefits:**
- **Intuitive UI**: Show projects → instances hierarchy
- **Granular control**: Delete individual instances without affecting project
- **Better UX**: Users understand project vs instance distinction
- **Scalability**: Support customers with multiple chat deployments

The v2 API fixes the fundamental design flaw and provides a much cleaner, more logical way to manage AAF deployments! 🚀

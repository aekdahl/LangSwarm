# AAF Multi-Project Deployment Guide

This guide covers deploying the complete AAF multi-project infrastructure with automated project creation and centralized management.

## Architecture Overview

```mermaid
graph TD
    A[Admin Frontend] --> B[Backend Orchestrator]
    B --> C[Project Creator Function]
    B --> D[Project Registry - BigQuery]
    B --> E[AAF Instance 1]
    B --> F[AAF Instance 2]
    B --> G[AAF Instance N]
    
    C --> H[New GCP Project]
    H --> I[API Enablement]
    H --> J[IAM Setup]
    H --> K[BigQuery Setup]
    H --> L[AAF Deployment]
```

## Components

### 1. **Project Creator Cloud Function**
- **Purpose**: Automated GCP project creation and AAF deployment
- **Triggers**: HTTP requests from Backend Orchestrator
- **Deploys**: New AAF instances to Cloud Run
- **Updates**: Project registry with deployment info

### 2. **Backend Orchestrator**
- **Purpose**: Central API gateway for all AAF instances
- **Features**: Request routing, authentication, health monitoring
- **Storage**: Project registry in BigQuery
- **Proxy**: Routes requests to correct AAF instances

### 3. **Project Registry**
- **Storage**: BigQuery table with project metadata
- **Data**: Project info, service URLs, health status
- **Caching**: In-memory cache for fast lookups

---

## Prerequisites

### Required Permissions
Your deployment service account needs:
- `roles/resourcemanager.projectCreator`
- `roles/billing.admin` (or access to billing account)
- `roles/serviceusage.serviceUsageAdmin`
- `roles/iam.serviceAccountAdmin`
- `roles/cloudbuild.builds.builder`
- `roles/run.admin`
- `roles/bigquery.admin`

### Required Environment Variables
```bash
# Billing and Organization
export BILLING_ACCOUNT_ID="012345-678901-234567"
export ORGANIZATION_ID="123456789012"  # Optional
export FOLDER_ID="folders/123456789"   # Optional (alternative to org)

# Main orchestrator project
export GOOGLE_CLOUD_PROJECT="main-orchestrator-project"
export REGISTRY_PROJECT_ID="main-orchestrator-project"

# API Keys and Secrets
export ORCHESTRATOR_API_SECRET="your-secure-orchestrator-api-key"
export PROJECT_CREATOR_FUNCTION_URL=""  # Will be set after function deployment

# Google Cloud Authentication
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

---

## Deployment Steps

### Step 1: Deploy Project Creator Function

```bash
cd external/deploy/project-creator

# Set required environment variables
export BILLING_ACCOUNT_ID="your-billing-account-id"
export ORGANIZATION_ID="your-org-id"  # or FOLDER_ID
export REGISTRY_PROJECT_ID="your-main-project"

# Make deployment script executable
chmod +x deploy.sh

# Deploy the function
./deploy.sh
```

**Output:**
```
Function deployed successfully!
Function URL: https://us-central1-main-project.cloudfunctions.net/aaf-project-creator
```

Copy the Function URL for the next step.

### Step 2: Deploy Backend Orchestrator

```bash
cd external/deploy/orchestrator

# Set environment variables
export ORCHESTRATOR_API_SECRET="your-secure-api-secret"
export PROJECT_CREATOR_FUNCTION_URL="https://us-central1-main-project.cloudfunctions.net/aaf-project-creator"

# Make deployment script executable
chmod +x deploy.sh

# Deploy the orchestrator
./deploy.sh
```

**Output:**
```
Orchestrator deployed successfully!
Service URL: https://aaf-orchestrator-hash-uc.a.run.app
```

### Step 3: Verify Deployment

```bash
# Test orchestrator health
curl "https://aaf-orchestrator-hash-uc.a.run.app/health"

# Expected response:
{
  "status": "healthy",
  "service": "aaf-orchestrator",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Usage Examples

### Create New AAF Project

```bash
curl -X POST "https://aaf-orchestrator-hash-uc.a.run.app/projects/create" \
  -H "Authorization: Bearer your-orchestrator-api-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Customer ABC Chatbot",
    "customer_info": {
      "name": "John Doe",
      "email": "john@customerabc.com",
      "company": "Customer ABC Inc"
    },
    "aaf_config": {
      "openai_api_key": "sk-customer-openai-key",
      "default_model": "gpt-4",
      "system_prompt": "You are a customer support assistant for ABC Inc."
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "project_id": "aaf-customer-abc-chatbot-a1b2c3d4",
  "project_info": {
    "project_id": "aaf-customer-abc-chatbot-a1b2c3d4",
    "display_name": "Customer ABC Chatbot",
    "labels": {...}
  },
  "deployment": {
    "service_url": "https://aaf-backend-hash-uc.a.run.app",
    "management_api_secret": "generated-secret-key"
  },
  "message": "Project created and deployed successfully"
}
```

### List All Projects

```bash
curl "https://aaf-orchestrator-hash-uc.a.run.app/projects" \
  -H "Authorization: Bearer your-orchestrator-api-secret"
```

**Response:**
```json
{
  "projects": [
    {
      "project_id": "aaf-customer-abc-chatbot-a1b2c3d4",
      "project_name": "Customer ABC Chatbot",
      "customer_info": {...},
      "service_url": "https://aaf-backend-hash-uc.a.run.app",
      "status": "active",
      "health_status": "healthy",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

### Proxy Request to AAF Instance

```bash
# Chat with specific project's AAF instance
curl -X POST "https://aaf-orchestrator-hash-uc.a.run.app/proxy/aaf-customer-abc-chatbot-a1b2c3d4/api/chat/" \
  -H "Authorization: Bearer your-orchestrator-api-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my account",
    "session_id": "user-session-123"
  }'
```

**Response:**
```json
{
  "response": "Hello! I'm here to help you with your ABC Inc account. What specific issue can I assist you with?",
  "agent_id": "aaf_chatbot",
  "session_id": "user-session-123",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

## Frontend Integration

### React Admin Dashboard

```jsx
import React, { useState, useEffect } from 'react';

const AAFManager = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const ORCHESTRATOR_URL = 'https://aaf-orchestrator-hash-uc.a.run.app';
  const API_KEY = 'your-orchestrator-api-secret';
  
  const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  };
  
  useEffect(() => {
    loadProjects();
  }, []);
  
  const loadProjects = async () => {
    try {
      const response = await fetch(`${ORCHESTRATOR_URL}/projects`, { headers });
      const data = await response.json();
      setProjects(data.projects);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };
  
  const createProject = async (projectData) => {
    setLoading(true);
    try {
      const response = await fetch(`${ORCHESTRATOR_URL}/projects/create`, {
        method: 'POST',
        headers,
        body: JSON.stringify(projectData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('Project created successfully!');
        loadProjects(); // Refresh list
      } else {
        alert('Project creation failed: ' + result.message);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const chatWithProject = async (projectId, message) => {
    try {
      const response = await fetch(
        `${ORCHESTRATOR_URL}/proxy/${projectId}/api/chat/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({ message })
        }
      );
      
      const result = await response.json();
      return result.response;
    } catch (error) {
      console.error('Chat failed:', error);
      return 'Error: Could not connect to chatbot';
    }
  };
  
  return (
    <div className="aaf-manager">
      <h1>AAF Project Manager</h1>
      
      <div className="project-actions">
        <button onClick={() => setShowCreateForm(true)} disabled={loading}>
          Create New Project
        </button>
        <button onClick={loadProjects}>Refresh</button>
      </div>
      
      <div className="projects-list">
        {projects.map(project => (
          <ProjectCard 
            key={project.project_id}
            project={project}
            onChat={(message) => chatWithProject(project.project_id, message)}
          />
        ))}
      </div>
      
      {showCreateForm && (
        <CreateProjectForm 
          onSubmit={createProject}
          onCancel={() => setShowCreateForm(false)}
          loading={loading}
        />
      )}
    </div>
  );
};
```

### Vue.js Project Management

```vue
<template>
  <div class="aaf-dashboard">
    <h1>AAF Multi-Project Dashboard</h1>
    
    <div class="actions">
      <button @click="createProject" :disabled="loading">
        Create New Project
      </button>
      <button @click="loadProjects">Refresh</button>
    </div>
    
    <div class="projects-grid">
      <div v-for="project in projects" :key="project.project_id" class="project-card">
        <h3>{{ project.project_name }}</h3>
        <p>Status: {{ project.health_status }}</p>
        <p>Customer: {{ project.customer_info.company }}</p>
        
        <div class="project-actions">
          <button @click="openChatInterface(project)">Test Chat</button>
          <button @click="viewProjectDetails(project)">Details</button>
          <button @click="manageProject(project)">Manage</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      projects: [],
      loading: false,
      orchestratorUrl: 'https://aaf-orchestrator-hash-uc.a.run.app',
      apiKey: 'your-orchestrator-api-secret'
    };
  },
  
  async mounted() {
    await this.loadProjects();
  },
  
  methods: {
    async loadProjects() {
      try {
        const response = await this.$http.get('/projects', {
          baseURL: this.orchestratorUrl,
          headers: { 'Authorization': `Bearer ${this.apiKey}` }
        });
        
        this.projects = response.data.projects;
      } catch (error) {
        this.$toast.error('Failed to load projects');
      }
    },
    
    async createProject() {
      // Open create project modal/form
      this.$modal.show('create-project-form');
    },
    
    async openChatInterface(project) {
      // Open chat interface for specific project
      this.$router.push(`/chat/${project.project_id}`);
    },
    
    async manageProject(project) {
      // Open project management interface
      this.$router.push(`/manage/${project.project_id}`);
    }
  }
};
</script>
```

---

## Monitoring and Health Checks

### Automated Health Monitoring

```bash
# Check all project health statuses
curl "https://aaf-orchestrator-hash-uc.a.run.app/projects" \
  -H "Authorization: Bearer your-orchestrator-api-secret" \
  | jq '.projects[] | {project_id: .project_id, health: .health_status}'
```

### Individual Project Health

```bash
# Check specific project health
curl "https://aaf-orchestrator-hash-uc.a.run.app/projects/aaf-customer-abc-chatbot-a1b2c3d4/health" \
  -H "Authorization: Bearer your-orchestrator-api-secret"
```

### Monitoring Dashboard

Set up monitoring with:
- Google Cloud Monitoring for infrastructure metrics
- Custom health check endpoints for application status
- BigQuery analytics for usage patterns
- Alerting for unhealthy instances

---

## Security Considerations

### API Authentication
- Each AAF instance has its own management API secret
- Orchestrator handles authentication centrally
- Frontend never directly accesses instance credentials

### Network Security
- All services run on Google Cloud with VPC security
- HTTPS encryption for all API communications
- IAM-based access control for GCP resources

### Data Isolation
- Each customer has separate GCP project
- BigQuery datasets are project-isolated
- No cross-customer data access

---

## Scaling and Performance

### Horizontal Scaling
- Orchestrator can scale to handle multiple concurrent requests
- Each AAF instance scales independently on Cloud Run
- BigQuery handles high-volume analytics workloads

### Cost Optimization
- Cloud Run pay-per-use pricing
- BigQuery pay-per-query model
- Automatic scaling down during low usage

### Performance Monitoring
- Request latency tracking through orchestrator
- Individual instance performance metrics
- Cross-project analytics and reporting

This deployment infrastructure provides a complete multi-tenant AAF solution with automated project creation, centralized management, and enterprise-grade security! 🚀

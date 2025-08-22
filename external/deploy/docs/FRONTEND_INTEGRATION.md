# Frontend Integration Guide

## **Essential Information for Frontend Applications**

### **1. Orchestrator Configuration**

```javascript
// Main configuration object for frontend
const AAF_CONFIG = {
  // Orchestrator endpoint
  orchestratorUrl: 'https://aaf-orchestrator-xyz.a.run.app',
  
  // Authentication
  orchestratorApiSecret: 'your-orchestrator-api-secret',
  
  // API endpoints
  endpoints: {
    // Project management
    projects: '/projects',
    createProject: '/projects/create',
    getProject: '/projects/{project_id}',
    deleteProject: '/projects/{project_id}',
    
    // Health monitoring
    orchestratorHealth: '/health',
    projectHealth: '/projects/{project_id}/health',
    
    // Proxy to AAF instances (all AAF APIs)
    proxyBase: '/proxy/{project_id}'
  },
  
  // Default settings
  defaults: {
    chatSessionId: () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    requestTimeout: 30000, // 30 seconds
    streamTimeout: 300000, // 5 minutes for streaming
  }
};
```

### **2. Project Information Structure**

```typescript
interface AAFProject {
  // Basic project info
  project_id: string;           // "aaf-customer-abc-xyz123"
  project_name: string;         // "Customer ABC Chatbot"
  status: 'active' | 'deleted'; // Project status
  
  // Customer information
  customer_info: {
    name: string;               // "John Doe"
    email: string;              // "john@customerabc.com"
    company: string;            // "Customer ABC Inc"
  };
  
  // Service endpoints
  service_url: string;          // "https://aaf-backend-xyz.a.run.app"
  
  // Health monitoring
  health_status: 'healthy' | 'unhealthy' | 'unknown';
  last_health_check: string;   // ISO timestamp
  
  // Timestamps
  created_at: string;          // ISO timestamp
  last_updated: string;        // ISO timestamp
  
  // Access credentials (handled internally by orchestrator)
  // management_api_secret: string; // NOT exposed to frontend
}
```

### **3. Authentication Flow**

```javascript
class AAFApiClient {
  constructor(config) {
    this.baseUrl = config.orchestratorUrl;
    this.apiSecret = config.orchestratorApiSecret;
    this.defaultHeaders = {
      'Authorization': `Bearer ${this.apiSecret}`,
      'Content-Type': 'application/json'
    };
  }
  
  // Project management methods
  async createProject(projectData) {
    const response = await fetch(`${this.baseUrl}/projects/create`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify(projectData)
    });
    
    if (!response.ok) {
      throw new Error(`Project creation failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  async listProjects() {
    const response = await fetch(`${this.baseUrl}/projects`, {
      headers: this.defaultHeaders
    });
    
    return await response.json();
  }
  
  // Proxy methods for AAF instances
  async proxyRequest(projectId, path, options = {}) {
    const url = `${this.baseUrl}/proxy/${projectId}${path}`;
    const config = {
      headers: this.defaultHeaders,
      ...options
    };
    
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`AAF request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  // Specific AAF methods
  async sendChatMessage(projectId, message, sessionId) {
    return this.proxyRequest(projectId, '/api/chat/', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId })
    });
  }
  
  async getAgents(projectId) {
    return this.proxyRequest(projectId, '/api/chat/agents');
  }
  
  async updateConfiguration(projectId, config) {
    return this.proxyRequest(projectId, '/api/config-editor/update', {
      method: 'PUT',
      body: JSON.stringify({
        config,
        backup_current: true,
        restart_agents: true
      })
    });
  }
}
```

### **4. Real-time Updates (Optional)**

```javascript
// Using Firestore real-time listeners for project updates
class AAFRealtimeManager {
  constructor(config) {
    this.config = config;
    this.listeners = new Map();
  }
  
  // Listen to project changes
  subscribeToProjects(callback) {
    // This would connect to Firestore directly or through a WebSocket
    // For now, polling implementation:
    const pollInterval = setInterval(async () => {
      try {
        const client = new AAFApiClient(this.config);
        const projects = await client.listProjects();
        callback(projects.projects);
      } catch (error) {
        console.error('Failed to poll projects:', error);
      }
    }, 5000); // Poll every 5 seconds
    
    this.listeners.set('projects', pollInterval);
    
    return () => {
      clearInterval(pollInterval);
      this.listeners.delete('projects');
    };
  }
  
  // Listen to specific project health changes
  subscribeToProjectHealth(projectId, callback) {
    const pollInterval = setInterval(async () => {
      try {
        const client = new AAFApiClient(this.config);
        const health = await client.proxyRequest(projectId, '/health');
        callback(health);
      } catch (error) {
        callback({ status: 'unreachable', error: error.message });
      }
    }, 30000); // Poll every 30 seconds
    
    this.listeners.set(`health_${projectId}`, pollInterval);
    
    return () => {
      clearInterval(pollInterval);
      this.listeners.delete(`health_${projectId}`);
    };
  }
  
  unsubscribeAll() {
    this.listeners.forEach(interval => clearInterval(interval));
    this.listeners.clear();
  }
}
```

### **5. Error Handling Patterns**

```javascript
class AAFErrorHandler {
  static handle(error, context = '') {
    console.error(`AAF Error ${context}:`, error);
    
    if (error.status === 401) {
      return {
        type: 'auth_error',
        message: 'Authentication failed. Please check your API key.',
        action: 'refresh_auth'
      };
    }
    
    if (error.status === 404) {
      return {
        type: 'not_found',
        message: context.includes('project') 
          ? 'Project not found or has been deleted.'
          : 'Requested resource not found.',
        action: 'refresh_data'
      };
    }
    
    if (error.status === 503) {
      return {
        type: 'service_unavailable',
        message: 'AAF instance is temporarily unavailable.',
        action: 'retry_later'
      };
    }
    
    if (error.message?.includes('timeout')) {
      return {
        type: 'timeout',
        message: 'Request timed out. Please try again.',
        action: 'retry'
      };
    }
    
    return {
      type: 'unknown_error',
      message: 'An unexpected error occurred.',
      action: 'contact_support'
    };
  }
}

// Usage in components
try {
  const result = await aafClient.sendChatMessage(projectId, message, sessionId);
} catch (error) {
  const errorInfo = AAFErrorHandler.handle(error, 'chat');
  this.showError(errorInfo.message);
  
  if (errorInfo.action === 'retry') {
    // Show retry button
  } else if (errorInfo.action === 'refresh_auth') {
    // Redirect to login or refresh tokens
  }
}
```

### **6. State Management (React/Redux)**

```javascript
// Redux store structure for AAF management
const initialState = {
  orchestrator: {
    connected: false,
    lastHealthCheck: null,
    error: null
  },
  projects: {
    list: [],
    selected: null,
    loading: false,
    error: null
  },
  chat: {
    sessions: {},
    activeSession: null,
    messages: {},
    streaming: false
  },
  configuration: {
    currentConfig: null,
    validationResult: null,
    saving: false
  }
};

// Actions
const actions = {
  // Project actions
  LOAD_PROJECTS_START: 'LOAD_PROJECTS_START',
  LOAD_PROJECTS_SUCCESS: 'LOAD_PROJECTS_SUCCESS',
  LOAD_PROJECTS_ERROR: 'LOAD_PROJECTS_ERROR',
  
  CREATE_PROJECT_START: 'CREATE_PROJECT_START',
  CREATE_PROJECT_SUCCESS: 'CREATE_PROJECT_SUCCESS',
  CREATE_PROJECT_ERROR: 'CREATE_PROJECT_ERROR',
  
  SELECT_PROJECT: 'SELECT_PROJECT',
  
  // Chat actions
  SEND_MESSAGE_START: 'SEND_MESSAGE_START',
  SEND_MESSAGE_SUCCESS: 'SEND_MESSAGE_SUCCESS',
  SEND_MESSAGE_ERROR: 'SEND_MESSAGE_ERROR',
  
  RECEIVE_STREAM_CHUNK: 'RECEIVE_STREAM_CHUNK',
  STREAM_COMPLETE: 'STREAM_COMPLETE',
  
  // Configuration actions
  LOAD_CONFIG_SUCCESS: 'LOAD_CONFIG_SUCCESS',
  UPDATE_CONFIG_START: 'UPDATE_CONFIG_START',
  UPDATE_CONFIG_SUCCESS: 'UPDATE_CONFIG_SUCCESS',
  
  // Health monitoring
  UPDATE_PROJECT_HEALTH: 'UPDATE_PROJECT_HEALTH'
};

// Async action creators
const loadProjects = () => async (dispatch, getState) => {
  dispatch({ type: actions.LOAD_PROJECTS_START });
  
  try {
    const client = new AAFApiClient(AAF_CONFIG);
    const result = await client.listProjects();
    
    dispatch({
      type: actions.LOAD_PROJECTS_SUCCESS,
      payload: result.projects
    });
  } catch (error) {
    dispatch({
      type: actions.LOAD_PROJECTS_ERROR,
      payload: AAFErrorHandler.handle(error, 'projects')
    });
  }
};

const sendChatMessage = (projectId, message, sessionId) => async (dispatch) => {
  dispatch({ type: actions.SEND_MESSAGE_START });
  
  try {
    const client = new AAFApiClient(AAF_CONFIG);
    const result = await client.sendChatMessage(projectId, message, sessionId);
    
    dispatch({
      type: actions.SEND_MESSAGE_SUCCESS,
      payload: { projectId, sessionId, message, response: result }
    });
  } catch (error) {
    dispatch({
      type: actions.SEND_MESSAGE_ERROR,
      payload: AAFErrorHandler.handle(error, 'chat')
    });
  }
};
```

### **7. WebSocket Integration (for real-time chat)**

```javascript
class AAFWebSocketManager {
  constructor(config) {
    this.config = config;
    this.connections = new Map();
  }
  
  async connectToProject(projectId, sessionId) {
    // Since we're proxying through orchestrator, we need to handle WebSocket differently
    // Option 1: Direct WebSocket to AAF instance (requires service URL)
    const client = new AAFApiClient(this.config);
    const project = await client.getProject(projectId);
    
    const wsUrl = project.service_url.replace('https://', 'wss://') + '/api/ws';
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected to project:', projectId);
      
      // Send initial message
      ws.send(JSON.stringify({
        type: 'ping',
        data: { session_id: sessionId }
      }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleWebSocketMessage(projectId, data);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected from project:', projectId);
      this.connections.delete(projectId);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error for project:', projectId, error);
    };
    
    this.connections.set(projectId, ws);
    return ws;
  }
  
  sendMessage(projectId, message, sessionId) {
    const ws = this.connections.get(projectId);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'chat',
        data: {
          message,
          session_id: sessionId,
          stream: true
        }
      }));
    }
  }
  
  handleWebSocketMessage(projectId, data) {
    // Emit to components or state management
    if (data.type === 'agent_chunk') {
      // Handle streaming response chunk
      this.onStreamChunk?.(projectId, data);
    } else if (data.type === 'agent_response') {
      // Handle complete response
      this.onMessage?.(projectId, data);
    }
  }
  
  disconnect(projectId) {
    const ws = this.connections.get(projectId);
    if (ws) {
      ws.close();
      this.connections.delete(projectId);
    }
  }
  
  disconnectAll() {
    this.connections.forEach(ws => ws.close());
    this.connections.clear();
  }
}
```

### **8. Environment Configuration**

```javascript
// config/environment.js
const environments = {
  development: {
    orchestratorUrl: 'http://localhost:8080',
    orchestratorApiSecret: 'dev-api-secret',
    debug: true,
    polling: {
      projects: 10000,    // 10 seconds
      health: 60000       // 1 minute
    }
  },
  
  staging: {
    orchestratorUrl: 'https://staging-orchestrator.company.com',
    orchestratorApiSecret: process.env.REACT_APP_STAGING_API_SECRET,
    debug: false,
    polling: {
      projects: 30000,    // 30 seconds
      health: 120000      // 2 minutes
    }
  },
  
  production: {
    orchestratorUrl: 'https://orchestrator.company.com',
    orchestratorApiSecret: process.env.REACT_APP_PROD_API_SECRET,
    debug: false,
    polling: {
      projects: 60000,    // 1 minute
      health: 300000      // 5 minutes
    }
  }
};

export const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return environments[env];
};
```

## **Summary: Frontend Only Needs**

1. **🔗 Orchestrator URL**: Single endpoint for all operations
2. **🔑 API Secret**: One secret for orchestrator authentication  
3. **📋 Project List**: Get from `/projects` endpoint
4. **🔄 Proxy Pattern**: Use `/proxy/{project_id}/{aaf_path}` for all AAF APIs
5. **❤️ Health Monitoring**: Built-in health check endpoints
6. **⚡ Real-time Updates**: Optional WebSocket or polling for live updates

**The frontend never needs to know individual project credentials or service URLs - the orchestrator handles everything!** 🚀

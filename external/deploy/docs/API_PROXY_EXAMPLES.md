# Complete AAF API Proxy Examples

The Backend Orchestrator proxies **ALL** AAF APIs to individual instances. Here are comprehensive examples:

## **Chat APIs**

```bash
# Send chat message
curl -X POST "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "user123"}'

# Stream chat response
curl -X POST "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/stream" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": true}'

# List available agents
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/agents" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Get session info
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/sessions/user123" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"
```

## **Management APIs**

```bash
# Get current configuration
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/management/config" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Update agent configuration
curl -X POST "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/management/agents" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new_agent",
    "model": "gpt-4",
    "behavior": "helpful",
    "system_prompt": "You are a helpful assistant"
  }'

# Restart AAF instance
curl -X POST "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/management/restart" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}" \
  -d '{"force": false}'
```

## **Configuration Editor APIs**

```bash
# Get current config (frontend format)
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/config-editor/current" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Validate configuration
curl -X POST "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/config-editor/validate" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{"agents": [{"id": "test", "model": "gpt-4"}]}'

# Get JSON schema for forms
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/config-editor/schema" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Get configuration templates
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/config-editor/templates" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"
```

## **Session Management**

```bash
# List active sessions
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/sessions" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Get session statistics
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/sessions/stats" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Reset specific session
curl -X POST "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/chat/sessions/user123/reset" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"
```

## **Health & Monitoring**

```bash
# AAF instance health
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/health" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# Management API health
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/management/health" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"

# WebSocket statistics
curl "${ORCHESTRATOR_URL}/proxy/${PROJECT_ID}/api/ws/stats" \
  -H "Authorization: Bearer ${ORCHESTRATOR_API_SECRET}"
```

## **Frontend Integration Examples**

### **React: Complete AAF Management**

```jsx
class AAFInstanceManager {
  constructor(orchestratorUrl, apiSecret, projectId) {
    this.baseUrl = `${orchestratorUrl}/proxy/${projectId}`;
    this.headers = {
      'Authorization': `Bearer ${apiSecret}`,
      'Content-Type': 'application/json'
    };
  }
  
  // Chat APIs
  async sendMessage(message, sessionId) {
    const response = await fetch(`${this.baseUrl}/api/chat/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ message, session_id: sessionId })
    });
    return await response.json();
  }
  
  async streamChat(message, sessionId) {
    const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ message, session_id: sessionId, stream: true })
    });
    
    const reader = response.body.getReader();
    return {
      async *[Symbol.asyncIterator]() {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = new TextDecoder().decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              yield data;
            }
          }
        }
      }
    };
  }
  
  // Management APIs
  async getConfiguration() {
    const response = await fetch(`${this.baseUrl}/api/management/config`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  async updateAgent(agentConfig) {
    const response = await fetch(`${this.baseUrl}/api/management/agents`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(agentConfig)
    });
    return await response.json();
  }
  
  async restartInstance() {
    const response = await fetch(`${this.baseUrl}/api/management/restart`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ force: false })
    });
    return await response.json();
  }
  
  // Configuration Editor APIs
  async getCurrentConfig() {
    const response = await fetch(`${this.baseUrl}/api/config-editor/current`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  async validateConfig(config) {
    const response = await fetch(`${this.baseUrl}/api/config-editor/validate`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(config)
    });
    return await response.json();
  }
  
  async getConfigSchema() {
    const response = await fetch(`${this.baseUrl}/api/config-editor/schema`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  async getTemplates() {
    const response = await fetch(`${this.baseUrl}/api/config-editor/templates`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  // Session Management
  async listSessions() {
    const response = await fetch(`${this.baseUrl}/api/chat/sessions`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  async getSessionStats() {
    const response = await fetch(`${this.baseUrl}/api/chat/sessions/stats`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  async resetSession(sessionId) {
    const response = await fetch(`${this.baseUrl}/api/chat/sessions/${sessionId}/reset`, {
      method: 'POST',
      headers: this.headers
    });
    return await response.json();
  }
  
  // Health & Monitoring
  async checkHealth() {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: this.headers
    });
    return await response.json();
  }
  
  async getWebSocketStats() {
    const response = await fetch(`${this.baseUrl}/api/ws/stats`, {
      headers: this.headers
    });
    return await response.json();
  }
}

// Usage
const aafManager = new AAFInstanceManager(
  'https://orchestrator-url.com',
  'your-api-secret',
  'project-id-123'
);

// Chat with the instance
const response = await aafManager.sendMessage('Hello!', 'user-session-123');

// Stream chat
for await (const chunk of aafManager.streamChat('Hello!', 'user-session-123')) {
  console.log('Chunk:', chunk);
}

// Update configuration
await aafManager.updateAgent({
  id: 'support_bot',
  model: 'gpt-4',
  system_prompt: 'Updated prompt'
});
```

### **Vue.js: Project Management Dashboard**

```vue
<template>
  <div class="aaf-dashboard">
    <div class="project-selector">
      <select v-model="selectedProject" @change="loadProjectData">
        <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
          {{ project.project_name }}
        </option>
      </select>
    </div>
    
    <div v-if="selectedProject" class="project-management">
      <!-- Chat Interface -->
      <div class="chat-section">
        <h3>Test Chat</h3>
        <div class="chat-messages" ref="chatMessages">
          <div v-for="msg in chatMessages" :key="msg.id" class="message">
            <strong>{{ msg.sender }}:</strong> {{ msg.content }}
          </div>
        </div>
        <div class="chat-input">
          <input v-model="chatInput" @keyup.enter="sendMessage" placeholder="Type a message...">
          <button @click="sendMessage">Send</button>
        </div>
      </div>
      
      <!-- Configuration Management -->
      <div class="config-section">
        <h3>Configuration</h3>
        <button @click="loadCurrentConfig">Load Current Config</button>
        <button @click="showConfigEditor">Edit Configuration</button>
        <button @click="restartInstance">Restart Instance</button>
        
        <div v-if="currentConfig" class="config-display">
          <h4>Current Agents:</h4>
          <ul>
            <li v-for="agent in currentConfig.agents" :key="agent.id">
              {{ agent.id }} - {{ agent.model }} ({{ agent.behavior }})
            </li>
          </ul>
        </div>
      </div>
      
      <!-- Session Management -->
      <div class="session-section">
        <h3>Active Sessions</h3>
        <button @click="loadSessions">Refresh Sessions</button>
        
        <div v-if="sessions" class="sessions-list">
          <div v-for="session in sessions" :key="session.session_id" class="session-item">
            <span>{{ session.session_id }}</span>
            <span>{{ session.created_at }}</span>
            <button @click="resetSession(session.session_id)">Reset</button>
          </div>
        </div>
        
        <div v-if="sessionStats" class="session-stats">
          <h4>Statistics:</h4>
          <p>Total Sessions: {{ sessionStats.total_active_sessions }}</p>
          <p>Sessions Last Hour: {{ sessionStats.sessions_last_hour }}</p>
        </div>
      </div>
      
      <!-- Health Monitoring -->
      <div class="health-section">
        <h3>Health Status</h3>
        <button @click="checkHealth">Check Health</button>
        
        <div v-if="healthStatus" class="health-display">
          <p>Status: <span :class="healthStatus.status">{{ healthStatus.status }}</span></p>
          <p>LangSwarm: {{ healthStatus.langswarm_status }}</p>
          <p>Agents: {{ healthStatus.agents_count }}</p>
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
      selectedProject: null,
      chatMessages: [],
      chatInput: '',
      currentConfig: null,
      sessions: null,
      sessionStats: null,
      healthStatus: null,
      orchestratorUrl: 'https://your-orchestrator.com',
      apiSecret: 'your-orchestrator-api-secret'
    };
  },
  
  async mounted() {
    await this.loadProjects();
  },
  
  methods: {
    async loadProjects() {
      const response = await fetch(`${this.orchestratorUrl}/projects`, {
        headers: { 'Authorization': `Bearer ${this.apiSecret}` }
      });
      const data = await response.json();
      this.projects = data.projects;
    },
    
    async loadProjectData() {
      if (!this.selectedProject) return;
      
      await Promise.all([
        this.loadCurrentConfig(),
        this.loadSessions(),
        this.checkHealth()
      ]);
    },
    
    async sendMessage() {
      if (!this.chatInput.trim()) return;
      
      const message = this.chatInput;
      this.chatInput = '';
      
      // Add user message
      this.chatMessages.push({
        id: Date.now(),
        sender: 'User',
        content: message
      });
      
      // Send to AAF
      const response = await fetch(
        `${this.orchestratorUrl}/proxy/${this.selectedProject}/api/chat/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.apiSecret}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message,
            session_id: 'dashboard-test-session'
          })
        }
      );
      
      const result = await response.json();
      
      // Add assistant response
      this.chatMessages.push({
        id: Date.now() + 1,
        sender: 'Assistant',
        content: result.response
      });
      
      // Scroll to bottom
      this.$nextTick(() => {
        this.$refs.chatMessages.scrollTop = this.$refs.chatMessages.scrollHeight;
      });
    },
    
    async loadCurrentConfig() {
      const response = await fetch(
        `${this.orchestratorUrl}/proxy/${this.selectedProject}/api/config-editor/current`,
        {
          headers: { 'Authorization': `Bearer ${this.apiSecret}` }
        }
      );
      this.currentConfig = await response.json();
    },
    
    async restartInstance() {
      if (!confirm('Are you sure you want to restart this instance?')) return;
      
      const response = await fetch(
        `${this.orchestratorUrl}/proxy/${this.selectedProject}/api/management/restart`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.apiSecret}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ force: false })
        }
      );
      
      const result = await response.json();
      alert(result.message);
    },
    
    async loadSessions() {
      const [sessionsResponse, statsResponse] = await Promise.all([
        fetch(`${this.orchestratorUrl}/proxy/${this.selectedProject}/api/chat/sessions`, {
          headers: { 'Authorization': `Bearer ${this.apiSecret}` }
        }),
        fetch(`${this.orchestratorUrl}/proxy/${this.selectedProject}/api/chat/sessions/stats`, {
          headers: { 'Authorization': `Bearer ${this.apiSecret}` }
        })
      ]);
      
      const sessionsData = await sessionsResponse.json();
      this.sessions = sessionsData.sessions;
      this.sessionStats = await statsResponse.json();
    },
    
    async resetSession(sessionId) {
      await fetch(
        `${this.orchestratorUrl}/proxy/${this.selectedProject}/api/chat/sessions/${sessionId}/reset`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${this.apiSecret}` }
        }
      );
      
      await this.loadSessions(); // Refresh
    },
    
    async checkHealth() {
      const response = await fetch(
        `${this.orchestratorUrl}/proxy/${this.selectedProject}/health`,
        {
          headers: { 'Authorization': `Bearer ${this.apiSecret}` }
        }
      );
      this.healthStatus = await response.json();
    }
  }
};
</script>
```

The proxy provides **complete transparent access** to all AAF functionality through a single orchestrator endpoint! 🚀

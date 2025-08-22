# Custom Backend Integration Guide

## 📚 **Reading Order**

1. **[Overview](01_OVERVIEW.md)** - Understand what custom backend integration provides
2. **[Endpoints](02_ENDPOINTS.md)** - Learn the 4 required API endpoints  
3. **[Implementation](03_IMPLEMENTATION.md)** - See code examples in Node.js and Python
4. **[Adoption](04_ADOPTION.md)** - Register your backend with the orchestrator
5. **[Troubleshooting](05_TROUBLESHOOTING.md)** - Fix common integration issues

## 🎯 **What You're Building**

### **4 Simple Endpoints**
```
GET  /health                 - Service validation
GET  /api/prompts/schema     - What can be configured  
GET  /api/prompts           - Current prompt values
PUT  /api/prompts           - Update prompt values
```

### **What You Get**
- **Centralized prompt management** via web UI
- **No code deployments** needed for prompt changes
- **Unified control** across all your AI services
- **Simple integration** - your service stays unchanged

### **What You DON'T Need**
- ❌ Demo management system
- ❌ Knowledge base features  
- ❌ Multi-tool integrations
- ❌ Complex configuration management

## ⚡ **Quick Start**

### **1. Add Health Endpoint**
```javascript
app.get('/health', (req, res) => {
  res.json({
    status: "healthy",
    backend_type: "custom",
    prompt_management: { enabled: true, method: "api" }
  });
});
```

### **2. Define Your Prompts**
```javascript
app.get('/api/prompts/schema', (req, res) => {
  res.json({
    fields: [
      {
        name: "system_prompt",
        label: "System Prompt", 
        type: "textarea",
        required: true
      }
    ]
  });
});
```

### **3. Get/Set Prompts**
```javascript
let prompts = { system_prompt: "You are a helpful assistant." };

app.get('/api/prompts', (req, res) => res.json(prompts));

app.put('/api/prompts', (req, res) => {
  Object.assign(prompts, req.body);
  applyPromptsToAI(prompts); // Your integration point
  res.json({ success: true, updated_prompts: Object.keys(req.body) });
});
```

### **4. Adopt Your Backend**
```bash
curl -X POST https://orchestrator-url/api/backends/adopt \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Backend",
    "backend_type": "custom",
    "service_url": "https://my-backend.run.app"
  }'
```

## 🔧 **Integration Points**

### **Apply Prompts to Your AI**
The key integration point is the `applyPromptsToAI()` function - this is where you connect the orchestrator's prompt updates to your existing AI system:

```javascript
function applyPromptsToAI(prompts) {
  // Update your AI engine with new prompts
  aiEngine.setSystemPrompt(prompts.system_prompt);
  aiEngine.setAssistantName(prompts.assistant_name);
  // ... your specific AI integration logic
}
```

## 📋 **Success Criteria**

Your backend is successfully integrated when:

- ✅ Health endpoint returns correct format
- ✅ Schema defines your configurable prompts
- ✅ Get/Put prompts work correctly  
- ✅ Adoption via orchestrator succeeds
- ✅ Prompt updates apply to your AI system
- ✅ Frontend shows prompt editor for your backend

## 🆘 **Need Help?**

- Check [Troubleshooting](05_TROUBLESHOOTING.md) for common issues
- Test each endpoint individually before adoption
- Start with minimal implementation, add complexity gradually
- Verify orchestrator can reach your service URL

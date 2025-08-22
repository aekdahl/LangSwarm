# Troubleshooting Custom Backend Integration

## 🚨 **Common Issues**

### **❌ Adoption Fails - Health Check**

**Error:** `Backend health check failed`

**Causes:**
- Health endpoint returns wrong format
- Health endpoint not accessible  
- Missing required fields

**Solutions:**
```bash
# Test your health endpoint
curl https://your-backend.run.app/health

# Should return:
{
  "status": "healthy",
  "backend_type": "custom",
  "prompt_management": {
    "enabled": true,
    "method": "api"
  }
}

# Required fields:
# - status: "healthy" 
# - backend_type: "custom"
# - prompt_management.enabled: true
# - prompt_management.method: "api"
```

---

### **❌ Schema Endpoint Not Working**

**Error:** `Failed to load prompt schema`

**Causes:**
- Endpoint returns wrong format
- Missing field definitions
- Invalid field types

**Solutions:**
```bash
# Test schema endpoint
curl https://your-backend.run.app/api/prompts/schema

# Should return:
{
  "fields": [
    {
      "name": "system_prompt",
      "label": "System Prompt", 
      "type": "textarea",
      "required": true
    }
  ]
}

# Valid field types: text, textarea, select, number, password
# Required field properties: name, label, type
```

---

### **❌ Prompt Updates Not Working**

**Error:** `Failed to update prompts`

**Causes:**
- PUT endpoint not implemented
- Wrong response format
- Authentication issues

**Solutions:**
```bash
# Test update endpoint
curl -X PUT https://your-backend.run.app/api/prompts \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "Test prompt"}'

# Should return:
{
  "success": true,
  "updated_prompts": ["system_prompt"],
  "restart_required": false
}

# Required response fields:
# - success: boolean
# - updated_prompts: array of updated field names
```

---

### **❌ Authentication Issues**

**Error:** `Authentication failed`

**Causes:**
- Wrong authentication type
- Invalid credentials
- Missing auth headers

**Solutions:**

**For API Key:**
```javascript
// In your backend
app.use((req, res, next) => {
  const apiKey = req.headers['authorization']?.replace('Bearer ', '') || 
                 req.headers['x-api-key'];
  
  if (apiKey !== 'your-secret-key') {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  next();
});
```

**For Basic Auth:**
```javascript
app.use((req, res, next) => {
  const auth = req.headers['authorization'];
  if (!auth || !auth.startsWith('Basic ')) {
    return res.status(401).json({ error: 'Basic auth required' });
  }
  
  const credentials = Buffer.from(auth.slice(6), 'base64').toString();
  const [username, password] = credentials.split(':');
  
  if (username !== 'admin' || password !== 'secret') {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  next();
});
```

---

## 🔍 **Debugging Steps**

### **1. Check Cloud Run Service**
```bash
# Verify service is running
gcloud run services describe my-custom-service \
  --region=us-central1 \
  --project=my-project
```

### **2. Check Service URL**
```bash
# Get the correct service URL
gcloud run services describe my-custom-service \
  --region=us-central1 \
  --project=my-project \
  --format="value(status.url)"
```

### **3. Test All Endpoints**
```bash
BASE_URL="https://your-service-url.run.app"

# Test each endpoint
curl $BASE_URL/health
curl $BASE_URL/api/prompts/schema  
curl $BASE_URL/api/prompts
curl -X PUT $BASE_URL/api/prompts -H "Content-Type: application/json" -d '{}'
```

### **4. Check Orchestrator Logs**
```bash
# View orchestrator logs for adoption errors
gcloud run services logs read orchestrator \
  --region=us-central1 \
  --project=your-project \
  --limit=50
```

---

## 📋 **Validation Checklist**

Before attempting adoption, verify:

- [ ] Health endpoint returns correct format
- [ ] Schema endpoint returns valid field definitions  
- [ ] Get prompts endpoint returns current values
- [ ] Update prompts endpoint accepts PUT requests
- [ ] All endpoints use correct content types (JSON)
- [ ] Authentication is working (if configured)
- [ ] Service URL is accessible from orchestrator
- [ ] CORS is configured if needed

---

## 🆘 **Still Having Issues?**

### **Check Orchestrator Health**
```bash
curl https://orchestrator-url.run.app/health
```

### **Verify Network Access**
Make sure the orchestrator can reach your backend:
- Both services in same GCP project
- No VPC or firewall restrictions
- Public Cloud Run services (not requiring authentication to access)

### **Review Required vs Optional**
- **Required:** health, schema, get prompts, update prompts endpoints
- **Optional:** authentication, custom endpoint paths, descriptions

### **Test with Minimal Implementation**
Start with the simplest possible implementation and add complexity gradually.

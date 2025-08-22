# Implementation Examples

## 🟢 **Node.js / Express**

```javascript
const express = require('express');
const app = express();
app.use(express.json());

// Simple in-memory storage (use database in production)
let currentPrompts = {
  system_prompt: "You are a helpful assistant.",
  assistant_name: "AI Helper", 
  response_style: "professional"
};

// 1. Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: "healthy",
    service: "my-custom-backend",
    version: "1.0.0", 
    backend_type: "custom",
    prompt_management: {
      enabled: true,
      method: "api"
    }
  });
});

// 2. Prompt schema
app.get('/api/prompts/schema', (req, res) => {
  res.json({
    fields: [
      {
        name: "system_prompt",
        label: "System Prompt",
        type: "textarea",
        required: true,
        description: "Main AI behavior prompt"
      },
      {
        name: "assistant_name", 
        label: "Assistant Name",
        type: "text",
        default: "AI Assistant"
      },
      {
        name: "response_style",
        label: "Response Style",
        type: "select", 
        options: ["professional", "casual", "technical"],
        default: "professional"
      }
    ]
  });
});

// 3. Get current prompts
app.get('/api/prompts', (req, res) => {
  res.json(currentPrompts);
});

// 4. Update prompts
app.put('/api/prompts', (req, res) => {
  const updatedFields = [];
  
  for (const [key, value] of Object.entries(req.body)) {
    if (currentPrompts.hasOwnProperty(key)) {
      currentPrompts[key] = value;
      updatedFields.push(key);
      
      // Apply the prompt to your AI system
      applyPromptToAI(key, value);
    }
  }
  
  res.json({
    success: true,
    updated_prompts: updatedFields,
    restart_required: false
  });
});

// Your AI logic implementation
function applyPromptToAI(promptKey, promptValue) {
  console.log(`Applying ${promptKey}: ${promptValue}`);
  // Update your AI system with new prompt
  // This is where you integrate with your existing AI logic
}

app.listen(8080, () => {
  console.log('Custom backend running on port 8080');
});
```

---

## 🐍 **Python / FastAPI**

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Any

app = FastAPI()

# Simple in-memory storage (use database in production)
current_prompts = {
    "system_prompt": "You are a helpful assistant.",
    "assistant_name": "AI Helper",
    "response_style": "professional"
}

class PromptUpdate(BaseModel):
    system_prompt: str = None
    assistant_name: str = None  
    response_style: str = None

# 1. Health endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "my-custom-backend", 
        "version": "1.0.0",
        "backend_type": "custom",
        "prompt_management": {
            "enabled": True,
            "method": "api"
        }
    }

# 2. Prompt schema
@app.get("/api/prompts/schema")
async def get_prompt_schema():
    return {
        "fields": [
            {
                "name": "system_prompt",
                "label": "System Prompt",
                "type": "textarea",
                "required": True,
                "description": "Main AI behavior prompt"
            },
            {
                "name": "assistant_name",
                "label": "Assistant Name", 
                "type": "text",
                "default": "AI Assistant"
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

# 3. Get current prompts
@app.get("/api/prompts")
async def get_prompts():
    return current_prompts

# 4. Update prompts
@app.put("/api/prompts")
async def update_prompts(updates: Dict[str, Any]):
    updated_fields = []
    
    for key, value in updates.items():
        if key in current_prompts:
            current_prompts[key] = value
            updated_fields.append(key)
            
            # Apply to your AI system
            apply_prompt_to_ai(key, value)
    
    return {
        "success": True,
        "updated_prompts": updated_fields,
        "restart_required": False
    }

def apply_prompt_to_ai(prompt_key: str, prompt_value: str):
    print(f"Applying {prompt_key}: {prompt_value}")
    # Update your AI system with new prompt
    # This is where you integrate with your existing AI logic
```

---

## 🔧 **Integration Points**

### **Apply Prompts to Your AI**
```python
def apply_prompt_to_ai(prompt_key: str, prompt_value: str):
    if prompt_key == "system_prompt":
        # Update your AI's system prompt
        ai_engine.set_system_prompt(prompt_value)
    elif prompt_key == "assistant_name":
        # Update how AI introduces itself
        ai_engine.set_assistant_name(prompt_value) 
    elif prompt_key == "response_style":
        # Update response style settings
        ai_engine.set_style(prompt_value)
```

### **Database Storage (Recommended)**
```python
# Instead of in-memory storage, use a database
import sqlite3

def save_prompt(key: str, value: str):
    conn = sqlite3.connect('prompts.db')
    conn.execute(
        "INSERT OR REPLACE INTO prompts (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def load_prompts() -> Dict[str, str]:
    conn = sqlite3.connect('prompts.db')
    cursor = conn.execute("SELECT key, value FROM prompts")
    prompts = dict(cursor.fetchall())
    conn.close()
    return prompts
```

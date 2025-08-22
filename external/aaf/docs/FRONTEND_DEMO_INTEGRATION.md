# Frontend Demo Integration Guide

This guide provides the essential API information for integrating the AAF demo system into your frontend application.

## 🎯 **Overview**

The demo system provides APIs for:
1. **Create** AI-powered demos of any website with embedded chat
2. **Manage** demo collections with creation, listing, and deletion
3. **View** demos via shareable URLs that clients can access
4. **Edit** designs via design editor APIs (frontend will build the editor)

---

## 📝 **Complete API Reference**

### **1. Demo Management**

#### **Create Demo**
```http
POST /api/demo/create
Content-Type: application/json

{
  "url": "https://client-website.com",
  "title": "ClientCorp Demo",
  "design_preference": "professional",
  "use_ai_design": true,
  "use_ai_prompt": true,
  "created_by": "user_id_123",
  "tags": ["sales", "client-corp"]
}
```

**AI Design Preferences:** `professional`, `modern`, `playful`, `minimal`

**Response:**
```json
{
  "demo_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "ClientCorp Demo",
  "source_url": "https://client-website.com",
  "design": { /* Complete AI-generated design object */ },
  "created_at": "2025-08-21T06:30:00Z",
  "view_count": 0,
  "status": "active"
}
```

#### **List Demos**
```http
GET /api/demo/list?created_by=user_id&limit=50
```

#### **Get Demo Info**
```http
GET /api/demo/info/{demo_id}
```

#### **Delete Demo**
```http
DELETE /api/demo/delete/{demo_id}?permanent=false
```

### **2. Demo Viewing (Client Access)**

#### **View Demo** (Shareable URL)
```http
GET /api/demo/view/{demo_id}
```
Returns complete HTML page with embedded chat widget.

#### **Demo Page Access** (Clean URL for clients)
```http
GET /demo/{demo_id}
```
User-friendly URL that redirects to the demo viewer.

### **3. Design Editor APIs**

#### **Get Current Design**
```http
GET /api/demo/design/{demo_id}
```

Returns complete design object with 25+ properties:
```json
{
  "chat_position": "bottom-right",
  "chat_title": "Chat with us",
  "primary_color": "#007bff",
  "background_color": "#ffffff",
  "font_family": "Inter, sans-serif",
  "auto_open": false,
  "enable_file_upload": true,
  "generated_by_ai": true,
  "ai_confidence": 0.85,
  // ... 20+ more design properties
}
```

#### **Update Design**
```http
PUT /api/demo/design/{demo_id}
Content-Type: application/json

{
  "design": { /* Complete design object with changes */ },
  "update_reason": "Client requested brand colors"
}
```

#### **Reset to AI Baseline**
```http
POST /api/demo/design/{demo_id}/reset?design_preference=professional
```

---

## 🔧 **Implementation Examples**

### **Basic Demo Creation**
```javascript
const createDemo = async (websiteUrl, userId) => {
  const response = await fetch('/api/demo/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: websiteUrl,
      title: `Demo of ${new URL(websiteUrl).hostname}`,
      design_preference: 'professional',
      use_ai_design: true,
      created_by: userId
    })
  });
  
  if (!response.ok) {
    throw new Error(`Demo creation failed: ${response.statusText}`);
  }
  
  return await response.json();
};
```

### **Demo Management**
```javascript
// Get user's demos
const demos = await fetch('/api/demo/list?created_by=user123').then(r => r.json());

// Get shareable URL for clients
const getClientUrl = (demoId) => `/demo/${demoId}`;

// Delete demo
await fetch(`/api/demo/delete/${demoId}`, { method: 'DELETE' });
```

### **Design Editor Integration**
```javascript
// Load design for editor
const design = await fetch(`/api/demo/design/${demoId}`).then(r => r.json());

// Save design changes
await fetch(`/api/demo/design/${demoId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    design: modifiedDesign,
    update_reason: 'Updated colors and positioning'
  })
});

// Reset to AI baseline
await fetch(`/api/demo/design/${demoId}/reset?design_preference=modern`, {
  method: 'POST'
});
```

---

## 🎨 **Design Object Properties**

The design object contains 25+ editable properties organized in categories:

### **Basic Settings**
- `chat_position`: "bottom-right" | "bottom-left" | "top-right" | "top-left"
- `chat_title`: string
- `chat_subtitle`: string
- `chat_placeholder`: string

### **Visual Design**
- `primary_color`: hex color
- `secondary_color`: hex color
- `text_color`: hex color
- `background_color`: hex color
- `border_radius`: CSS value (e.g., "8px")
- `font_family`: CSS font family

### **Widget Behavior**
- `auto_open`: boolean
- `show_launcher`: boolean
- `enable_sound`: boolean
- `enable_typing_indicator`: boolean

### **Layout**
- `widget_width`: CSS value
- `widget_height`: CSS value
- `max_height`: CSS value

### **Advanced Features**
- `enable_file_upload`: boolean
- `enable_emoji_picker`: boolean
- `enable_markdown`: boolean
- `custom_css`: string

### **AI Metadata**
- `generated_by_ai`: boolean
- `ai_confidence`: number (0-1)
- `design_reasoning`: string

---

## 🔧 **Error Handling**

### **Common Error Responses**
```json
{
  "detail": "Failed to create demo: Database not available"
}
```

### **Error Handling Pattern**
```javascript
const handleDemoAPI = async (apiCall) => {
  try {
    return await apiCall();
  } catch (error) {
    if (error.message.includes('Firestore')) {
      throw new Error('Database not available. Please contact support.');
    } else if (error.message.includes('website')) {
      throw new Error('Unable to access the specified website.');
    } else {
      throw new Error('Operation failed. Please try again.');
    }
  }
};
```

---

## 🛠 **Frontend Implementation Notes**

### **Demo Management Section**
Create a demo management interface that includes:
- ✅ **Demo creation form** (URL input + AI style selection)
- ✅ **Demo list/grid** with preview thumbnails
- ✅ **Share URL copying** (`/demo/{demo_id}`)
- ✅ **Delete confirmation**
- ✅ **View counts and created dates**

### **Design Editor**
Build a visual design editor that:
- ✅ **Loads design** via `GET /design/{demo_id}`
- ✅ **Live preview** via iframe to `/demo/{demo_id}`
- ✅ **Save changes** via `PUT /design/{demo_id}`
- ✅ **Reset options** via `POST /design/{demo_id}/reset`
- ✅ **Color pickers, dropdowns, checkboxes** for all design properties

### **Client Demo Access**
Implement clean demo URLs:
- ✅ **`/demo/{demo_id}`** - User-friendly URL for clients
- ✅ **Full-screen demo view** without your app's navigation
- ✅ **Social sharing metadata** for link previews

---

## 🚀 **Getting Started**

1. **Set up demo management** with create/list/delete functionality
2. **Add shareable URLs** using `/demo/{demo_id}` format  
3. **Build design editor** using the design API endpoints
4. **Test with real websites** to see AI design generation
5. **Customize styling** to match your application's theme

**All design changes persist automatically via Firestore - no additional persistence work needed!**

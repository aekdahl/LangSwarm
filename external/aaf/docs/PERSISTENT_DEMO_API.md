# Persistent Demo API Documentation

The Persistent Demo API allows you to create shareable demo pages that are stored and can be accessed via unique URLs. Perfect for client presentations, sales demos, and showcasing AAF functionality.

## Features

🔗 **Shareable URLs**: Create persistent demo pages with unique URLs
💾 **Cloud Storage**: HTML content stored in Google Cloud Storage
📊 **Analytics**: View counts and access tracking
⏰ **Expiration**: Automatic cleanup of expired demos
🎨 **Full Customization**: All demo features (AI design, themes, positioning)
🔒 **Access Control**: Optional creator filtering and permissions

## Base URL
```
/api/demo/
```

---

## Endpoints

### 1. Create Persistent Demo

**`POST /api/demo/create`**

Create a new persistent demo page with shareable URL.

**Request Body:**
```json
{
  "url": "https://example.com",
  "title": "Custom Demo Title",
  
  "chat_position": "bottom-right",
  "chat_theme": "light",
  "chat_title": "Chat with us",
  "chat_subtitle": "We're here to help!",
  "chat_placeholder": "Type your message...",
  
  "primary_color": "#007bff",
  "secondary_color": "#6c757d",
  "text_color": "#333333",
  "background_color": "#ffffff",
  "border_radius": "12px",
  "font_family": "Inter, sans-serif",
  
  "auto_open": false,
  "show_launcher": true,
  "enable_sound": true,
  "enable_typing_indicator": true,
  
  "enable_branding": false,
  "custom_css": "/* Custom CSS */",
  "custom_logo_url": "https://example.com/logo.png",
  
  "use_ai_design": true,
  "use_ai_prompt": true,
  
  "widget_width": "350px",
  "widget_height": "500px",
  "max_height": "80vh",
  
  "enable_file_upload": false,
  "enable_emoji_picker": true,
  "enable_markdown": true,
  
  "created_by": "user_id_123",
  "tags": ["sales", "demo", "client-corp"]
}
```

**Complete Parameters:**
- `url` (required): Target website URL to reproduce
- `title` (optional): Custom title for the demo

**Chat Widget Design:**
- `chat_position`: `bottom-right`, `bottom-left`, `top-right`, `top-left`
- `chat_theme`: `light`, `dark`, `brand`, `custom`
- `chat_title`: Chat widget title text
- `chat_subtitle`: Optional subtitle text
- `chat_placeholder`: Input placeholder text

**Visual Design:**
- `primary_color`: Primary color (hex code, e.g., #007bff)
- `secondary_color`: Secondary color (hex code)
- `text_color`: Text color (hex code)
- `background_color`: Background color (hex code)
- `border_radius`: Border radius (e.g., 12px)
- `font_family`: Font family (e.g., 'Inter, sans-serif')

**Widget Behavior:**
- `auto_open`: Auto-open chat widget on page load
- `show_launcher`: Show chat launcher button
- `enable_sound`: Enable notification sounds
- `enable_typing_indicator`: Show typing indicator

**Branding & Customization:**
- `enable_branding`: Show "Powered by AAF" footer
- `custom_css`: Additional CSS for advanced styling
- `custom_logo_url`: URL to custom logo image

**AI Features:**
- `use_ai_design`: Enable AI-powered UI design generation
- `use_ai_prompt`: Generate personalized system prompt

**Widget Size & Layout:**
- `widget_width`: Widget width (e.g., 350px, 100%)
- `widget_height`: Widget height (e.g., 500px)
- `max_height`: Maximum widget height

**Advanced Features:**
- `enable_file_upload`: Allow file uploads in chat
- `enable_emoji_picker`: Show emoji picker
- `enable_markdown`: Support markdown formatting

**Metadata:**
- `created_by`: Optional creator identifier
- `tags`: Array of tags for organizing demos

**Response:**
```json
{
  "demo_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Demo of https://example.com",
  "source_url": "https://example.com",
  "chat_config": {
    "chat_position": "bottom-right",
    "chat_theme": "light",
    "chat_title": "Chat with us",
    "enable_branding": false,
    "custom_css": null,
    "use_ai_design": true,
    "use_ai_prompt": true
  },
  "created_at": "2025-08-20T21:30:00.000Z",
  "expires_at": "2025-08-27T21:30:00.000Z",
  "created_by": "user_id_123",
  "view_count": 0,
  "last_viewed": null,
  "status": "active"
}
```

### 2. View Demo Page

**`GET /api/demo/view/{demo_id}`**

View a stored demo page by its ID. This is the shareable URL.

**Example:**
```
https://your-aaf-instance.run.app/api/demo/view/550e8400-e29b-41d4-a716-446655440000
```

**Response:** HTML page with integrated chat widget

**Status Codes:**
- `200`: Demo loaded successfully
- `404`: Demo not found
- `410`: Demo expired or deleted

### 3. List Demo Pages

**`GET /api/demo/list`**

List stored demo pages with optional filtering.

**Query Parameters:**
- `created_by` (optional): Filter by creator ID
- `limit` (optional): Maximum number of results (default: 50)

**Example:**
```bash
curl "https://your-aaf-instance.run.app/api/demo/list?created_by=user_id_123&limit=10"
```

**Response:**
```json
[
  {
    "demo_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Demo of https://example.com",
    "source_url": "https://example.com",
    "created_at": "2025-08-20T21:30:00.000Z",
    "expires_at": "2025-08-27T21:30:00.000Z",
    "view_count": 5,
    "last_viewed": "2025-08-21T10:15:00.000Z",
    "status": "active"
  }
]
```

### 4. Get Demo Information

**`GET /api/demo/info/{demo_id}`**

Get demo metadata without viewing the content.

**Response:**
```json
{
  "demo_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Demo of https://example.com",
  "source_url": "https://example.com",
  "chat_config": {
    "chat_position": "bottom-right",
    "chat_theme": "light"
  },
  "created_at": "2025-08-20T21:30:00.000Z",
  "expires_at": "2025-08-27T21:30:00.000Z",
  "created_by": "user_id_123",
  "view_count": 5,
  "last_viewed": "2025-08-21T10:15:00.000Z",
  "status": "active"
}
```

### 5. Update Demo Design

**`PUT /api/demo/update/{demo_id}`**

Update an existing demo with new design parameters. This regenerates the demo with updated settings while preserving analytics.

**Request Body:** Same as create endpoint with full design parameters

**Response:** Updated DemoMetadata object

### 6. Delete Demo Page

**`DELETE /api/demo/delete/{demo_id}?permanent=false`**

Delete a demo page with soft delete (default) or hard delete options.

**Query Parameters:**
- `permanent` (optional): Set to `true` for hard delete (removes from storage completely)

**Response:**
```json
{
  "message": "Demo 550e8400-e29b-41d4-a716-446655440000 deleted (soft delete)",
  "permanent": false
}
```

### 7. Cleanup Expired Demos

**`POST /api/demo/cleanup`**

Admin endpoint to clean up expired demo pages.

**Response:**
```json
{
  "message": "Cleanup completed",
  "deleted_count": 3
}
```

---

## Storage Architecture

### Firestore Collections
- **Collection**: `aaf_demo_pages`
- **Document ID**: Demo UUID
- **Fields**: Metadata, configuration, timestamps, analytics

### Cloud Storage
- **Bucket**: `{project-id}-aaf-demos`
- **Path**: `demos/{demo_id}/index.html`
- **Content**: Complete HTML with embedded chat widget

---

## Usage Examples

### Frontend Integration

```javascript
// Create a persistent demo
const createDemo = async (url, config) => {
  const response = await fetch('/api/demo/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: url,
      title: `Demo of ${url}`,
      chat_theme: 'dark',
      use_ai_design: true,
      ttl_hours: 168,
      created_by: 'user_123'
    })
  });
  
  const demo = await response.json();
  console.log(`Demo created: /api/demo/view/${demo.demo_id}`);
  return demo;
};

// List user's demos
const listMyDemos = async (userId) => {
  const response = await fetch(`/api/demo/list?created_by=${userId}`);
  return await response.json();
};
```

### Sharing Demo URLs

```html
<!-- Email template -->
<a href="https://your-aaf-instance.run.app/api/demo/view/550e8400-e29b-41d4-a716-446655440000">
  View Interactive Demo
</a>

<!-- Social sharing -->
<meta property="og:url" content="https://your-aaf-instance.run.app/api/demo/view/550e8400-e29b-41d4-a716-446655440000">
<meta property="og:title" content="Interactive Chat Demo">
<meta property="og:description" content="See our AI chatbot in action on your website">
```

### Automated Cleanup

```bash
# Set up cron job for cleanup (run daily)
curl -X POST "https://your-aaf-instance.run.app/api/demo/cleanup"
```

---

## Benefits

### For Sales Teams
- 🎯 **Instant Demos**: Create demos on-demand during calls
- 📊 **Usage Analytics**: Track demo views and engagement
- 🔗 **Shareable Links**: Send persistent URLs via email/Slack
- ⏰ **Controlled Access**: Set expiration dates for security

### For Clients
- 🌐 **Real Website**: See their actual website with chat
- 💬 **Interactive**: Fully functional chat with real AI
- 📱 **Mobile Ready**: Works on all devices
- 🎨 **Branded**: AI-matched colors and design

### For Development
- 🧪 **Testing**: Create test demos for QA
- 📝 **Documentation**: Store demo examples
- 🔄 **Versioning**: Track different configurations
- 🧹 **Auto-cleanup**: No manual maintenance required

---

## Error Handling

| Status Code | Description | Action |
|-------------|-------------|---------|
| `404` | Demo not found | Check demo ID |
| `410` | Demo expired | Create new demo |
| `500` | Server error | Check logs |

## Security Notes

- Demo content is sanitized for XSS protection
- Expired demos are automatically cleaned up
- Access can be restricted by creator ID
- Cloud Storage buckets use IAM permissions

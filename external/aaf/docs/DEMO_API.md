# AAF Demo API Documentation

The Demo API allows you to reproduce customer websites with an integrated chat UI, perfect for testing and showcasing the AAF chatbot functionality.

## Features

🌐 **Website Reproduction**: Fetches and displays any public website
💬 **Integrated Chat Widget**: Fully functional chat interface overlay
🎨 **Customizable Themes**: Light, dark, and brand theme options
📱 **Mobile Responsive**: Works perfectly on all device sizes
🔒 **Security Measures**: Safe website rendering with CSP headers
⚡ **Real-time Chat**: Live chat with your AAF agents
🎯 **Multiple Positions**: Chat widget positioning options

## Base URL
```
/api/demo/
```

---

## Endpoints

### 1. Website Reproduction with Chat

**`POST /api/demo/website`**

Reproduce a customer's website with integrated chat UI.

**Request Body:**
```json
{
  "url": "https://example.com",
  "chat_position": "bottom-right",
  "chat_theme": "light",
  "chat_title": "Chat with us",
  "enable_branding": false,
  "custom_css": "/* Custom CSS */"
}
```

**Parameters:**
- `url` (required): Target website URL to reproduce
- `chat_position`: `bottom-right`, `bottom-left`, `top-right`, `top-left`
- `chat_theme`: `light`, `dark`, `brand`
- `chat_title`: Custom title for chat widget
- `enable_branding`: Show "Powered by AAF" footer
- `custom_css`: Additional CSS for customization

**Response:** HTML page with integrated chat widget

### 2. Simple Website Demo

**`GET /api/demo/website-simple?url={url}&chat_position={position}&chat_theme={theme}`**

Quick demo endpoint for testing.

**Query Parameters:**
- `url` (required): Website URL to reproduce
- `chat_position` (optional): Widget position (default: bottom-right)
- `chat_theme` (optional): Theme (default: light)

**Example:**
```bash
curl "http://localhost:8000/api/demo/website-simple?url=https://example.com&chat_theme=dark"
```

### 3. Chat Widget Preview

**`GET /api/demo/preview`**

Standalone chat widget preview without website integration.

**Response:** HTML page showing just the chat widget for testing

### 4. Embed Code Generator

**`GET /api/demo/embed`**

Generate JavaScript embed code for websites.

**Query Parameters:**
- `chat_title`: Chat widget title
- `chat_position`: Widget position
- `chat_theme`: Theme selection
- `enable_branding`: Show AAF branding

**Response:**
```json
{
  "embed_code": "<script>...</script>",
  "instructions": {
    "1": "Copy the embed code above",
    "2": "Paste it before the closing </body> tag",
    "3": "The chat widget will automatically appear",
    "4": "Customize configuration as needed"
  }
}
```

### 5. Test URLs

**`GET /api/demo/test-urls`**

Get suggested URLs for testing demo functionality.

**Response:**
```json
{
  "test_urls": [
    "https://example.com",
    "https://httpbin.org/html",
    "https://www.wikipedia.org",
    "https://github.com",
    "https://stackoverflow.com"
  ],
  "note": "These URLs can be used to test website reproduction"
}
```

---

## Chat Widget Configuration

### Themes

#### Light Theme
```json
{
  "chat_theme": "light",
  "primary": "#007bff",
  "background": "#ffffff",
  "text": "#333333"
}
```

#### Dark Theme
```json
{
  "chat_theme": "dark",
  "primary": "#0d6efd",
  "background": "#2d3748",
  "text": "#ffffff"
}
```

#### Brand Theme
```json
{
  "chat_theme": "brand",
  "primary": "#28a745",
  "background": "#ffffff",
  "text": "#333333"
}
```

### Positions

- **`bottom-right`**: Default position, bottom-right corner
- **`bottom-left`**: Bottom-left corner
- **`top-right`**: Top-right corner  
- **`top-left`**: Top-left corner

### Custom CSS Examples

```css
/* Custom brand colors */
.aaf-chat-toggle {
  background: #ff6b35 !important;
}

.aaf-chat-header {
  background: linear-gradient(45deg, #ff6b35, #f7931e) !important;
}

/* Custom sizing */
.aaf-chat-window {
  width: 400px !important;
  height: 600px !important;
}

/* Custom border radius */
.aaf-chat-window {
  border-radius: 20px !important;
}

.aaf-message {
  border-radius: 12px !important;
}
```

---

## Frontend Integration Examples

### React Demo Component

```jsx
import React, { useState } from 'react';

const AAFDemo = () => {
  const [demoUrl, setDemoUrl] = useState('');
  const [theme, setTheme] = useState('light');
  const [position, setPosition] = useState('bottom-right');
  const [loading, setLoading] = useState(false);

  const generateDemo = async () => {
    if (!demoUrl) return;

    setLoading(true);
    
    try {
      const response = await fetch('/api/demo/website', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: demoUrl,
          chat_theme: theme,
          chat_position: position,
          chat_title: 'Demo Chat',
          enable_branding: true
        })
      });

      if (response.ok) {
        const html = await response.text();
        
        // Open in new window
        const newWindow = window.open();
        newWindow.document.write(html);
        newWindow.document.close();
      } else {
        alert('Failed to generate demo');
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="aaf-demo-generator">
      <h2>AAF Chat Demo Generator</h2>
      
      <div className="form-group">
        <label>Website URL:</label>
        <input
          type="url"
          value={demoUrl}
          onChange={(e) => setDemoUrl(e.target.value)}
          placeholder="https://example.com"
          required
        />
      </div>

      <div className="form-group">
        <label>Theme:</label>
        <select value={theme} onChange={(e) => setTheme(e.target.value)}>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="brand">Brand</option>
        </select>
      </div>

      <div className="form-group">
        <label>Position:</label>
        <select value={position} onChange={(e) => setPosition(e.target.value)}>
          <option value="bottom-right">Bottom Right</option>
          <option value="bottom-left">Bottom Left</option>
          <option value="top-right">Top Right</option>
          <option value="top-left">Top Left</option>
        </select>
      </div>

      <button onClick={generateDemo} disabled={loading || !demoUrl}>
        {loading ? 'Generating...' : 'Generate Demo'}
      </button>

      <div className="quick-actions">
        <h3>Quick Tests:</h3>
        <button onClick={() => setDemoUrl('https://example.com')}>
          Example.com
        </button>
        <button onClick={() => setDemoUrl('https://httpbin.org/html')}>
          HTTPBin HTML
        </button>
        <button onClick={() => window.open('/api/demo/preview')}>
          Widget Preview
        </button>
      </div>
    </div>
  );
};

export default AAFDemo;
```

### Vue.js Demo Manager

```vue
<template>
  <div class="demo-manager">
    <h2>🤖 AAF Chat Demo</h2>
    
    <div class="demo-form">
      <div class="input-group">
        <label>Website URL</label>
        <input 
          v-model="demoConfig.url" 
          type="url" 
          placeholder="https://your-website.com"
          @keyup.enter="generateDemo"
        >
      </div>
      
      <div class="options-grid">
        <div class="option-group">
          <label>Theme</label>
          <select v-model="demoConfig.theme">
            <option value="light">☀️ Light</option>
            <option value="dark">🌙 Dark</option>
            <option value="brand">🎨 Brand</option>
          </select>
        </div>
        
        <div class="option-group">
          <label>Position</label>
          <select v-model="demoConfig.position">
            <option value="bottom-right">↘️ Bottom Right</option>
            <option value="bottom-left">↙️ Bottom Left</option>
            <option value="top-right">↗️ Top Right</option>
            <option value="top-left">↖️ Top Left</option>
          </select>
        </div>
        
        <div class="option-group">
          <label>Chat Title</label>
          <input v-model="demoConfig.title" placeholder="Chat with us">
        </div>
        
        <div class="option-group">
          <label>
            <input type="checkbox" v-model="demoConfig.branding">
            Show AAF Branding
          </label>
        </div>
      </div>
      
      <div class="actions">
        <button @click="generateDemo" :disabled="!demoConfig.url || loading">
          {{ loading ? '⏳ Generating...' : '🚀 Generate Demo' }}
        </button>
        <button @click="previewWidget">
          👀 Preview Widget
        </button>
        <button @click="getEmbedCode">
          📋 Get Embed Code
        </button>
      </div>
    </div>
    
    <div v-if="embedCode" class="embed-code-section">
      <h3>📋 Embed Code</h3>
      <textarea v-model="embedCode" readonly></textarea>
      <button @click="copyEmbedCode">Copy to Clipboard</button>
    </div>
    
    <div class="quick-tests">
      <h3>⚡ Quick Tests</h3>
      <div class="test-buttons">
        <button 
          v-for="url in testUrls" 
          :key="url"
          @click="quickTest(url)"
        >
          {{ getUrlDomain(url) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      demoConfig: {
        url: '',
        theme: 'light',
        position: 'bottom-right',
        title: 'Chat with us',
        branding: true
      },
      loading: false,
      embedCode: '',
      testUrls: [
        'https://example.com',
        'https://httpbin.org/html',
        'https://www.wikipedia.org',
        'https://github.com'
      ]
    };
  },
  
  methods: {
    async generateDemo() {
      if (!this.demoConfig.url) return;
      
      this.loading = true;
      
      try {
        const response = await fetch('/api/demo/website', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: this.demoConfig.url,
            chat_theme: this.demoConfig.theme,
            chat_position: this.demoConfig.position,
            chat_title: this.demoConfig.title,
            enable_branding: this.demoConfig.branding
          })
        });
        
        if (response.ok) {
          const html = await response.text();
          
          // Open demo in new window
          const demoWindow = window.open('', '_blank');
          demoWindow.document.write(html);
          demoWindow.document.close();
        } else {
          this.$toast.error('Failed to generate demo');
        }
      } catch (error) {
        this.$toast.error('Error: ' + error.message);
      } finally {
        this.loading = false;
      }
    },
    
    previewWidget() {
      window.open('/api/demo/preview', '_blank');
    },
    
    async getEmbedCode() {
      try {
        const params = new URLSearchParams({
          chat_title: this.demoConfig.title,
          chat_position: this.demoConfig.position,
          chat_theme: this.demoConfig.theme,
          enable_branding: this.demoConfig.branding
        });
        
        const response = await fetch(`/api/demo/embed?${params}`);
        const data = await response.json();
        
        this.embedCode = data.embed_code;
      } catch (error) {
        this.$toast.error('Failed to generate embed code');
      }
    },
    
    copyEmbedCode() {
      navigator.clipboard.writeText(this.embedCode);
      this.$toast.success('Embed code copied to clipboard!');
    },
    
    quickTest(url) {
      this.demoConfig.url = url;
      this.generateDemo();
    },
    
    getUrlDomain(url) {
      return new URL(url).hostname.replace('www.', '');
    }
  }
};
</script>
```

### JavaScript Integration

```html
<!DOCTYPE html>
<html>
<head>
    <title>AAF Demo Integration</title>
</head>
<body>
    <h1>AAF Chat Demo</h1>
    
    <div id="demo-controls">
        <input type="url" id="website-url" placeholder="https://example.com">
        <select id="theme-select">
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="brand">Brand</option>
        </select>
        <button onclick="generateDemo()">Generate Demo</button>
        <button onclick="previewWidget()">Preview Widget</button>
    </div>

    <script>
    async function generateDemo() {
        const url = document.getElementById('website-url').value;
        const theme = document.getElementById('theme-select').value;
        
        if (!url) {
            alert('Please enter a website URL');
            return;
        }
        
        try {
            const response = await fetch('/api/demo/website', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    chat_theme: theme,
                    chat_position: 'bottom-right',
                    chat_title: 'Demo Chat',
                    enable_branding: true
                })
            });
            
            if (response.ok) {
                const html = await response.text();
                const newWindow = window.open();
                newWindow.document.write(html);
                newWindow.document.close();
            } else {
                alert('Failed to generate demo');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }
    
    function previewWidget() {
        window.open('/api/demo/preview', '_blank');
    }
    
    // Quick test function
    function quickTest(url) {
        document.getElementById('website-url').value = url;
        generateDemo();
    }
    </script>
    
    <!-- Quick test buttons -->
    <div>
        <h3>Quick Tests:</h3>
        <button onclick="quickTest('https://example.com')">Example.com</button>
        <button onclick="quickTest('https://httpbin.org/html')">HTTPBin</button>
        <button onclick="quickTest('https://www.wikipedia.org')">Wikipedia</button>
    </div>
</body>
</html>
```

---

## Security Considerations

### Website Reproduction Safety

1. **Content Security Policy**: Automatic CSP headers added
2. **Sandbox Attributes**: Safe iframe-like behavior
3. **URL Validation**: Only HTTP/HTTPS URLs allowed
4. **Script Sanitization**: Removes problematic JavaScript
5. **Relative URL Fixing**: Prevents broken resources

### Chat Security

1. **Input Validation**: Message length limits and sanitization
2. **Rate Limiting**: Built-in request throttling
3. **Session Management**: Secure session handling
4. **CORS Protection**: Configurable CORS policies

### Best Practices

- Always test demo URLs before showing to customers
- Use HTTPS websites for better compatibility
- Monitor demo usage for abuse prevention
- Implement custom rate limiting for public demos

---

## Customization Examples

### Custom Brand Integration

```json
{
  "url": "https://your-company.com",
  "chat_position": "bottom-right",
  "chat_theme": "brand",
  "chat_title": "Your Company Support",
  "enable_branding": false,
  "custom_css": "
    .aaf-chat-toggle { 
      background: #your-brand-color !important; 
    }
    .aaf-chat-header { 
      background: linear-gradient(45deg, #color1, #color2) !important; 
    }
  "
}
```

### Mobile-Optimized Demo

```json
{
  "url": "https://mobile-site.com",
  "chat_position": "bottom-right",
  "chat_theme": "light",
  "custom_css": "
    @media (max-width: 768px) {
      .aaf-chat-window {
        width: calc(100vw - 20px) !important;
        height: 70vh !important;
        bottom: 10px !important;
        left: 10px !important;
        right: 10px !important;
      }
    }
  "
}
```

The AAF Demo API provides a complete solution for showcasing your chatbot on any website with pixel-perfect reproduction and full customization options! 🚀

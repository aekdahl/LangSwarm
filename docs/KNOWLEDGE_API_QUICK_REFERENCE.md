# Knowledge Management API - Quick Reference

## 🚀 Quick Start

```javascript
// Initialize
const instanceUrl = 'https://your-aaf-instance.run.app';
const authToken = 'your-bearer-token';

// Scrape a website
const result = await fetch(`${instanceUrl}/api/knowledge/scrape`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://example.com/page'
  })
});

const data = await result.json();
console.log(data.success ? '✅ Success' : '❌ Failed');
```

## 📋 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/knowledge/scrape` | Scrape URL and store embeddings |
| `GET` | `/api/knowledge/urls` | List all stored URLs |
| `GET` | `/api/knowledge/stats` | Get knowledge base statistics |

## 🔧 Request Examples

### Scrape Website
```javascript
POST /api/knowledge/scrape
{
  "url": "https://example.com/docs",
  "max_content_length": 8000,     // Optional
  "chunk_size": 1000,             // Optional  
  "chunk_overlap": 200            // Optional
}
```

### Response
```javascript
{
  "success": true,
  "url": "https://example.com/docs",
  "title": "Documentation",
  "chunks_processed": 5,
  "documents_stored": 5,
  "document_ids": ["abc_0", "abc_1", ...]
}
```

## ⚡ One-Liner Functions

```javascript
// Scrape URL
const scrape = (url) => fetch(`${instanceUrl}/api/knowledge/scrape`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ url })
}).then(r => r.json());

// Get stored URLs
const getUrls = () => fetch(`${instanceUrl}/api/knowledge/urls`, {
  headers: { 'Authorization': `Bearer ${authToken}` }
}).then(r => r.json());

// Get stats
const getStats = () => fetch(`${instanceUrl}/api/knowledge/stats`, {
  headers: { 'Authorization': `Bearer ${authToken}` }
}).then(r => r.json());
```

## 🎯 Common Use Cases

### 1. Scrape Multiple URLs
```javascript
const urls = [
  'https://example.com/page1',
  'https://example.com/page2', 
  'https://example.com/page3'
];

// Sequential (recommended to avoid overwhelming server)
for (const url of urls) {
  try {
    const result = await scrape(url);
    console.log(`✅ ${result.title}: ${result.chunks_processed} chunks`);
    await new Promise(r => setTimeout(r, 2000)); // 2 second delay
  } catch (error) {
    console.error(`❌ ${url}: ${error.message}`);
  }
}
```

### 2. Build Knowledge Dashboard
```javascript
async function buildDashboard() {
  const [urls, stats] = await Promise.all([getUrls(), getStats()]);
  
  document.getElementById('total-urls').textContent = stats.total_urls;
  document.getElementById('total-chunks').textContent = stats.total_chunks;
  
  const urlList = urls.map(url => `
    <div class="url-item">
      <h3>${url.title}</h3>
      <p>${url.url}</p>
      <small>${url.chunk_count} chunks • ${new Date(url.last_updated).toLocaleDateString()}</small>
    </div>
  `).join('');
  
  document.getElementById('url-list').innerHTML = urlList;
}
```

### 3. Form Integration
```javascript
document.getElementById('scrape-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const url = new FormData(e.target).get('url');
  const button = e.target.querySelector('button[type="submit"]');
  
  // Show loading
  button.textContent = 'Scraping...';
  button.disabled = true;
  
  try {
    const result = await scrape(url);
    alert(`✅ Success: ${result.title} (${result.chunks_processed} chunks)`);
    e.target.reset();
  } catch (error) {
    alert(`❌ Error: ${error.message}`);
  } finally {
    button.textContent = 'Scrape URL';
    button.disabled = false;
  }
});
```

## ⚠️ Error Handling

```javascript
async function safeRequest(fn, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries - 1) {
        // Last attempt failed
        if (error.message.includes('timeout')) {
          throw new Error('Request timed out. The website may be slow.');
        } else if (error.message.includes('404')) {
          throw new Error('URL not found. Please check the link.');
        } else if (error.message.includes('403')) {
          throw new Error('Access denied. The website blocked our request.');
        } else {
          throw new Error(`Request failed: ${error.message}`);
        }
      }
      
      // Wait before retry
      await new Promise(r => setTimeout(r, 1000 * (i + 1)));
    }
  }
}

// Usage
try {
  const result = await safeRequest(() => scrape(url));
  console.log('Success:', result);
} catch (error) {
  console.error('Final error:', error.message);
}
```

## 💡 Pro Tips

1. **Validate URLs first:**
```javascript
const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};
```

2. **Show progress for long operations:**
```javascript
const progress = document.getElementById('progress');
progress.innerHTML = 'Scraping... (this may take 30-60 seconds)';
```

3. **Handle the knowledge base being immediately available:**
```javascript
// After successful scrape, the content is immediately searchable
// Users can ask the chatbot about the scraped content right away
```

4. **Batch processing with delays:**
```javascript
// Don't spam the server - add delays between requests
const delay = (ms) => new Promise(r => setTimeout(r, ms));
await delay(2000); // 2 second delay
```

## 🔗 Integration Flow

1. **User submits URL** → Frontend validates URL
2. **Frontend calls scrape API** → Server uses Crawl4AI to scrape
3. **Content is processed** → Split into chunks, generate embeddings  
4. **Stored in BigQuery** → Available for vector search immediately
5. **Chatbot can answer questions** → About the scraped content

## 📱 UI Components

### Simple Scrape Button
```html
<form id="scrape-form">
  <input type="url" name="url" placeholder="https://example.com" required>
  <button type="submit">Scrape & Add to Knowledge Base</button>
</form>
```

### Knowledge Base Status
```html
<div class="knowledge-stats">
  <div class="stat">
    <span class="number" id="total-urls">0</span>
    <span class="label">URLs Indexed</span>
  </div>
  <div class="stat">
    <span class="number" id="total-chunks">0</span>
    <span class="label">Content Chunks</span>
  </div>
</div>
```

That's it! The Knowledge Management API is ready to integrate. The scraped content becomes immediately available to the AAF chatbot for answering user questions. 🚀

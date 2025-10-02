# Knowledge Management API - Frontend Integration Guide

## Overview

The Knowledge Management API provides endpoints for scraping websites, storing content as embeddings, and searching through the knowledge base using vector similarity. This enables semantic search capabilities for AAF chatbot instances.

## Base URL Structure

Each AAF instance has its own knowledge management endpoints:
```
https://[aaf-instance-url]/api/knowledge/
```

## Authentication

All requests require the same authentication as other AAF APIs:
```javascript
headers: {
  'Authorization': 'Bearer [your-api-token]',
  'Content-Type': 'application/json'
}
```

## API Endpoints

### 1. Scrape Website Content

**Endpoint:** `POST /api/knowledge/scrape`

**Description:** Scrapes a website URL using Crawl4AI, generates embeddings, and stores them in BigQuery for vector search.

**Request Body:**
```javascript
{
  "url": "https://example.com/page",           // Required: URL to scrape
  "max_content_length": 8000,                 // Optional: Max content length (default: 8000)
  "chunk_size": 1000,                         // Optional: Size of content chunks (default: 1000)
  "chunk_overlap": 200                        // Optional: Overlap between chunks (default: 200)
}
```

**Response (Success):**
```javascript
{
  "success": true,
  "url": "https://example.com/page",
  "title": "Example Page Title",
  "chunks_processed": 5,
  "documents_stored": 5,
  "document_ids": [
    "abc123_0", "abc123_1", "abc123_2", "abc123_3", "abc123_4"
  ]
}
```

**Response (Error):**
```javascript
{
  "success": false,
  "url": "https://example.com/page",
  "error": "Failed to scrape URL: Connection timeout"
}
```

**Frontend Implementation Example:**
```javascript
async function scrapeWebsite(instanceUrl, authToken, url, options = {}) {
  try {
    const response = await fetch(`${instanceUrl}/api/knowledge/scrape`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: url,
        max_content_length: options.maxLength || 8000,
        chunk_size: options.chunkSize || 1000,
        chunk_overlap: options.chunkOverlap || 200
      })
    });

    const result = await response.json();
    
    if (result.success) {
      console.log(`✅ Scraped ${result.chunks_processed} chunks from ${result.title}`);
      return result;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Scraping failed:', error);
    throw error;
  }
}
```

### 2. List Stored URLs

**Endpoint:** `GET /api/knowledge/urls`

**Description:** Get a list of all URLs that have been scraped and stored in the knowledge base.

**Response:**
```javascript
[
  {
    "url": "https://example.com/page1",
    "title": "Page 1 Title",
    "chunk_count": 5,
    "last_updated": "2024-01-15T10:30:00Z",
    "metadata": {
      "domain": "example.com",
      "description": "Page description",
      "scraper": "crawl4ai_mcp"
    }
  },
  {
    "url": "https://example.com/page2", 
    "title": "Page 2 Title",
    "chunk_count": 3,
    "last_updated": "2024-01-14T15:45:00Z",
    "metadata": {
      "domain": "example.com",
      "scraper": "crawl4ai_mcp"
    }
  }
]
```

**Frontend Implementation Example:**
```javascript
async function getStoredUrls(instanceUrl, authToken) {
  try {
    const response = await fetch(`${instanceUrl}/api/knowledge/urls`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const urls = await response.json();
    return urls;
  } catch (error) {
    console.error('Failed to fetch stored URLs:', error);
    throw error;
  }
}
```

### 3. Knowledge Base Statistics

**Endpoint:** `GET /api/knowledge/stats`

**Description:** Get statistics about the knowledge base.

**Response:**
```javascript
{
  "total_urls": 25,
  "total_chunks": 150,
  "urls": [
    // Same format as /urls endpoint
  ]
}
```

**Frontend Implementation Example:**
```javascript
async function getKnowledgeStats(instanceUrl, authToken) {
  try {
    const response = await fetch(`${instanceUrl}/api/knowledge/stats`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    const stats = await response.json();
    return stats;
  } catch (error) {
    console.error('Failed to fetch knowledge stats:', error);
    throw error;
  }
}
```

## Frontend Integration Patterns

### 1. Knowledge Management Dashboard

```javascript
class KnowledgeManager {
  constructor(instanceUrl, authToken) {
    this.instanceUrl = instanceUrl;
    this.authToken = authToken;
  }

  async initialize() {
    // Load existing URLs and stats
    const [urls, stats] = await Promise.all([
      this.getStoredUrls(),
      this.getStats()
    ]);
    
    this.renderDashboard(urls, stats);
  }

  async addUrl(url, options = {}) {
    // Show loading state
    this.showLoading(`Scraping ${url}...`);
    
    try {
      const result = await this.scrapeWebsite(url, options);
      this.showSuccess(`✅ Added ${result.title} (${result.chunks_processed} chunks)`);
      
      // Refresh the dashboard
      await this.initialize();
      
      return result;
    } catch (error) {
      this.showError(`❌ Failed to scrape ${url}: ${error.message}`);
      throw error;
    }
  }

  renderDashboard(urls, stats) {
    // Render URL list with metadata
    const urlList = urls.map(url => `
      <div class="url-item">
        <div class="url-title">${url.title}</div>
        <div class="url-details">
          <span class="url-link">${url.url}</span>
          <span class="chunk-count">${url.chunk_count} chunks</span>
          <span class="last-updated">${this.formatDate(url.last_updated)}</span>
        </div>
      </div>
    `).join('');

    // Update DOM
    document.getElementById('url-list').innerHTML = urlList;
    document.getElementById('total-urls').textContent = stats.total_urls;
    document.getElementById('total-chunks').textContent = stats.total_chunks;
  }

  // ... helper methods
}
```

### 2. URL Scraping Form

```javascript
class ScrapeForm {
  constructor(knowledgeManager) {
    this.km = knowledgeManager;
    this.setupEventListeners();
  }

  setupEventListeners() {
    document.getElementById('scrape-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(e.target);
      const url = formData.get('url');
      const maxLength = parseInt(formData.get('maxLength')) || 8000;
      const chunkSize = parseInt(formData.get('chunkSize')) || 1000;
      const chunkOverlap = parseInt(formData.get('chunkOverlap')) || 200;

      try {
        await this.km.addUrl(url, {
          maxLength,
          chunkSize, 
          chunkOverlap
        });
        
        // Reset form
        e.target.reset();
      } catch (error) {
        // Error already handled by KnowledgeManager
      }
    });
  }
}
```

### 3. Bulk URL Processing

```javascript
class BulkProcessor {
  constructor(knowledgeManager) {
    this.km = knowledgeManager;
  }

  async processSitemap(sitemapUrl, options = {}) {
    try {
      // Fetch and parse sitemap
      const urls = await this.parseSitemap(sitemapUrl);
      
      // Filter URLs if needed
      const filteredUrls = this.filterUrls(urls, options.filters);
      
      // Process in batches to avoid overwhelming the server
      const batchSize = options.batchSize || 3;
      const results = [];
      
      for (let i = 0; i < filteredUrls.length; i += batchSize) {
        const batch = filteredUrls.slice(i, i + batchSize);
        
        const batchPromises = batch.map(url => 
          this.km.addUrl(url, options.scrapeOptions)
            .catch(error => ({ url, error: error.message }))
        );
        
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);
        
        // Add delay between batches
        if (i + batchSize < filteredUrls.length) {
          await this.delay(options.delayBetweenBatches || 2000);
        }
      }
      
      return results;
    } catch (error) {
      console.error('Bulk processing failed:', error);
      throw error;
    }
  }

  async parseSitemap(sitemapUrl) {
    // Implementation to fetch and parse XML sitemap
    // Return array of URLs
  }

  filterUrls(urls, filters = {}) {
    return urls.filter(url => {
      // Apply include/exclude patterns
      if (filters.include && !filters.include.some(pattern => url.includes(pattern))) {
        return false;
      }
      if (filters.exclude && filters.exclude.some(pattern => url.includes(pattern))) {
        return false;
      }
      return true;
    });
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Error Handling

### Common Error Scenarios

1. **URL Scraping Failures:**
```javascript
// Handle different types of scraping errors
if (error.message.includes('timeout')) {
  showError('The website took too long to respond. Please try again.');
} else if (error.message.includes('not found')) {
  showError('The URL could not be found. Please check the link.');
} else if (error.message.includes('blocked')) {
  showError('The website blocked our scraper. Try a different page.');
} else {
  showError(`Scraping failed: ${error.message}`);
}
```

2. **Network Issues:**
```javascript
async function withRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      console.log(`Attempt ${i + 1} failed, retrying...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

## UI/UX Recommendations

### 1. Progress Indicators
```javascript
// Show scraping progress
function showScrapingProgress(url) {
  return {
    show: () => {
      // Show spinner and status
      document.getElementById('scraping-status').innerHTML = `
        <div class="progress-indicator">
          <div class="spinner"></div>
          <div class="status-text">Scraping ${url}...</div>
          <div class="substatus">This may take 30-60 seconds</div>
        </div>
      `;
    },
    
    update: (message) => {
      document.querySelector('.substatus').textContent = message;
    },
    
    hide: () => {
      document.getElementById('scraping-status').innerHTML = '';
    }
  };
}
```

### 2. URL Validation
```javascript
function validateUrl(url) {
  try {
    const urlObj = new URL(url);
    
    // Check if it's HTTP/HTTPS
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      return { valid: false, error: 'URL must use HTTP or HTTPS protocol' };
    }
    
    // Check for common problematic patterns
    if (url.includes('#') && !url.includes('?')) {
      return { valid: false, error: 'Fragment-only URLs may not work well' };
    }
    
    return { valid: true };
  } catch (error) {
    return { valid: false, error: 'Invalid URL format' };
  }
}
```

### 3. Results Display
```javascript
function renderUrlItem(urlData) {
  const lastUpdated = new Date(urlData.last_updated).toLocaleDateString();
  
  return `
    <div class="url-item" data-url="${urlData.url}">
      <div class="url-header">
        <h3 class="url-title">${urlData.title}</h3>
        <div class="url-actions">
          <button class="btn-secondary" onclick="reshapeUrl('${urlData.url}')">
            Re-scrape
          </button>
          <button class="btn-danger" onclick="removeUrl('${urlData.url}')">
            Remove
          </button>
        </div>
      </div>
      
      <div class="url-details">
        <div class="url-link">
          <a href="${urlData.url}" target="_blank">${urlData.url}</a>
        </div>
        
        <div class="url-metadata">
          <span class="chunk-count">
            <i class="icon-docs"></i>
            ${urlData.chunk_count} chunks
          </span>
          
          <span class="last-updated">
            <i class="icon-clock"></i>
            Updated ${lastUpdated}
          </span>
          
          ${urlData.metadata.description ? 
            `<span class="description">${urlData.metadata.description}</span>` : 
            ''
          }
        </div>
      </div>
    </div>
  `;
}
```

## Testing the Integration

### 1. Test URLs
Use these URLs for testing the scraping functionality:
- Documentation pages (usually work well)
- Blog posts with clear content structure
- FAQ pages with Q&A format

### 2. Integration Tests
```javascript
// Test basic scraping
async function testBasicScraping() {
  const testUrl = 'https://httpbin.org/html';
  
  try {
    const result = await scrapeWebsite(instanceUrl, authToken, testUrl);
    console.log('✅ Basic scraping test passed', result);
  } catch (error) {
    console.error('❌ Basic scraping test failed', error);
  }
}

// Test error handling
async function testErrorHandling() {
  const invalidUrl = 'https://this-domain-does-not-exist-12345.com';
  
  try {
    await scrapeWebsite(instanceUrl, authToken, invalidUrl);
    console.error('❌ Error handling test failed - should have thrown error');
  } catch (error) {
    console.log('✅ Error handling test passed', error.message);
  }
}
```

## Security Considerations

1. **URL Validation:** Always validate URLs on the frontend before sending to the API
2. **Rate Limiting:** Implement client-side rate limiting to avoid overwhelming the server
3. **CORS:** Ensure proper CORS configuration for cross-origin requests
4. **Authentication:** Store auth tokens securely and handle token expiration

## Support

For questions about the Knowledge Management API integration:
1. Check the API response error messages for specific guidance
2. Test with simple URLs first before trying complex sites
3. Monitor the scraping process - it typically takes 30-60 seconds per URL
4. The BigQuery vector search will be available immediately after successful scraping

The knowledge base content will automatically be available to the AAF chatbot for answering user questions once scraping is complete.

# AI-Powered Chat UI Design System

The AI Design System automatically analyzes websites and generates custom chat UI designs and personalized prompts that perfectly match the brand and target audience.

## Overview

The AI Design System consists of three main components:

1. **🔍 Website Analysis**: Extracts brand colors, typography, company info, and style
2. **🎨 UI Design Generation**: Creates custom chat themes that match the website
3. **💬 Prompt Personalization**: Generates context-aware system prompts

## Features

### 🔍 **Website Analysis**
- **Visual Elements**: Colors, fonts, layout style detection
- **Company Information**: Name, industry, business type extraction
- **Brand Personality**: Tone, target audience, communication style
- **Content Analysis**: Services, topics, language detection
- **Cultural Context**: Country and language-specific adaptations

### 🎨 **UI Design Generation**
- **Brand-Matched Colors**: Harmonious color schemes from website palette
- **Typography Matching**: Font families that complement the website
- **Style Consistency**: Design elements that feel native to the site
- **Position Optimization**: Optimal chat widget placement
- **Custom CSS**: Advanced styling that matches brand aesthetic

### 💬 **Prompt Personalization**
- **Company-Specific Knowledge**: Industry and business context
- **Brand Voice Matching**: Communication style and tone alignment
- **Multi-Language Support**: Localized prompts and responses
- **Role-Based Agents**: Specialized agent roles (support, sales, etc.)
- **Cultural Adaptation**: Region-appropriate communication patterns

---

## API Endpoints

### 1. AI-Powered Website Demo

**`POST /api/demo/website`**

Enhanced demo endpoint with AI design capabilities.

**Request Body:**
```json
{
  "url": "https://example.com",
  "use_ai_design": true,
  "use_ai_prompt": true,
  "chat_position": "auto",
  "chat_theme": "auto",
  "enable_branding": false
}
```

**New Parameters:**
- `use_ai_design`: Enable AI-powered UI design generation
- `use_ai_prompt`: Generate personalized system prompts
- `chat_position`: Use "auto" for AI-optimized positioning
- `chat_theme`: Use "auto" for AI-generated themes

### 2. Website Analysis

**`POST /api/demo/ai-analyze`**

Analyze a website and return comprehensive analysis data.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/demo/ai-analyze?url=https://example.com" \
     -H "Content-Type: application/json"
```

**Response:**
```json
{
  "analysis": {
    "company_name": "Example Corp",
    "industry": "Technology", 
    "business_type": "SaaS",
    "language": "en",
    "country": "US",
    "design_style": "modern",
    "tone": "professional",
    "target_audience": "b2b",
    "primary_colors": ["#007bff", "#17a2b8"],
    "services": ["Cloud Solutions", "Analytics"],
    "main_topics": ["technology", "innovation", "business"]
  },
  "design": {
    "primary_color": "#007bff",
    "secondary_color": "#6c757d", 
    "background_color": "#ffffff",
    "text_color": "#333333",
    "accent_color": "#17a2b8",
    "font_family": "Inter, sans-serif",
    "border_radius": "12px",
    "chat_position": "bottom-right",
    "theme_name": "example_corp_custom",
    "chat_title": "Example Corp Support",
    "welcome_message": "Hi! I'm here to help with your technology questions.",
    "placeholder_text": "Ask about our solutions..."
  },
  "prompt": {
    "system_prompt": "You are a knowledgeable customer support specialist for Example Corp, a leading technology company specializing in cloud solutions and analytics...",
    "agent_name": "Alex",
    "agent_role": "Technology Consultant", 
    "company_context": "Example Corp provides cutting-edge cloud solutions and analytics tools for businesses...",
    "language": "en"
  }
}
```

---

## Usage Examples

### React Integration

```jsx
import React, { useState } from 'react';

const AIDesignDemo = () => {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyzeWebsite = async (url) => {
    setLoading(true);
    try {
      const response = await fetch('/api/demo/ai-analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateAIDemo = async (url) => {
    const response = await fetch('/api/demo/website', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        use_ai_design: true,
        use_ai_prompt: true,
        enable_branding: true
      })
    });

    if (response.ok) {
      const html = await response.text();
      const demoWindow = window.open();
      demoWindow.document.write(html);
      demoWindow.document.close();
    }
  };

  return (
    <div className="ai-design-demo">
      <h2>🤖 AI-Powered Chat Design</h2>
      
      <div className="url-input">
        <input 
          type="url" 
          placeholder="https://example.com"
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              analyzeWebsite(e.target.value);
            }
          }}
        />
        <button onClick={() => generateAIDemo(url)} disabled={loading}>
          {loading ? '🧠 Analyzing...' : '🚀 Generate AI Demo'}
        </button>
      </div>

      {analysisData && (
        <div className="analysis-results">
          <div className="company-info">
            <h3>📊 Company Analysis</h3>
            <p><strong>Company:</strong> {analysisData.analysis.company_name}</p>
            <p><strong>Industry:</strong> {analysisData.analysis.industry}</p>
            <p><strong>Style:</strong> {analysisData.analysis.design_style}</p>
            <p><strong>Tone:</strong> {analysisData.analysis.tone}</p>
            <p><strong>Language:</strong> {analysisData.analysis.language}</p>
          </div>

          <div className="design-preview">
            <h3>🎨 Generated Design</h3>
            <div className="color-palette">
              <div 
                className="color-swatch"
                style={{ backgroundColor: analysisData.design.primary_color }}
                title="Primary Color"
              />
              <div 
                className="color-swatch"
                style={{ backgroundColor: analysisData.design.secondary_color }}
                title="Secondary Color"
              />
              <div 
                className="color-swatch"
                style={{ backgroundColor: analysisData.design.accent_color }}
                title="Accent Color"
              />
            </div>
            <p><strong>Font:</strong> {analysisData.design.font_family}</p>
            <p><strong>Title:</strong> {analysisData.design.chat_title}</p>
            <p><strong>Position:</strong> {analysisData.design.chat_position}</p>
          </div>

          <div className="prompt-preview">
            <h3>💬 Generated Prompt</h3>
            <p><strong>Agent:</strong> {analysisData.prompt.agent_name}</p>
            <p><strong>Role:</strong> {analysisData.prompt.agent_role}</p>
            <div className="prompt-text">
              <strong>System Prompt:</strong>
              <textarea 
                value={analysisData.prompt.system_prompt}
                readOnly
                rows={6}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIDesignDemo;
```

### Vue.js Implementation

```vue
<template>
  <div class="ai-design-interface">
    <h2>🧠 AI Chat Designer</h2>
    
    <div class="input-section">
      <input 
        v-model="websiteUrl"
        type="url" 
        placeholder="Enter website URL"
        @keyup.enter="analyzeWebsite"
      >
      <div class="action-buttons">
        <button @click="analyzeWebsite" :disabled="loading">
          {{ loading ? '🔍 Analyzing...' : '🔍 Analyze Website' }}
        </button>
        <button @click="generateDemo" :disabled="!websiteUrl || loading">
          🚀 Generate AI Demo
        </button>
      </div>
    </div>

    <div v-if="analysis" class="results-grid">
      <!-- Company Information -->
      <div class="analysis-card">
        <h3>🏢 Company Profile</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>Company:</label>
            <span>{{ analysis.analysis.company_name }}</span>
          </div>
          <div class="info-item">
            <label>Industry:</label>
            <span>{{ analysis.analysis.industry }}</span>
          </div>
          <div class="info-item">
            <label>Business Type:</label>
            <span>{{ analysis.analysis.business_type }}</span>
          </div>
          <div class="info-item">
            <label>Language:</label>
            <span>{{ analysis.analysis.language }}</span>
          </div>
          <div class="info-item">
            <label>Style:</label>
            <span>{{ analysis.analysis.design_style }}</span>
          </div>
          <div class="info-item">
            <label>Tone:</label>
            <span>{{ analysis.analysis.tone }}</span>
          </div>
        </div>
      </div>

      <!-- Design Preview -->
      <div class="design-card">
        <h3>🎨 AI-Generated Design</h3>
        <div class="design-preview">
          <div class="color-section">
            <h4>Color Palette</h4>
            <div class="color-palette">
              <div 
                v-for="(color, name) in designColors" 
                :key="name"
                class="color-item"
              >
                <div 
                  class="color-swatch" 
                  :style="{ backgroundColor: color }"
                ></div>
                <span>{{ name }}</span>
              </div>
            </div>
          </div>
          
          <div class="typography-section">
            <h4>Typography</h4>
            <p :style="{ fontFamily: analysis.design.font_family }">
              {{ analysis.design.font_family }}
            </p>
          </div>
          
          <div class="widget-preview">
            <h4>Widget Preview</h4>
            <div class="mini-widget" :style="widgetStyle">
              <div class="mini-header">{{ analysis.design.chat_title }}</div>
              <div class="mini-message">{{ analysis.design.welcome_message }}</div>
              <div class="mini-input">{{ analysis.design.placeholder_text }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Prompt Configuration -->
      <div class="prompt-card">
        <h3>💬 AI Agent Configuration</h3>
        <div class="agent-info">
          <div class="agent-profile">
            <h4>{{ analysis.prompt.agent_name }}</h4>
            <p class="agent-role">{{ analysis.prompt.agent_role }}</p>
          </div>
          
          <div class="company-context">
            <h4>Company Context</h4>
            <p>{{ analysis.prompt.company_context }}</p>
          </div>
          
          <div class="system-prompt">
            <h4>System Prompt</h4>
            <textarea 
              v-model="analysis.prompt.system_prompt"
              readonly
              rows="8"
            ></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Services & Topics -->
    <div v-if="analysis" class="additional-info">
      <div class="services-section">
        <h3>🛠️ Detected Services</h3>
        <div class="tag-list">
          <span 
            v-for="service in analysis.analysis.services" 
            :key="service"
            class="tag"
          >
            {{ service }}
          </span>
        </div>
      </div>
      
      <div class="topics-section">
        <h3>📋 Main Topics</h3>
        <div class="tag-list">
          <span 
            v-for="topic in analysis.analysis.main_topics" 
            :key="topic"
            class="tag topic-tag"
          >
            {{ topic }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      websiteUrl: '',
      analysis: null,
      loading: false
    };
  },
  
  computed: {
    designColors() {
      if (!this.analysis) return {};
      
      return {
        'Primary': this.analysis.design.primary_color,
        'Secondary': this.analysis.design.secondary_color,
        'Background': this.analysis.design.background_color,
        'Text': this.analysis.design.text_color,
        'Accent': this.analysis.design.accent_color
      };
    },
    
    widgetStyle() {
      if (!this.analysis) return {};
      
      return {
        fontFamily: this.analysis.design.font_family,
        borderRadius: this.analysis.design.border_radius,
        backgroundColor: this.analysis.design.background_color,
        color: this.analysis.design.text_color,
        border: `2px solid ${this.analysis.design.primary_color}`
      };
    }
  },
  
  methods: {
    async analyzeWebsite() {
      if (!this.websiteUrl) return;
      
      this.loading = true;
      try {
        const response = await fetch('/api/demo/ai-analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: this.websiteUrl })
        });
        
        this.analysis = await response.json();
      } catch (error) {
        this.$toast.error('Analysis failed: ' + error.message);
      } finally {
        this.loading = false;
      }
    },
    
    async generateDemo() {
      if (!this.websiteUrl) return;
      
      try {
        const response = await fetch('/api/demo/website', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: this.websiteUrl,
            use_ai_design: true,
            use_ai_prompt: true,
            enable_branding: true
          })
        });
        
        if (response.ok) {
          const html = await response.text();
          const demoWindow = window.open();
          demoWindow.document.write(html);
          demoWindow.document.close();
        }
      } catch (error) {
        this.$toast.error('Demo generation failed: ' + error.message);
      }
    }
  }
};
</script>

<style scoped>
.ai-design-interface {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.analysis-card, .design-card, .prompt-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.color-palette {
  display: flex;
  gap: 10px;
  margin: 10px 0;
}

.color-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.color-swatch {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 2px solid #eee;
}

.mini-widget {
  max-width: 200px;
  padding: 10px;
  border-radius: 8px;
  margin: 10px 0;
}

.mini-header {
  font-weight: bold;
  margin-bottom: 8px;
  padding: 8px;
  background: rgba(0,0,0,0.1);
  border-radius: 4px;
}

.mini-message, .mini-input {
  padding: 6px;
  margin: 4px 0;
  background: rgba(0,0,0,0.05);
  border-radius: 4px;
  font-size: 12px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.topic-tag {
  background: #d1ecf1;
}
</style>
```

---

## AI Analysis Process

### 1. **Website Content Extraction**
```
URL Input → HTML Fetch → Content Parse → Visual Analysis
```

- Fetches website HTML content
- Extracts meta information (title, description)
- Analyzes CSS and inline styles
- Identifies structural elements

### 2. **AI-Powered Analysis**
```
Content → GPT-4 Analysis → Structured Data → Design Generation
```

- **Company Identification**: Name, industry, business type
- **Visual Style Analysis**: Colors, fonts, layout patterns  
- **Brand Personality**: Tone, target audience, communication style
- **Content Understanding**: Services, topics, cultural context

### 3. **Design Generation**
```
Analysis → Design Rules → Custom CSS → Widget Configuration
```

- **Color Harmony**: Extracts and harmonizes brand colors
- **Typography Matching**: Selects complementary fonts
- **Layout Optimization**: Determines best positioning
- **Style Consistency**: Ensures brand alignment

### 4. **Prompt Personalization**
```
Company Data → Context Building → Prompt Engineering → Agent Configuration
```

- **Industry Knowledge**: Incorporates sector-specific context
- **Brand Voice**: Matches communication style and tone
- **Localization**: Adapts for language and culture
- **Role Definition**: Creates appropriate agent personas

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Required for AI features
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional AI configuration
AI_DESIGN_ENABLED=true
AI_ANALYSIS_TIMEOUT=30
AI_DESIGN_CACHE_TTL=3600
```

### LangSwarm Configuration

Update `config/langswarm.yaml`:

```yaml
# AI Design System
ai_design:
  enabled: true
  openai_model: "gpt-4"
  analysis_timeout: 30
  cache_results: true
  cache_ttl: 3600
  
  # Fallback configuration
  fallback_theme: "light"
  fallback_language: "en"
  
  # Design constraints
  max_colors: 5
  supported_fonts: ["Arial", "Helvetica", "Inter", "Roboto"]
  
agents:
  - id: "ai_design_analyzer"
    model: "gpt-4"
    system_prompt: "You are an expert web designer and brand analyst..."
    
  - id: "ai_prompt_generator" 
    model: "gpt-4"
    system_prompt: "You are an expert AI prompt engineer..."
```

---

## Best Practices

### 🎯 **Effective Usage**

1. **Website Selection**: Works best with well-designed, brand-consistent websites
2. **Color Accuracy**: Ensure websites have clear brand colors (not just black/white)
3. **Content Quality**: Rich content leads to better company analysis
4. **Language Support**: Currently optimized for English, with expanding language support

### 🔧 **Customization**

1. **Override AI Suggestions**: All AI-generated designs can be manually overridden
2. **Hybrid Approach**: Combine AI insights with manual customizations
3. **A/B Testing**: Generate multiple AI variants for testing
4. **Brand Guidelines**: AI respects existing brand consistency

### 🚀 **Performance**

1. **Analysis Caching**: Results cached for 1 hour by default
2. **Async Processing**: Non-blocking AI analysis
3. **Graceful Fallbacks**: Always provides working design if AI fails
4. **Rate Limiting**: Built-in OpenAI API rate limiting

### 🔒 **Security & Privacy**

1. **Content Limits**: Only analyzes first 10KB of website content
2. **No Storage**: Website content not permanently stored
3. **API Keys**: Secure OpenAI API key management
4. **Rate Limiting**: Prevents API abuse

The AI Design System transforms generic chat widgets into brand-native interfaces that feel custom-built for each website, dramatically improving user engagement and brand consistency! 🎨🤖

# 🏗️ Your First LangSwarm Project

**Build a complete multi-agent AI system step-by-step.**

In this tutorial, you'll build a **Document Analysis System** that can read files, extract insights, and generate summaries using multiple AI agents working together.

## 🎯 **What You'll Build**

A document analysis system with:
- 📄 **Document Reader Agent** - Reads and parses files
- 🔍 **Analysis Agent** - Extracts key insights and data
- 📝 **Summary Agent** - Creates comprehensive summaries
- 🔄 **Workflow Orchestration** - Coordinates all agents

## 🚀 **Step 1: Project Setup**

### **Create Project Directory**
```bash
mkdir my-langswarm-project
cd my-langswarm-project
```

### **Install LangSwarm**
```bash
pip install langswarm
```

### **Set API Key**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## 📝 **Step 2: Create Configuration**

Create `langswarm.yaml`:
```yaml
version: "2.0"
name: "Document Analysis System"
description: "Multi-agent document analysis and summarization"

# Define our three agents
agents:
  - id: "document_reader"
    name: "Document Reader"
    provider: "openai"
    model: "gpt-4o"
    system_prompt: |
      You are a document reader specialist. Your job is to:
      1. Read and parse document content
      2. Identify document structure and format
      3. Extract raw text content cleanly
      4. Preserve important formatting and structure

  - id: "analyzer"
    name: "Content Analyzer" 
    provider: "openai"
    model: "gpt-4o"
    system_prompt: |
      You are a content analysis expert. Your job is to:
      1. Analyze document content for key themes and topics
      2. Extract important facts, figures, and data points
      3. Identify main arguments and conclusions
      4. Note any actionable items or recommendations

  - id: "summarizer"
    name: "Summary Generator"
    provider: "openai"
    model: "gpt-4o"
    system_prompt: |
      You are a summary specialist. Your job is to:
      1. Create clear, concise summaries
      2. Highlight the most important points
      3. Structure information logically
      4. Make content accessible to any audience

# Define tools for file operations
tools:
  filesystem:
    type: "mcp"
    local_mode: true
    description: "Read and write files"

# Define the analysis workflow
workflows:
  - id: "document_analysis"
    name: "Document Analysis Pipeline"
    description: "Complete document analysis from reading to summary"
    steps:
      - id: "read_step"
        agent: "document_reader"
        tools: ["filesystem"]
        description: "Read and parse the document"
        
      - id: "analyze_step"
        agent: "analyzer"
        input: "${read_step.output}"
        description: "Analyze content for insights"
        
      - id: "summarize_step"
        agent: "summarizer"
        input: "${analyze_step.output}"
        description: "Generate final summary"
        output: 
          to: "user"

# Memory configuration for persistent conversations
memory:
  backend: "sqlite"
  settings:
    persist_directory: "./data"

# Observability for debugging
observability:
  logging:
    level: "INFO"
  tracing:
    enabled: true
```

## 🤖 **Step 3: Create the Main Script**

Create `analyze_document.py`:
```python
#!/usr/bin/env python3
"""
Document Analysis System
A complete LangSwarm V2 example showing multi-agent workflows.
"""

import asyncio
import sys
from pathlib import Path
from langswarm.core.config import load_config
from langswarm.core.workflows import get_workflow_engine
from langswarm.core.agents import AgentBuilder

async def main():
    """Main function to run document analysis."""
    
    # Check if document path provided
    if len(sys.argv) < 2:
        print("Usage: python analyze_document.py <path_to_document>")
        print("Example: python analyze_document.py ./sample_document.txt")
        return
    
    document_path = sys.argv[1]
    
    # Verify document exists
    if not Path(document_path).exists():
        print(f"❌ Document not found: {document_path}")
        return
    
    print(f"🚀 Starting document analysis for: {document_path}")
    print("=" * 60)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = load_config("langswarm.yaml")
        print(f"✅ Loaded {len(config.agents)} agents and {len(config.workflows)} workflows")
        
        # Get workflow engine
        print("🔧 Initializing workflow engine...")
        engine = get_workflow_engine()
        
        # Execute the document analysis workflow
        print("🔄 Running document analysis workflow...")
        result = await engine.execute_workflow(
            workflow_id="document_analysis",
            input_data={
                "document_path": document_path,
                "user_request": f"Please analyze the document at {document_path}"
            }
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 ANALYSIS RESULTS")
        print("=" * 60)
        print(result.output)
        print("\n" + "=" * 60)
        print(f"✅ Analysis completed successfully!")
        print(f"📈 Workflow executed in {result.execution_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📄 **Step 4: Create Sample Document**

Create `sample_document.txt`:
```text
# Quarterly Business Report - Q3 2024

## Executive Summary
Our company achieved record-breaking performance in Q3 2024, with revenue increasing by 35% compared to the same period last year. Key highlights include successful product launches, expanded market presence, and improved operational efficiency.

## Financial Performance
- Total Revenue: $2.4 million (35% increase YoY)
- Net Profit: $480,000 (20% profit margin)
- Operating Expenses: $1.92 million
- Customer Acquisition Cost: $150 (down from $200)

## Key Achievements
1. **Product Launch**: Successfully launched our new AI-powered analytics platform
2. **Market Expansion**: Entered 3 new geographic markets
3. **Team Growth**: Hired 15 new employees across engineering and sales
4. **Customer Satisfaction**: Achieved 94% customer satisfaction score

## Challenges and Opportunities
### Challenges
- Supply chain disruptions affected delivery times
- Increased competition in the AI analytics space
- Higher than expected customer support volume

### Opportunities
- Growing demand for AI solutions in enterprise market
- Potential partnerships with major cloud providers
- Expansion into international markets showing strong interest

## Action Items for Q4
1. Optimize supply chain processes to reduce delivery times
2. Invest in additional customer support resources
3. Develop competitive analysis and pricing strategy
4. Explore partnership opportunities with cloud providers
5. Begin planning for international expansion

## Conclusion
Q3 2024 was a strong quarter that positions us well for continued growth. While we face some operational challenges, the market opportunities and our product-market fit give us confidence in our trajectory.
```

## 🚀 **Step 5: Run Your First Analysis**

```bash
python analyze_document.py sample_document.txt
```

Expected output:
```
🚀 Starting document analysis for: sample_document.txt
============================================================
📋 Loading configuration...
✅ Loaded 3 agents and 1 workflows
🔧 Initializing workflow engine...
🔄 Running document analysis workflow...

============================================================
📊 ANALYSIS RESULTS
============================================================
## Document Analysis Summary

**Document Type**: Quarterly Business Report (Q3 2024)

**Key Financial Metrics**:
- Revenue: $2.4M (35% YoY growth)
- Net Profit: $480K (20% margin)
- Customer Acquisition Cost: $150 (improved from $200)

**Major Achievements**:
1. AI-powered analytics platform launch
2. Geographic expansion (3 new markets)
3. Team scaling (15 new hires)
4. High customer satisfaction (94%)

**Critical Action Items**:
- Supply chain optimization needed
- Customer support scaling required
- Competitive analysis for AI market
- International expansion planning

**Overall Assessment**: Strong performance quarter with clear growth trajectory, though operational scaling challenges need attention.

============================================================
✅ Analysis completed successfully!
📈 Workflow executed in 12.34 seconds
```

## 🎯 **Step 6: Extend Your Project**

### **Add More Document Types**
```python
# Add support for different file types
def detect_document_type(file_path):
    """Detect document type and adjust analysis approach."""
    extension = Path(file_path).suffix.lower()
    
    if extension == '.pdf':
        return 'pdf_document'
    elif extension in ['.md', '.txt']:
        return 'text_document'
    elif extension in ['.docx', '.doc']:
        return 'word_document'
    else:
        return 'unknown_document'
```

### **Add Memory and Context**
```yaml
# Add to langswarm.yaml
memory:
  backend: "sqlite"
  settings:
    persist_directory: "./analysis_history"
    enable_semantic_search: true
```

### **Add More Specialized Agents**
```yaml
# Add to agents section in langswarm.yaml
- id: "fact_checker"
  name: "Fact Checker"
  provider: "openai"
  model: "gpt-4o"
  system_prompt: |
    You verify facts and claims in documents.
    Cross-reference information and flag potential inaccuracies.

- id: "action_extractor"
  name: "Action Item Extractor"
  provider: "openai"
  model: "gpt-4o"
  system_prompt: |
    You identify and extract actionable items from documents.
    Create clear, prioritized task lists with deadlines when mentioned.
```

## 🏆 **What You've Accomplished**

Congratulations! You've built a complete multi-agent AI system that:

- ✅ **Uses Multiple AI Agents** working together
- ✅ **Processes Real Documents** with structured analysis
- ✅ **Implements Workflows** for complex task orchestration
- ✅ **Handles Configuration** through YAML files
- ✅ **Provides Structured Output** with clear results
- ✅ **Includes Error Handling** and user feedback
- ✅ **Supports Extension** for additional features

## 🔥 **Next Steps**

### **Learn More Advanced Features**
- **[Workflow Guide](../../user-guides/workflows/README.md)** - Advanced workflow patterns
- **[Memory Systems](../../user-guides/memory/README.md)** - Persistent agent memory
- **[Tool Development](../../user-guides/tools/README.md)** - Create custom tools
- **[Multi-Modal Agents](../../user-guides/agents/README.md)** - Handle images, audio, video

### **Deploy Your System**
- **[Local Deployment](../../deployment/local/README.md)** - Run locally with Docker
- **[Cloud Deployment](../../deployment/cloud/README.md)** - Deploy to AWS, GCP, Azure
- **[Scaling Guide](../../deployment/scaling/README.md)** - Handle production workloads

### **Join the Community**
- **[Contributing](../../community/contributing/README.md)** - Contribute to LangSwarm
- **[Examples](../../examples/README.md)** - More project examples
- **[Support](../../community/support/README.md)** - Get help and share projects

---

**🎉 You've successfully built your first LangSwarm project! Ready to build more advanced AI systems?**

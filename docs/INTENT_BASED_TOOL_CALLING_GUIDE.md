# 🎯 Intent-Based Tool Calling - Recommended Approach

**Avoid parameter mapping issues by using natural language intents instead of exact parameters.**

---

## 🤔 **The Problem with Direct Parameters**

Agents often struggle with exact parameter names and can use incorrect parameters:

```json
❌ PROBLEMATIC - Direct Parameters:
{
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search", 
    "params": {"keyword": "refund policy"}  // Wrong parameter name!
  }
}
```

**Common Issues:**
- Using `keyword` instead of `query`
- Using `search` instead of `query` 
- Using `text` instead of `query`
- Parameter schema mismatches

## ✅ **The Solution: Intent-Based Calling**

Express what you want to accomplish, not how to do it:

```json
✅ RECOMMENDED - Intent-Based:
{
  "response": "I'll search our knowledge base for refund policy information.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "search for refund policy information",
    "context": "user asking about refund procedures for enterprise customers"
  }
}
```

---

## 🎯 **Intent-Based Examples**

### **Knowledge Base Search**
```json
{
  "response": "Let me search for that information in our knowledge base.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "find information about pricing for restaurants",
    "context": "user wants to know restaurant-specific pricing tiers and features"
  }
}
```

### **Document Retrieval**
```json
{
  "response": "I'll retrieve the full document for you.",
  "mcp": {
    "tool": "bigquery_vector_search", 
    "intent": "get complete document content",
    "context": "user needs full content for document ID from previous search results"
  }
}
```

### **Dataset Exploration**
```json
{
  "response": "Let me check what datasets are available.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "list available knowledge bases",
    "context": "user wants to explore what information sources are accessible"
  }
}
```

---

## 🔧 **How Intent-Based Works**

### **1. Agent Expresses Intent**
- Natural language description of what's needed
- Context about why it's needed
- No parameter mapping required

### **2. Tool Workflow Processes Intent**
- **Interprets** the natural language intent
- **Extracts** required parameters automatically
- **Asks for clarification** if anything is unclear

### **3. Automatic Parameter Mapping**
The tool workflow handles parameter extraction:
```
Intent: "search for refund policy information"
Context: "user asking about refund procedures"
↓
Automatically mapped to:
{
  "method": "similarity_search",
  "params": {
    "query": "refund policy procedures",
    "limit": 10,
    "similarity_threshold": 0.7
  }
}
```

---

## 📋 **Best Practices**

### **✅ Good Intent Descriptions**
- **Specific**: "search for pricing information for restaurants"
- **Action-oriented**: "find documents about", "retrieve content for", "list available"
- **Contextual**: Include why the information is needed

### **✅ Good Context Information**
- **User's goal**: "user wants to understand pricing options"
- **Previous results**: "following up on search results from earlier query"
- **Specific needs**: "needs technical documentation for troubleshooting"

### **❌ Avoid Vague Intents**
- **Too generic**: "search for something"
- **No context**: Missing why the information is needed
- **Too technical**: Don't try to specify exact parameters

---

## 🎉 **Benefits Summary**

| **Aspect** | **Direct Parameters** | **Intent-Based** |
|------------|----------------------|------------------|
| **Parameter Issues** | ❌ Common mapping errors | ✅ No parameter knowledge needed |
| **Maintainability** | ❌ Breaks with schema changes | ✅ Robust to tool updates |
| **Agent Complexity** | ❌ Must know exact schemas | ✅ Natural language only |
| **Error Recovery** | ❌ Hard failures | ✅ Automatic clarification |
| **User Experience** | ❌ Cryptic parameter errors | ✅ Natural conversation |

---

## 🚀 **Implementation**

### **Update Your Agent Instructions**
Instead of teaching agents parameter schemas, teach them to express intents:

```yaml
agents:
  - id: "knowledge_assistant"
    system_prompt: |
      When users ask questions, use intent-based tool calling:
      
      For knowledge searches, express your intent naturally:
      {
        "mcp": {
          "tool": "bigquery_vector_search",
          "intent": "search for [what user needs]",
          "context": "[why they need it]"
        }
      }
      
      Do NOT worry about exact parameter names or schemas.
      Let the tool workflow handle the technical details.
```

### **Migrate Existing Configurations**
Replace parameter-based examples with intent-based ones in your documentation and training.

---

## 📚 **Related Documentation**

- [System Prompt Template](langswarm/core/templates/system_prompt_template.md) - Intent examples
- [Cross-Workflow Clarification](langswarm/core/templates/fragments/cross_workflow_clarification.md) - Clarification handling
- [Workflows vs Direct Agents](docs/WORKFLOWS_VS_DIRECT_AGENTS_COMPARISON.md) - When to use each approach

---

**🎯 Use intent-based calling to eliminate parameter mapping issues and create more robust, maintainable agent systems!**

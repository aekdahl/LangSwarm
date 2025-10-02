# 🚨 Fix: "Agent 'main_workflow' not found" Error

## Root Cause
This error occurs when `main_workflow` is incorrectly structured in your YAML configuration. The system is treating `"main_workflow"` as a **workflow syntax string** instead of recognizing it as a **workflow identifier**.

## ❌ Incorrect YAML Structure (Causes the Error)

```yaml
# WRONG: main_workflow as a list item
workflows:
  - main_workflow  # ← This is treated as a string/agent name!
  - other_workflow

# OR WRONG: main_workflow as a simple string
workflows:
  main_workflow: "assistant -> user"  # ← This becomes simple syntax
```

## ✅ Correct YAML Structure

```yaml
# CORRECT: main_workflow as a key pointing to workflow definitions
workflows:
  main_workflow:
    - id: your_actual_workflow_name
      description: "Your workflow description"
      steps:
        - id: step1
          agent: your_agent
          input: "${context.user_input}"
          output:
            to: user
```

## 🔍 How to Identify the Issue

**If you see this error:**
```
⚠️ Agent 'main_workflow' not found, using 'aaf_chatbot' instead
```

**It means your YAML has:**
- `workflows` as a list containing `"main_workflow"` as a string
- OR `main_workflow` set to a simple string value

## 🛠️ Quick Fix Examples

### Fix 1: Convert List to Dict Structure
```yaml
# BEFORE (causing error):
workflows:
  - main_workflow

# AFTER (fixed):
workflows:
  main_workflow:
    - id: main_chat_workflow
      steps:
        - id: chat_step
          agent: aaf_chatbot
          input: "${context.user_input}"
          output:
            to: user
```

### Fix 2: Convert Simple String to Proper Structure
```yaml
# BEFORE (causing error):
workflows:
  main_workflow: "aaf_chatbot -> user"

# AFTER (fixed):
workflows:
  main_workflow:
    - id: chat_workflow
      simple: "aaf_chatbot -> user"  # Use 'simple' field for simple syntax
```

## 🧪 Test Your Fix

Run the diagnostic script to verify:
```bash
python3 diagnose_langswarm_issues.py
```

You should see:
```
✅ main_workflow structure looks correct (ID: your_workflow_id)
```

Instead of:
```
🚨 CRITICAL: 'main_workflow' found as list item!
```

## 📋 Complete Example

Here's a complete, correct YAML structure:

```yaml
version: "1.0"
project_name: "my-langswarm-app"

agents:
  - id: aaf_chatbot
    agent_type: openai
    model: gpt-4o
    system_prompt: "You are a helpful assistant"
    tools: ["bigquery_vector_search"]

tools:
  bigquery_vector_search:
    type: mcpbigquery_vector_search
    config:
      project_id: "${GOOGLE_CLOUD_PROJECT}"
      dataset_id: "vector_search"

workflows:
  main_workflow:  # ← KEY, not list item
    - id: search_and_respond  # ← Actual workflow ID
      description: "Search knowledge base and respond"
      steps:
        - id: process_query
          agent: aaf_chatbot
          input: "${context.user_input}"
          output:
            to: user
```

## 🎯 Summary

The error `"Agent 'main_workflow' not found"` is **NOT expected behavior** - it indicates a **malformed YAML configuration**. Fix your YAML structure and the error will disappear.

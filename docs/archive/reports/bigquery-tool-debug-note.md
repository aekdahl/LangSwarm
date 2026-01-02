# Separate Debug Trace Files - Case 3 BigQuery

## ✅ **What's Been Implemented:**

### **🎯 Configurable Test Scenarios:**
- **Configuration file**: `langswarm/core/debug/scenarios/bigquery_scenarios.yaml`
- **Scenarios**: Each scenario has name, description, query, expected behavior, and trace file suffix
- **Enable/disable**: Individual scenarios can be enabled/disabled in config
- **Success criteria**: Configurable evaluation criteria for each scenario type

### **📁 Separate Trace Files Design:**
Each scenario creates its own focused trace file:
- `debug_traces/case_3_bigquery_similarity_search.jsonl`
- `debug_traces/case_3_bigquery_list_datasets.jsonl` 
- `debug_traces/case_3_bigquery_error_handling.jsonl`
- `debug_traces/case_3_bigquery_tool.jsonl` (setup and coordination)

### **🔧 Configuration Structure:**
```yaml
scenarios:
  similarity_search:
    name: "similarity_search"
    description: "Real vector similarity search test"
    query: "Search for information about refund policies"
    expected_behavior: "Should generate embeddings and perform vector similarity search in BigQuery"
    trace_file_suffix: "similarity_search"
    enabled: true

config:
  scenario_timeout: 30
  continue_on_failure: true
  separate_trace_files: true
  
  success_criteria:
    similarity_search:
      min_response_length: 10
      required_keywords: ["search", "refund", "policy"]
```

### **💻 Current Output:**
The implementation shows each scenario clearly:
```
🧪 Running BigQuery scenario: similarity_search
📝 Description: Real vector similarity search test
❓ Query: 'Search for information about refund policies'
📁 Trace file: debug_traces/case_3_bigquery_similarity_search.jsonl
✅ Scenario result: Success
📤 Response: 'I'll search for that information about refund policies.'
```

### **📊 Summary:**
```
📊 BigQuery Tool Debug Summary:
   • Total scenarios: 3
   • Successful: 2
   • Failed: 1
   • Individual traces: 3 files created
```

## ✅ **Benefits Achieved:**
1. **Clear scenario separation** - Each test is clearly identified and isolated
2. **Configurable scenarios** - Easy to add/remove/modify test scenarios
3. **Detailed reporting** - Each scenario shows its purpose and expected behavior
4. **Flexible evaluation** - Success criteria configurable per scenario type
5. **Better debugging** - Can focus on specific scenarios individually

## 🎯 **Working Implementation:**
Each scenario now creates its own detailed trace file for independent analysis. No summary file needed - the individual traces contain all necessary information.

This represents a major improvement in debug case organization and makes it much easier to:
- Debug specific BigQuery operations
- Add new test scenarios
- Configure success criteria
- Analyze individual failure modes
- Understand complex multi-step workflows

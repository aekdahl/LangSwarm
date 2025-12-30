# LangSwarm V2 YAML Compatibility Guide

**Complete guide for using existing YAML workflows with LangSwarm V2**

## 🎯 Overview

LangSwarm V2 provides 100% backward compatibility with existing YAML workflows through a comprehensive compatibility layer. You can continue using your existing YAML configurations while gradually migrating to the modern fluent builder API.

**Key Benefits:**
- **Zero Migration Friction**: Existing workflows work unchanged
- **Automatic Template Conversion**: Legacy syntax automatically modernized
- **Multiple Format Support**: Simple, complex, and legacy YAML formats
- **Seamless Integration**: YAML workflows integrate with V2 monitoring and middleware

---

## 🚀 Quick Start

### **Load Existing YAML Workflows**

```python
from langswarm.core.workflows import load_yaml_workflows, execute_workflow

# Load workflows from YAML file
workflows = await load_yaml_workflows("existing_workflows.yaml")
print(f"Loaded {len(workflows)} workflows")

# Execute YAML-loaded workflow
result = await execute_workflow("my_yaml_workflow", {"input": "data"})
print(f"Result: {result.final_result}")
```

### **Migrate YAML Directory**

```python
from langswarm.core.workflows import migrate_yaml_workflows

# Migrate all YAML files in directory
migration_result = await migrate_yaml_workflows(
    source_dir="./legacy_workflows/",
    target_format="v2_builder"  # or "v2_yaml" for updated YAML
)

print(f"Migrated {migration_result.success_count} workflows")
for error in migration_result.errors:
    print(f"Error: {error.file} - {error.message}")
```

---

## 📝 Supported YAML Formats

### **1. Simple Syntax**

The simplest format using arrow notation:

```yaml
# simple_workflow.yaml
workflows:
  data_processing: "data_extractor -> data_analyzer -> report_generator"
  
  content_review: "content_processor -> quality_checker -> reviewer -> approver"
  
  analysis_pipeline: "text_extractor -> sentiment_analyzer -> topic_extractor -> summarizer"
```

**V2 Usage:**
```python
# Load and execute simple syntax
workflows = await load_yaml_workflows("simple_workflow.yaml")
result = await execute_workflow("data_processing", {"input": "sample data"})
```

### **2. List Format**

Array-based workflow definitions:

```yaml
# list_workflow.yaml
workflows:
  complex_analysis:
    - step: extract
      agent: data_extractor
      input: "${input}"
    
    - step: validate
      agent: data_validator
      input: "${extract}"
      depends_on: [extract]
    
    - step: analyze
      agent: data_analyzer
      input: "${validate}"
      depends_on: [validate]
      
    - step: format
      type: transform
      function: format_results
      input: "${analyze}"
      depends_on: [analyze]
```

**V2 Usage:**
```python
# Load list format workflows
workflows = await load_yaml_workflows("list_workflow.yaml")
result = await execute_workflow("complex_analysis", {"input": "data"})
```

### **3. Dictionary Format**

Full workflow configuration with metadata:

```yaml
# dict_workflow.yaml
workflows:
  comprehensive_pipeline:
    name: "Comprehensive Data Pipeline"
    description: "Full data processing with validation and error handling"
    timeout: 300
    retry_policy:
      max_retries: 3
      exponential_backoff: true
    error_strategy: "continue"
    
    variables:
      confidence_threshold: 0.8
      output_format: "json"
    
    steps:
      - id: extract
        type: agent
        agent_id: data_extractor
        input_template: "Extract data from: ${input}"
        timeout: 60
        
      - id: validate
        type: tool
        tool_name: data_validator
        tool_input: "${extract}"
        depends_on: [extract]
        
      - id: quality_check
        type: condition
        condition: "${validate.confidence} >= ${confidence_threshold}"
        true_step: analyze
        false_step: manual_review
        depends_on: [validate]
        
      - id: analyze
        type: agent
        agent_id: data_analyzer
        input_template: "Analyze validated data: ${validate}"
        depends_on: [quality_check]
        
      - id: manual_review
        type: agent
        agent_id: manual_reviewer
        input_template: "Manual review needed: ${validate}"
        depends_on: [quality_check]
        
      - id: format_output
        type: transform
        function: format_final_output
        input: "${analyze || manual_review}"
        depends_on: [analyze, manual_review]
```

**V2 Usage:**
```python
# Load dictionary format workflows
workflows = await load_yaml_workflows("dict_workflow.yaml")
result = await execute_workflow("comprehensive_pipeline", {
    "input": "complex data set",
    "confidence_threshold": 0.9  # Override default
})
```

### **4. Legacy Format Support**

Automatic conversion of legacy template syntax:

```yaml
# legacy_workflow.yaml
workflows:
  legacy_analysis:
    steps:
      - id: extract
        agent: extractor
        input: "${context.user_input}"  # Legacy syntax
        
      - id: process
        agent: processor
        input: "${context.step_outputs.extract}"  # Legacy syntax
        depends_on: [extract]
        
      - id: respond
        agent: responder
        input: "${context.step_outputs.process}"  # Legacy syntax
        depends_on: [process]
```

**Automatic Conversion:**
```python
# V2 automatically converts legacy syntax
workflows = await load_yaml_workflows("legacy_workflow.yaml")

# Legacy ${context.step_outputs.extract} becomes ${extract}
# Legacy ${context.user_input} becomes ${input}
result = await execute_workflow("legacy_analysis", {"input": "user data"})
```

---

## 🔄 Migration Strategies

### **Strategy 1: Keep YAML, Upgrade Execution**

Continue using YAML but run with V2 engine:

```python
# Use existing YAML with V2 features
workflows = await load_yaml_workflows("existing.yaml")

# Execute with V2 monitoring
monitor = get_workflow_monitor()
await monitor.subscribe_to_workflow("my_workflow", on_step_complete)

result = await execute_workflow("my_workflow", inputs, mode="streaming")
```

### **Strategy 2: Convert to Updated YAML**

Modernize YAML syntax while keeping YAML format:

```python
# Migrate to modern YAML syntax
migration_result = await migrate_yaml_workflows(
    source_dir="./legacy/",
    target_format="v2_yaml",
    output_dir="./modernized/"
)

# Modern YAML with V2 syntax
```

**Before (Legacy):**
```yaml
workflows:
  analysis:
    steps:
      - id: extract
        input: "${context.user_input}"
      - id: process
        input: "${context.step_outputs.extract}"
```

**After (Modern YAML):**
```yaml
workflows:
  analysis:
    steps:
      - id: extract
        input: "${input}"
      - id: process
        input: "${extract}"
        depends_on: [extract]
```

### **Strategy 3: Convert to Fluent Builder**

Convert YAML workflows to V2 fluent builder code:

```python
# Convert to fluent builder
migration_result = await migrate_yaml_workflows(
    source_dir="./yaml_workflows/",
    target_format="v2_builder",
    output_dir="./python_workflows/"
)

# Generates Python files with fluent builder code
```

**Generated Code:**
```python
# Generated from YAML
from langswarm.core.workflows import WorkflowBuilder

workflow = (WorkflowBuilder("analysis", "Data Analysis")
    .add_agent_step("extract", "data_extractor", "${input}")
    .add_agent_step("process", "data_processor", "${extract}", depends_on=["extract"])
    .build())
```

---

## 🛠️ Advanced YAML Features

### **Conditional Workflows**

```yaml
workflows:
  conditional_approval:
    steps:
      - id: review
        type: agent
        agent_id: reviewer
        input: "Review this content: ${input}"
        
      - id: auto_approve_check
        type: condition
        condition: "${review.score} >= 0.8"
        true_step: auto_approve
        false_step: manual_approval
        depends_on: [review]
        
      - id: auto_approve
        type: agent
        agent_id: auto_approver
        input: "Auto-approved: ${review}"
        depends_on: [auto_approve_check]
        
      - id: manual_approval
        type: agent
        agent_id: manual_approver
        input: "Manual approval needed: ${review}"
        depends_on: [auto_approve_check]
```

### **Tool Integration**

```yaml
workflows:
  tool_workflow:
    steps:
      - id: search
        type: tool
        tool_name: web_search
        tool_input: "${query}"
        tool_config:
          max_results: 10
          timeout: 30
          
      - id: read_file
        type: tool
        tool_name: filesystem
        tool_input: "${filename}"
        tool_config:
          operation: read
          encoding: utf-8
          
      - id: process_data
        type: agent
        agent_id: processor
        input: "Process search results: ${search} and file content: ${read_file}"
        depends_on: [search, read_file]
```

### **Data Transformation**

```yaml
workflows:
  transform_workflow:
    steps:
      - id: extract
        type: agent
        agent_id: extractor
        input: "${input}"
        
      - id: normalize
        type: transform
        function: normalize_data
        input: "${extract}"
        depends_on: [extract]
        
      - id: validate
        type: transform
        function: validate_format
        input: "${normalize}"
        depends_on: [normalize]
```

### **Error Handling**

```yaml
workflows:
  robust_workflow:
    error_strategy: "continue"
    retry_policy:
      max_retries: 3
      exponential_backoff: true
      retry_delay: 1.0
    
    steps:
      - id: risky_step
        type: agent
        agent_id: risky_agent
        input: "${input}"
        retry_count: 5
        fallback_step: backup_step
        
      - id: backup_step
        type: agent
        agent_id: backup_agent
        input: "${input}"
```

---

## 📊 Migration Tools

### **Batch Migration**

```python
from langswarm.core.workflows import YAMLMigrationTool

# Create migration tool
migrator = YAMLMigrationTool()

# Migrate entire directory
result = await migrator.migrate_directory(
    source_dir="./legacy_workflows/",
    target_dir="./v2_workflows/",
    target_format="v2_builder",
    validate=True,
    backup=True
)

print(f"Migration Summary:")
print(f"  Files processed: {result.files_processed}")
print(f"  Successful migrations: {result.success_count}")
print(f"  Failed migrations: {result.error_count}")
print(f"  Warnings: {result.warning_count}")

# Review migration details
for migration in result.migrations:
    if migration.success:
        print(f"✓ {migration.source_file} -> {migration.target_file}")
    else:
        print(f"✗ {migration.source_file}: {migration.error}")
```

### **Validation During Migration**

```python
# Validate YAML workflows before migration
validator = YAMLWorkflowValidator()

validation_result = await validator.validate_file("workflow.yaml")
if validation_result.is_valid:
    # Proceed with migration
    workflows = await load_yaml_workflows("workflow.yaml")
else:
    print("Validation errors:")
    for error in validation_result.errors:
        print(f"  - {error.message} (Line {error.line})")
```

### **Custom Migration Rules**

```python
# Configure custom migration rules
migration_config = {
    "template_conversion": {
        "${context.user_input}": "${input}",
        "${context.step_outputs.{step}}": "${{{step}}}",
        "${context.variables.{var}}": "${{{var}}}"
    },
    "step_conversion": {
        "agent_step": "agent",
        "tool_step": "tool",
        "condition_step": "condition"
    },
    "validation_rules": [
        "check_circular_dependencies",
        "validate_agent_references",
        "check_template_syntax"
    ]
}

# Apply custom migration
result = await migrator.migrate_with_config(
    source_file="custom_workflow.yaml",
    config=migration_config
)
```

---

## 🔍 Debugging YAML Workflows

### **Validation Errors**

```python
# Common YAML validation issues and solutions
try:
    workflows = await load_yaml_workflows("problematic.yaml")
except YAMLValidationError as e:
    print(f"YAML Error: {e.message}")
    print(f"Line {e.line}, Column {e.column}")
    print(f"Suggestion: {e.suggestion}")

# Example fixes:
"""
Error: Invalid step dependency 'nonexistent_step'
Solution: Check step IDs for typos, ensure referenced steps exist

Error: Circular dependency detected: step1 -> step2 -> step1
Solution: Review step dependencies, remove circular references

Error: Missing required field 'agent_id' in step 'analyze'
Solution: Add agent_id field or change step type
"""
```

### **Template Syntax Issues**

```python
# Common template syntax problems
template_issues = {
    "Legacy syntax": {
        "problem": "${context.step_outputs.extract}",
        "solution": "${extract}",
        "auto_fix": True
    },
    "Invalid variable": {
        "problem": "${nonexistent_var}",
        "solution": "Add variable or use correct name",
        "auto_fix": False
    },
    "Malformed template": {
        "problem": "$extract}",  # Missing opening brace
        "solution": "${extract}",
        "auto_fix": True
    }
}

# Enable auto-fix during migration
migration_result = await migrate_yaml_workflows(
    source_dir="./problematic/",
    auto_fix_templates=True,
    report_fixes=True
)
```

---

## 📈 Performance Considerations

### **YAML Loading Performance**

```python
# Optimize YAML loading for large files
yaml_config = {
    "lazy_loading": True,      # Load workflows on-demand
    "cache_parsed": True,      # Cache parsed workflows
    "validate_async": True,    # Async validation
    "batch_size": 10          # Batch process multiple files
}

workflows = await load_yaml_workflows(
    "large_workflow_collection.yaml",
    config=yaml_config
)
```

### **Memory Management**

```python
# Manage memory for large YAML collections
async with YAMLWorkflowManager() as manager:
    # Load workflows in batches
    for batch in manager.load_batches("huge_workflows.yaml", batch_size=5):
        for workflow in batch:
            result = await execute_workflow(workflow.workflow_id, inputs)
            # Process result immediately, don't accumulate
```

---

## 🔧 Best Practices

### **YAML Structure**
- **Use clear step IDs**: Make step names descriptive and consistent
- **Document dependencies**: Clearly specify step dependencies
- **Organize by complexity**: Group simple workflows separately from complex ones
- **Use variables**: Define reusable variables for common values

### **Migration Strategy**
- **Start with simple workflows**: Migrate simple workflows first to validate process
- **Validate thoroughly**: Always validate workflows before and after migration
- **Keep backups**: Maintain backups of original YAML files
- **Test incrementally**: Test migrated workflows individually before batch processing

### **Template Syntax**
- **Use V2 syntax**: Prefer `${step}` over legacy `${context.step_outputs.step}`
- **Validate variables**: Ensure all template variables are defined
- **Escape special characters**: Handle special characters in template values
- **Test templates**: Validate template resolution with sample data

### **Error Handling**
- **Plan for failures**: Include fallback steps for critical operations
- **Use retries**: Configure appropriate retry policies
- **Monitor execution**: Use V2 monitoring to track workflow health
- **Handle edge cases**: Consider and handle unusual input scenarios

---

## 💡 Examples

### **Complete Migration Example**

```python
import asyncio
from langswarm.core.workflows import (
    load_yaml_workflows, 
    migrate_yaml_workflows,
    execute_workflow,
    get_workflow_monitor
)

async def complete_migration_example():
    """Complete example of YAML workflow migration and execution"""
    
    # 1. Load existing YAML workflows
    print("Loading existing YAML workflows...")
    workflows = await load_yaml_workflows("legacy_workflows.yaml")
    print(f"Loaded {len(workflows)} workflows")
    
    # 2. Validate loaded workflows
    print("Validating workflows...")
    for workflow in workflows:
        validation = await workflow.validate()
        if not validation.is_valid:
            print(f"Warning: {workflow.workflow_id} has validation issues")
    
    # 3. Execute YAML workflow with V2 features
    print("Executing workflow with V2 monitoring...")
    monitor = get_workflow_monitor()
    
    # Subscribe to events
    async def on_step_complete(event):
        print(f"Step completed: {event.step_id} - {event.status}")
    
    await monitor.subscribe_to_workflow("data_analysis", on_step_complete)
    
    # Execute with streaming
    async for step_result in execute_workflow_stream("data_analysis", {"input": "sample data"}):
        print(f"Real-time: {step_result.step_id} -> {step_result.status}")
    
    # 4. Migrate to modern format
    print("Migrating to modern format...")
    migration_result = await migrate_yaml_workflows(
        source_dir="./legacy/",
        target_format="v2_builder",
        output_dir="./modern/",
        validate=True
    )
    
    print(f"Migration complete: {migration_result.success_count} workflows migrated")
    
    return workflows, migration_result

# Run the example
if __name__ == "__main__":
    asyncio.run(complete_migration_example())
```

---

**LangSwarm V2's YAML compatibility ensures a smooth transition from legacy workflows while providing access to all modern V2 features including monitoring, middleware integration, and enhanced error handling.**

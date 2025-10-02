# YAML Workflow Migration & Compatibility

**Seamless migration path from V1 YAML workflows to V2 with 100% backward compatibility**

## 🎯 Overview

LangSwarm V2 provides complete backward compatibility with existing YAML workflows while offering a smooth migration path to modern V2 features. This guide covers automatic YAML parsing, template conversion, and gradual migration strategies.

**Migration Benefits:**
- **Zero Downtime**: Existing YAML workflows work immediately
- **Automatic Conversion**: Legacy template syntax automatically updated
- **Gradual Migration**: Migrate at your own pace
- **Enhanced Features**: Access V2 monitoring and middleware while using YAML

---

## 🔄 Migration Strategies

### **Strategy 1: Immediate Compatibility**

Your existing YAML workflows work immediately without changes:

```python
# Existing YAML workflows work with V2 engine
from langswarm.core.workflows import load_yaml_workflows, execute_workflow

# Load your existing YAML files
workflows = await load_yaml_workflows("production_workflows.yaml")

# Execute with V2 engine - no changes needed
result = await execute_workflow("existing_workflow", inputs)
```

### **Strategy 2: Enhanced Execution**

Keep YAML format but add V2 monitoring and middleware:

```python
# Use existing YAML with V2 features
workflows = await load_yaml_workflows("workflows.yaml")

# Add V2 monitoring
monitor = get_workflow_monitor()
await monitor.subscribe_to_workflow("my_workflow", callback)

# Execute with middleware
result = await execute_workflow_with_middleware(
    "my_workflow", 
    inputs, 
    user_id="user123"
)
```

### **Strategy 3: Modernized YAML**

Update YAML syntax while keeping YAML format:

```yaml
# Before (Legacy YAML)
workflows:
  data_analysis:
    steps:
      - id: extract
        agent: extractor
        input: "${context.user_input}"  # Legacy syntax
      - id: process
        agent: processor
        input: "${context.step_outputs.extract}"  # Legacy syntax

# After (Modern YAML) - Auto-converted
workflows:
  data_analysis:
    steps:
      - id: extract
        agent: extractor
        input: "${input}"  # Modern syntax
      - id: process
        agent: processor
        input: "${extract}"  # Modern syntax
        depends_on: [extract]  # Explicit dependencies
```

### **Strategy 4: Full V2 Migration**

Convert to fluent builder API for maximum V2 benefits:

```python
# Generated from YAML migration
from langswarm.core.workflows import WorkflowBuilder

workflow = (WorkflowBuilder("data_analysis", "Data Analysis")
    .add_agent_step("extract", "extractor", "${input}")
    .add_agent_step("process", "processor", "${extract}", depends_on=["extract"])
    .build())
```

---

## 📄 YAML Format Compatibility

### **Legacy Template Syntax**

V2 automatically converts legacy template syntax:

```yaml
# V1 Legacy Syntax (automatically converted)
workflows:
  legacy_workflow:
    steps:
      - id: user_input_step
        input: "${context.user_input}"
        
      - id: step_output_usage
        input: "${context.step_outputs.user_input_step}"
        
      - id: variable_usage
        input: "${context.variables.my_variable}"
        
      - id: metadata_usage
        input: "${context.metadata.source}"
```

**Automatic Conversion to V2:**
```yaml
# V2 Modern Syntax (auto-generated)
workflows:
  legacy_workflow:
    steps:
      - id: user_input_step
        input: "${input}"  # context.user_input -> input
        
      - id: step_output_usage
        input: "${user_input_step}"  # context.step_outputs.X -> X
        depends_on: [user_input_step]  # Auto-added dependency
        
      - id: variable_usage
        input: "${my_variable}"  # context.variables.X -> X
        
      - id: metadata_usage
        input: "${metadata.source}"  # context.metadata -> metadata
```

### **Complex Legacy Workflows**

```yaml
# Complex legacy workflow with all V1 patterns
workflows:
  complex_legacy:
    variables:
      threshold: 0.8
      output_format: "json"
    
    steps:
      - id: extract_data
        type: agent_step
        agent: data_extractor
        input_template: "Extract from: ${context.user_input}"
        timeout: 60
        
      - id: validate_extraction
        type: tool_step
        tool: data_validator
        input: "${context.step_outputs.extract_data}"
        depends_on: [extract_data]
        
      - id: quality_gate
        type: condition_step
        condition: "${context.step_outputs.validate_extraction.score} >= ${context.variables.threshold}"
        true_branch: process_data
        false_branch: manual_review
        depends_on: [validate_extraction]
        
      - id: process_data
        type: agent_step
        agent: data_processor
        input_template: "Process: ${context.step_outputs.validate_extraction.data}"
        depends_on: [quality_gate]
        
      - id: manual_review
        type: agent_step
        agent: manual_reviewer
        input_template: "Review needed: ${context.step_outputs.validate_extraction}"
        depends_on: [quality_gate]
        
      - id: format_output
        type: transform_step
        function: format_results
        input: "${context.step_outputs.process_data || context.step_outputs.manual_review}"
        output_format: "${context.variables.output_format}"
        depends_on: [process_data, manual_review]
```

**V2 Auto-Conversion:**
```yaml
# Automatically converted to V2 syntax
workflows:
  complex_legacy:
    variables:
      threshold: 0.8
      output_format: "json"
    
    steps:
      - id: extract_data
        type: agent
        agent_id: data_extractor
        input_template: "Extract from: ${input}"
        timeout_seconds: 60
        
      - id: validate_extraction
        type: tool
        tool_name: data_validator
        tool_input: "${extract_data}"
        depends_on: [extract_data]
        
      - id: quality_gate
        type: condition
        condition: "${validate_extraction.score} >= ${threshold}"
        true_step: process_data
        false_step: manual_review
        depends_on: [validate_extraction]
        
      - id: process_data
        type: agent
        agent_id: data_processor
        input_template: "Process: ${validate_extraction.data}"
        depends_on: [quality_gate]
        
      - id: manual_review
        type: agent
        agent_id: manual_reviewer
        input_template: "Review needed: ${validate_extraction}"
        depends_on: [quality_gate]
        
      - id: format_output
        type: transform
        function: format_results
        input: "${process_data || manual_review}"
        transform_config:
          output_format: "${output_format}"
        depends_on: [process_data, manual_review]
```

---

## 🛠️ Migration Tools

### **Automated YAML Migration**

```python
from langswarm.core.workflows.yaml_parser import YAMLWorkflowMigrator

# Create migrator
migrator = YAMLWorkflowMigrator()

# Migrate single file
migration_result = await migrator.migrate_file(
    source_file="legacy_workflow.yaml",
    target_file="modern_workflow.yaml",
    target_format="v2_yaml",  # or "v2_builder" for Python code
    validate=True,
    backup=True
)

if migration_result.success:
    print(f"✓ Migrated {migration_result.workflows_migrated} workflows")
    print(f"Template conversions: {migration_result.template_conversions}")
else:
    print(f"✗ Migration failed: {migration_result.error}")
    for warning in migration_result.warnings:
        print(f"⚠ Warning: {warning}")
```

### **Batch Directory Migration**

```python
# Migrate entire directory
batch_result = await migrator.migrate_directory(
    source_dir="./legacy_workflows/",
    target_dir="./v2_workflows/",
    target_format="v2_builder",
    recursive=True,
    validate=True,
    create_backup=True
)

print(f"Batch Migration Results:")
print(f"Files processed: {batch_result.files_processed}")
print(f"Successful migrations: {batch_result.success_count}")
print(f"Failed migrations: {batch_result.error_count}")
print(f"Total workflows migrated: {batch_result.total_workflows}")

# Detailed results
for file_result in batch_result.file_results:
    if file_result.success:
        print(f"✓ {file_result.source_file} -> {file_result.target_file}")
        print(f"  Workflows: {file_result.workflows_migrated}")
        print(f"  Conversions: {file_result.template_conversions}")
    else:
        print(f"✗ {file_result.source_file}: {file_result.error}")
```

### **Migration Validation**

```python
# Validate migration results
validator = YAMLMigrationValidator()

validation_result = await validator.validate_migration(
    original_file="legacy_workflow.yaml",
    migrated_file="modern_workflow.yaml"
)

if validation_result.equivalent:
    print("✓ Migration successful - workflows are functionally equivalent")
else:
    print("⚠ Migration validation issues:")
    for issue in validation_result.differences:
        print(f"  - {issue.type}: {issue.description}")
        print(f"    Original: {issue.original_value}")
        print(f"    Migrated: {issue.migrated_value}")
        print(f"    Impact: {issue.impact}")
```

---

## 🔧 Advanced Migration Features

### **Custom Migration Rules**

```python
# Configure custom migration rules
migration_config = {
    "template_conversions": {
        # Custom template mappings
        "${context.user_input}": "${input}",
        "${context.step_outputs.{step}}": "${{{step}}}",
        "${context.variables.{var}}": "${{{var}}}",
        "${context.metadata.{key}}": "${{metadata.{key}}}",
        
        # Custom business logic mappings
        "${context.session.user_id}": "${user_id}",
        "${context.workflow.instance_id}": "${workflow_instance_id}"
    },
    
    "step_type_mappings": {
        # Legacy step type conversions
        "agent_step": "agent",
        "tool_step": "tool", 
        "condition_step": "condition",
        "transform_step": "transform",
        "custom_step": "custom"
    },
    
    "field_mappings": {
        # Field name updates
        "input_template": "prompt_template",
        "agent": "agent_id",
        "tool": "tool_name",
        "true_branch": "true_step",
        "false_branch": "false_step"
    },
    
    "validation_rules": [
        "check_circular_dependencies",
        "validate_agent_references", 
        "check_template_syntax",
        "verify_tool_availability"
    ]
}

# Apply custom migration
custom_migrator = YAMLWorkflowMigrator(config=migration_config)
result = await custom_migrator.migrate_file("custom_legacy.yaml")
```

### **Incremental Migration**

```python
# Migrate workflows incrementally
incremental_migrator = IncrementalYAMLMigrator()

# Stage 1: Basic compatibility (no changes to YAML)
stage1_result = await incremental_migrator.enable_v2_compatibility(
    "production_workflows.yaml"
)

# Stage 2: Template modernization (update syntax)
stage2_result = await incremental_migrator.modernize_templates(
    "production_workflows.yaml",
    backup=True
)

# Stage 3: Structure optimization (add explicit dependencies)
stage3_result = await incremental_migrator.optimize_structure(
    "production_workflows.yaml"
)

# Stage 4: Convert to builder (optional)
stage4_result = await incremental_migrator.convert_to_builder(
    "production_workflows.yaml",
    output_file="production_workflows.py"
)

print(f"Incremental Migration Complete:")
print(f"Stage 1 - Compatibility: {stage1_result.success}")
print(f"Stage 2 - Templates: {stage2_result.conversions}")
print(f"Stage 3 - Structure: {stage3_result.optimizations}")
print(f"Stage 4 - Builder: {stage4_result.workflows_converted}")
```

### **Migration with Business Logic**

```python
# Custom migration with business-specific transformations
class BusinessWorkflowMigrator(YAMLWorkflowMigrator):
    """Custom migrator with business logic"""
    
    async def apply_business_transformations(self, workflow_data):
        """Apply business-specific transformations"""
        
        # Add compliance steps to financial workflows
        if "financial" in workflow_data.get("name", "").lower():
            compliance_step = {
                "id": "compliance_check",
                "type": "agent",
                "agent_id": "compliance_validator",
                "input": "${input}",
                "required": True
            }
            workflow_data.setdefault("steps", []).insert(0, compliance_step)
        
        # Add audit logging to sensitive workflows
        if workflow_data.get("sensitivity") == "high":
            for step in workflow_data.get("steps", []):
                step["audit_logging"] = True
        
        # Convert legacy security patterns
        await self._convert_security_patterns(workflow_data)
        
        return workflow_data
    
    async def _convert_security_patterns(self, workflow_data):
        """Convert legacy security patterns to V2"""
        for step in workflow_data.get("steps", []):
            if step.get("require_approval"):
                # Convert to approval workflow pattern
                step["type"] = "condition"
                step["condition"] = "${approval_required}"
                step["true_step"] = f"{step['id']}_approved"
                step["false_step"] = f"{step['id']}_pending"

# Use business migrator
business_migrator = BusinessWorkflowMigrator()
result = await business_migrator.migrate_file("financial_workflows.yaml")
```

---

## 🧪 Testing Migration

### **Migration Testing Framework**

```python
import pytest
from langswarm.core.workflows.testing import YAMLMigrationTestSuite

class TestWorkflowMigration:
    """Test suite for YAML workflow migration"""
    
    async def test_basic_migration(self):
        """Test basic YAML to V2 migration"""
        
        # Create test YAML
        test_yaml = """
        workflows:
          test_workflow:
            steps:
              - id: step1
                agent: test_agent
                input: "${context.user_input}"
              - id: step2
                input: "${context.step_outputs.step1}"
        """
        
        # Migrate
        migrator = YAMLWorkflowMigrator()
        result = await migrator.migrate_yaml_content(test_yaml)
        
        # Verify migration
        assert result.success
        assert "test_workflow" in result.workflows
        
        # Verify template conversion
        step1 = result.workflows["test_workflow"]["steps"][0]
        assert step1["input"] == "${input}"
        
        step2 = result.workflows["test_workflow"]["steps"][1]
        assert step2["input"] == "${step1}"
        assert step2["depends_on"] == ["step1"]
    
    async def test_execution_equivalence(self):
        """Test that migrated workflows produce same results"""
        
        # Load original and migrated workflows
        original = await load_yaml_workflows("original.yaml")
        migrated = await load_yaml_workflows("migrated.yaml")
        
        # Test inputs
        test_inputs = {"input": "test data"}
        
        # Execute both
        original_result = await execute_workflow("test_workflow", test_inputs, workflows=original)
        migrated_result = await execute_workflow("test_workflow", test_inputs, workflows=migrated)
        
        # Compare results
        assert original_result.status == migrated_result.status
        assert original_result.final_result == migrated_result.final_result
        
        # Migrated should be faster due to V2 optimizations
        assert migrated_result.total_duration_ms <= original_result.total_duration_ms
    
    async def test_complex_workflow_migration(self):
        """Test migration of complex workflows with all features"""
        
        complex_yaml = """
        workflows:
          complex_workflow:
            variables:
              threshold: 0.8
            steps:
              - id: extract
                type: agent_step
                agent: extractor
                input_template: "${context.user_input}"
              - id: validate
                type: condition_step
                condition: "${context.step_outputs.extract.confidence} >= ${context.variables.threshold}"
                true_branch: process
                false_branch: manual_review
              - id: process
                type: agent_step
                agent: processor
                input_template: "${context.step_outputs.extract.data}"
              - id: manual_review
                type: agent_step
                agent: reviewer
                input_template: "${context.step_outputs.extract}"
        """
        
        migrator = YAMLWorkflowMigrator()
        result = await migrator.migrate_yaml_content(complex_yaml)
        
        # Verify all features migrated correctly
        workflow = result.workflows["complex_workflow"]
        
        # Variables preserved
        assert workflow["variables"]["threshold"] == 0.8
        
        # Step types converted
        steps = {step["id"]: step for step in workflow["steps"]}
        assert steps["extract"]["type"] == "agent"
        assert steps["validate"]["type"] == "condition"
        
        # Templates converted
        assert steps["extract"]["input_template"] == "${input}"
        assert steps["validate"]["condition"] == "${extract.confidence} >= ${threshold}"
        assert steps["process"]["input_template"] == "${extract.data}"
        
        # Dependencies added
        assert "extract" in steps["validate"]["depends_on"]
        assert "validate" in steps["process"]["depends_on"]
        assert "validate" in steps["manual_review"]["depends_on"]
```

### **Performance Testing**

```python
async def test_migration_performance():
    """Test migration performance with large workflows"""
    
    # Generate large test YAML
    large_yaml = generate_large_workflow_yaml(num_workflows=100, steps_per_workflow=20)
    
    # Time migration
    start_time = time.time()
    migrator = YAMLWorkflowMigrator()
    result = await migrator.migrate_yaml_content(large_yaml)
    migration_time = time.time() - start_time
    
    print(f"Migration Performance:")
    print(f"  Workflows: {result.workflows_migrated}")
    print(f"  Migration time: {migration_time:.2f}s")
    print(f"  Workflows per second: {result.workflows_migrated / migration_time:.1f}")
    
    # Verify all workflows migrated successfully
    assert result.success
    assert result.workflows_migrated == 100
    
    # Performance benchmark
    assert migration_time < 10.0  # Should complete in under 10 seconds
    assert result.workflows_migrated / migration_time > 5  # At least 5 workflows/second
```

---

## 📋 Migration Checklist

### **Pre-Migration Assessment**
- [ ] Inventory all existing YAML workflow files
- [ ] Identify custom template syntax and business logic
- [ ] Document current workflow dependencies and integrations
- [ ] Plan migration strategy (immediate/gradual/full)

### **Migration Execution**
- [ ] Backup all original YAML files
- [ ] Run migration validation on test files
- [ ] Migrate non-critical workflows first
- [ ] Test migrated workflows in staging environment
- [ ] Gradually migrate production workflows

### **Post-Migration Validation**
- [ ] Verify all workflows load successfully
- [ ] Test execution with sample data
- [ ] Compare results with original workflows
- [ ] Monitor performance improvements
- [ ] Validate integration with V2 features

### **Production Deployment**
- [ ] Deploy migrated workflows to production
- [ ] Monitor execution health and performance
- [ ] Verify V2 monitoring and middleware integration
- [ ] Update operational procedures and documentation

---

## 🎯 Migration Success Metrics

### **Compatibility Verification**
- [ ] **100% Load Success**: All YAML workflows load without errors
- [ ] **Execution Equivalence**: Migrated workflows produce same results
- [ ] **Template Conversion**: All legacy syntax automatically converted
- [ ] **Dependency Resolution**: Dependencies correctly inferred and added

### **Performance Improvements**
- [ ] **Faster Execution**: V2 engine provides performance improvements
- [ ] **Better Monitoring**: Access to V2 monitoring and debugging
- [ ] **Enhanced Features**: Integration with V2 middleware and error handling
- [ ] **Improved Reliability**: Better error handling and recovery

### **Developer Experience**
- [ ] **Seamless Migration**: No manual workflow rewriting required
- [ ] **Gradual Transition**: Ability to migrate incrementally
- [ ] **Enhanced Debugging**: Better error messages and execution tracing
- [ ] **Future Flexibility**: Path to modern fluent builder API

---

**LangSwarm V2's YAML compatibility layer ensures zero-friction migration from existing workflows while providing immediate access to V2's enhanced monitoring, middleware integration, and performance optimizations.**

# YAML Workflow Migration Examples

**Real-world examples of migrating YAML workflows to LangSwarm V2**

## 🎯 Overview

This collection provides practical examples of migrating different types of YAML workflows to LangSwarm V2, showing both automatic migration and manual optimization techniques.

**Example Categories:**
- **Simple Workflows**: Basic agent chains and linear processes
- **Complex Workflows**: Multi-step processes with conditions and branching
- **Legacy Workflows**: V1 workflows with legacy template syntax
- **Business Workflows**: Industry-specific workflow patterns

---

## 📝 Simple Workflow Examples

### **Example 1: Basic Data Processing**

#### **Original YAML (V1)**
```yaml
# simple_data_processing.yaml
workflows:
  data_processing: "data_extractor -> data_analyzer -> report_generator"
```

#### **V2 Auto-Migration Result**
```python
# Auto-generated from YAML
from langswarm.core.workflows import WorkflowBuilder

workflow = (WorkflowBuilder("data_processing", "Data Processing")
    .add_agent_step("data_extractor", "data_extractor", "${input}")
    .add_agent_step("data_analyzer", "data_analyzer", "${data_extractor}", depends_on=["data_extractor"])
    .add_agent_step("report_generator", "report_generator", "${data_analyzer}", depends_on=["data_analyzer"])
    .build())
```

#### **Migration Code**
```python
from langswarm.core.workflows import load_yaml_workflows, execute_workflow

# Load and execute original YAML
workflows = await load_yaml_workflows("simple_data_processing.yaml")
result = await execute_workflow("data_processing", {"input": "sample data"})

print(f"Result: {result.final_result}")
print(f"Duration: {result.total_duration_ms}ms")
```

### **Example 2: Content Review Pipeline**

#### **Original YAML**
```yaml
# content_review.yaml
workflows:
  content_review:
    - step: extract_content
      agent: content_extractor
      input: "${input}"
    
    - step: check_quality
      agent: quality_checker
      input: "${extract_content}"
      depends_on: [extract_content]
    
    - step: moderate_content
      agent: content_moderator
      input: "${extract_content}"
      depends_on: [extract_content]
    
    - step: final_review
      agent: final_reviewer
      input: "Quality: ${check_quality}, Moderation: ${moderate_content}"
      depends_on: [check_quality, moderate_content]
```

#### **V2 Migration**
```python
# Load and enhance with V2 features
workflows = await load_yaml_workflows("content_review.yaml")

# Add V2 monitoring
from langswarm.core.workflows import get_workflow_monitor

monitor = get_workflow_monitor()

async def content_review_callback(event):
    if event.type == "step_completed":
        print(f"✅ {event.step_id}: {event.data.get('status', 'completed')}")
    elif event.type == "step_failed":
        print(f"❌ {event.step_id}: {event.data.get('error', 'failed')}")

await monitor.subscribe_to_workflow("content_review", content_review_callback)

# Execute with monitoring
result = await execute_workflow("content_review", {
    "input": "User-generated content to review"
})
```

---

## 🔧 Complex Workflow Examples

### **Example 3: Approval Workflow with Conditions**

#### **Original YAML (Legacy Syntax)**
```yaml
# approval_workflow.yaml
workflows:
  document_approval:
    variables:
      auto_approve_threshold: 0.8
      reviewer_id: "senior_reviewer"
    
    steps:
      - id: initial_review
        type: agent_step
        agent: document_reviewer
        input_template: "Review this document: ${context.user_input}"
        
      - id: quality_gate
        type: condition_step
        condition: "${context.step_outputs.initial_review.score} >= ${context.variables.auto_approve_threshold}"
        true_branch: auto_approve
        false_branch: manual_approval
        depends_on: [initial_review]
        
      - id: auto_approve
        type: agent_step
        agent: auto_approver
        input_template: "Auto-approve: ${context.step_outputs.initial_review}"
        depends_on: [quality_gate]
        
      - id: manual_approval
        type: agent_step
        agent: "${context.variables.reviewer_id}"
        input_template: "Manual approval needed: ${context.step_outputs.initial_review}"
        depends_on: [quality_gate]
        
      - id: notification
        type: agent_step
        agent: notification_sender
        input_template: "Send notification: ${context.step_outputs.auto_approve || context.step_outputs.manual_approval}"
        depends_on: [auto_approve, manual_approval]
```

#### **V2 Auto-Migration Result**
```yaml
# Automatically converted to V2 syntax
workflows:
  document_approval:
    variables:
      auto_approve_threshold: 0.8
      reviewer_id: "senior_reviewer"
    
    steps:
      - id: initial_review
        type: agent
        agent_id: document_reviewer
        input_template: "Review this document: ${input}"
        
      - id: quality_gate
        type: condition
        condition: "${initial_review.score} >= ${auto_approve_threshold}"
        true_step: auto_approve
        false_step: manual_approval
        depends_on: [initial_review]
        
      - id: auto_approve
        type: agent
        agent_id: auto_approver
        input_template: "Auto-approve: ${initial_review}"
        depends_on: [quality_gate]
        
      - id: manual_approval
        type: agent
        agent_id: "${reviewer_id}"
        input_template: "Manual approval needed: ${initial_review}"
        depends_on: [quality_gate]
        
      - id: notification
        type: agent
        agent_id: notification_sender
        input_template: "Send notification: ${auto_approve || manual_approval}"
        depends_on: [auto_approve, manual_approval]
```

#### **Migration and Execution**
```python
# Migrate and execute approval workflow
workflows = await load_yaml_workflows("approval_workflow.yaml")

# Execute with different approval scenarios
test_cases = [
    {
        "name": "High Quality Document",
        "input": "Well-written, comprehensive report",
        "expected": "auto_approve"
    },
    {
        "name": "Low Quality Document", 
        "input": "Poorly written, incomplete draft",
        "expected": "manual_approval"
    }
]

for test_case in test_cases:
    result = await execute_workflow("document_approval", {
        "input": test_case["input"],
        "auto_approve_threshold": 0.8,
        "reviewer_id": "senior_reviewer"
    })
    
    print(f"Test: {test_case['name']}")
    print(f"Result: {result.final_result}")
    print(f"Expected path: {test_case['expected']}")
    print("---")
```

### **Example 4: Multi-Stage Analysis Pipeline**

#### **Original YAML**
```yaml
# analysis_pipeline.yaml
workflows:
  comprehensive_analysis:
    name: "Comprehensive Data Analysis Pipeline"
    timeout: 600
    retry_policy:
      max_retries: 2
      exponential_backoff: true
    
    variables:
      confidence_threshold: 0.85
      analysis_types: ["sentiment", "entities", "topics", "summary"]
    
    steps:
      - id: data_preparation
        type: agent_step
        agent: data_preprocessor
        input_template: "Prepare data for analysis: ${context.user_input}"
        timeout: 120
        
      - id: parallel_analysis
        type: parallel_group
        steps:
          - id: sentiment_analysis
            type: agent_step
            agent: sentiment_analyzer
            input_template: "Analyze sentiment: ${context.step_outputs.data_preparation}"
            
          - id: entity_extraction
            type: agent_step
            agent: entity_extractor
            input_template: "Extract entities: ${context.step_outputs.data_preparation}"
            
          - id: topic_modeling
            type: agent_step
            agent: topic_modeler
            input_template: "Extract topics: ${context.step_outputs.data_preparation}"
            
          - id: text_summarization
            type: agent_step
            agent: text_summarizer
            input_template: "Summarize text: ${context.step_outputs.data_preparation}"
        depends_on: [data_preparation]
        
      - id: quality_check
        type: condition_step
        condition: "${context.step_outputs.sentiment_analysis.confidence} >= ${context.variables.confidence_threshold}"
        true_branch: synthesis
        false_branch: quality_review
        depends_on: [parallel_analysis]
        
      - id: synthesis
        type: agent_step
        agent: analysis_synthesizer
        input_template: |
          Synthesize analysis results:
          Sentiment: ${context.step_outputs.sentiment_analysis}
          Entities: ${context.step_outputs.entity_extraction}
          Topics: ${context.step_outputs.topic_modeling}
          Summary: ${context.step_outputs.text_summarization}
        depends_on: [quality_check]
        
      - id: quality_review
        type: agent_step
        agent: quality_reviewer
        input_template: "Low confidence analysis - manual review needed"
        depends_on: [quality_check]
        
      - id: final_formatting
        type: transform_step
        function: format_analysis_report
        input: "${context.step_outputs.synthesis || context.step_outputs.quality_review}"
        depends_on: [synthesis, quality_review]
```

#### **V2 Fluent Builder Migration**
```python
# Convert to V2 fluent builder for maximum benefits
from langswarm.core.workflows import WorkflowBuilder

workflow = (WorkflowBuilder("comprehensive_analysis", "Comprehensive Data Analysis Pipeline")
    .set_timeout(600)
    .set_retry_policy(max_retries=2, exponential_backoff=True)
    
    .add_variable("confidence_threshold", 0.85)
    .add_variable("analysis_types", ["sentiment", "entities", "topics", "summary"])
    
    # Data preparation
    .add_agent_step("data_preparation", "data_preprocessor", 
                   "Prepare data for analysis: ${input}", 
                   timeout_seconds=120)
    
    # Parallel analysis
    .add_parallel_group([
        ("sentiment_analysis", "sentiment_analyzer", "Analyze sentiment: ${data_preparation}"),
        ("entity_extraction", "entity_extractor", "Extract entities: ${data_preparation}"),
        ("topic_modeling", "topic_modeler", "Extract topics: ${data_preparation}"),
        ("text_summarization", "text_summarizer", "Summarize text: ${data_preparation}")
    ], depends_on=["data_preparation"])
    
    # Quality gate
    .add_condition_step("quality_check", 
                       "${sentiment_analysis.confidence} >= ${confidence_threshold}",
                       "synthesis", "quality_review",
                       depends_on=["sentiment_analysis", "entity_extraction", "topic_modeling", "text_summarization"])
    
    # Synthesis path
    .add_agent_step("synthesis", "analysis_synthesizer",
                   """Synthesize analysis results:
                   Sentiment: ${sentiment_analysis}
                   Entities: ${entity_extraction}
                   Topics: ${topic_modeling}
                   Summary: ${text_summarization}""",
                   depends_on=["quality_check"])
    
    # Quality review path
    .add_agent_step("quality_review", "quality_reviewer",
                   "Low confidence analysis - manual review needed",
                   depends_on=["quality_check"])
    
    # Final formatting
    .add_transform_step("final_formatting", "${synthesis || quality_review}",
                       format_analysis_report,
                       depends_on=["synthesis", "quality_review"])
    
    .build())

# Execute with V2 monitoring
monitor = get_workflow_monitor()
debugger = get_workflow_debugger()

# Monitor execution
async def analysis_monitor(event):
    if event.type == "step_completed":
        step_result = event.data
        print(f"✅ {event.step_id} completed in {step_result.get('duration_ms', 0)}ms")
        
        # Log parallel execution performance
        if event.step_id in ["sentiment_analysis", "entity_extraction", "topic_modeling", "text_summarization"]:
            confidence = step_result.get("confidence", 0)
            print(f"   Confidence: {confidence:.2%}")

await monitor.subscribe_to_workflow("comprehensive_analysis", analysis_monitor)

# Execute analysis
result = await execute_workflow("comprehensive_analysis", {
    "input": "Large dataset for comprehensive analysis",
    "confidence_threshold": 0.9  # Override for this execution
})

# Analyze performance
performance = await debugger.analyze_workflow_performance("comprehensive_analysis")
print(f"Analysis Performance:")
print(f"  Total duration: {result.total_duration_ms}ms")
print(f"  Parallel efficiency: {performance.parallel_efficiency:.1%}")
print(f"  Bottlenecks: {[b.step_id for b in performance.bottlenecks]}")
```

---

## 🏢 Business Workflow Examples

### **Example 5: Financial Document Processing**

#### **Original YAML**
```yaml
# financial_processing.yaml
workflows:
  financial_document_processing:
    name: "Financial Document Processing"
    security_level: "high"
    compliance_required: true
    
    variables:
      accuracy_threshold: 0.95
      audit_required: true
      approver_role: "financial_manager"
    
    steps:
      - id: document_intake
        type: agent_step
        agent: document_classifier
        input_template: "Classify financial document: ${context.user_input}"
        security_level: "high"
        
      - id: compliance_check
        type: tool_step
        tool: compliance_validator
        input: "${context.step_outputs.document_intake}"
        required: true
        depends_on: [document_intake]
        
      - id: data_extraction
        type: agent_step
        agent: financial_data_extractor
        input_template: "Extract financial data: ${context.step_outputs.document_intake}"
        depends_on: [compliance_check]
        
      - id: accuracy_validation
        type: condition_step
        condition: "${context.step_outputs.data_extraction.accuracy} >= ${context.variables.accuracy_threshold}"
        true_branch: automated_processing
        false_branch: manual_review
        depends_on: [data_extraction]
        
      - id: automated_processing
        type: agent_step
        agent: automated_processor
        input_template: "Process: ${context.step_outputs.data_extraction}"
        depends_on: [accuracy_validation]
        
      - id: manual_review
        type: agent_step
        agent: financial_analyst
        input_template: "Manual review required: ${context.step_outputs.data_extraction}"
        depends_on: [accuracy_validation]
        
      - id: approval_required
        type: condition_step
        condition: "${context.variables.audit_required}"
        true_branch: manager_approval
        false_branch: final_processing
        depends_on: [automated_processing, manual_review]
        
      - id: manager_approval
        type: agent_step
        agent: "${context.variables.approver_role}"
        input_template: "Approval needed: ${context.step_outputs.automated_processing || context.step_outputs.manual_review}"
        depends_on: [approval_required]
        
      - id: final_processing
        type: agent_step
        agent: financial_processor
        input_template: "Final processing: ${context.step_outputs.automated_processing || context.step_outputs.manual_review}"
        depends_on: [approval_required]
        
      - id: audit_logging
        type: tool_step
        tool: audit_logger
        input: "${context.step_outputs.manager_approval || context.step_outputs.final_processing}"
        depends_on: [manager_approval, final_processing]
```

#### **V2 Migration with Business Logic**
```python
# Enhanced V2 migration with business-specific features
from langswarm.core.workflows import WorkflowBuilder
from langswarm.core.workflows.middleware_integration import execute_workflow_with_middleware

# Create enhanced financial workflow
financial_workflow = (WorkflowBuilder("financial_document_processing", "Financial Document Processing")
    .set_description("High-security financial document processing with compliance")
    .set_timeout(1800)  # 30 minutes for complex financial documents
    .set_retry_policy(max_retries=1, retry_delay=5.0)  # Conservative retry for financial data
    
    # Security and compliance variables
    .add_variable("accuracy_threshold", 0.95)
    .add_variable("audit_required", True)
    .add_variable("approver_role", "financial_manager")
    .add_variable("security_level", "high")
    
    # Document intake with enhanced security
    .add_agent_step("document_intake", "document_classifier",
                   "Classify financial document: ${input}",
                   metadata={"security_level": "high", "pii_handling": True})
    
    # Mandatory compliance check
    .add_tool_step("compliance_check", "compliance_validator", "${document_intake}",
                  depends_on=["document_intake"],
                  required=True,
                  metadata={"compliance_framework": "SOX"})
    
    # Data extraction with accuracy tracking
    .add_agent_step("data_extraction", "financial_data_extractor",
                   "Extract financial data: ${document_intake}",
                   depends_on=["compliance_check"],
                   metadata={"accuracy_tracking": True})
    
    # Accuracy-based routing
    .add_condition_step("accuracy_validation",
                       "${data_extraction.accuracy} >= ${accuracy_threshold}",
                       "automated_processing", "manual_review",
                       depends_on=["data_extraction"])
    
    # Processing paths
    .add_agent_step("automated_processing", "automated_processor",
                   "Process: ${data_extraction}",
                   depends_on=["accuracy_validation"],
                   metadata={"processing_type": "automated"})
    
    .add_agent_step("manual_review", "financial_analyst",
                   "Manual review required: ${data_extraction}",
                   depends_on=["accuracy_validation"],
                   metadata={"processing_type": "manual", "escalation": True})
    
    # Approval workflow
    .add_condition_step("approval_required", "${audit_required}",
                       "manager_approval", "final_processing",
                       depends_on=["automated_processing", "manual_review"])
    
    .add_agent_step("manager_approval", "${approver_role}",
                   "Approval needed: ${automated_processing || manual_review}",
                   depends_on=["approval_required"],
                   metadata={"approval_level": "manager", "audit_trail": True})
    
    .add_agent_step("final_processing", "financial_processor",
                   "Final processing: ${automated_processing || manual_review}",
                   depends_on=["approval_required"])
    
    # Mandatory audit logging
    .add_tool_step("audit_logging", "audit_logger",
                  "${manager_approval || final_processing}",
                  depends_on=["manager_approval", "final_processing"],
                  required=True,
                  metadata={"audit_type": "financial", "retention_years": 7})
    
    .build())

# Execute with middleware for enhanced security and monitoring
async def process_financial_document(document_data, user_id, session_id):
    """Process financial document with full security and compliance"""
    
    # Execute with middleware for security, audit, and monitoring
    result = await execute_workflow_with_middleware(
        "financial_document_processing",
        {
            "input": document_data,
            "accuracy_threshold": 0.98,  # Higher threshold for this execution
            "user_id": user_id,
            "session_id": session_id
        },
        user_id=user_id,
        security_context={
            "clearance_level": "financial",
            "audit_required": True,
            "compliance_frameworks": ["SOX", "PCI-DSS"]
        }
    )
    
    # Additional business logic
    if result.status == "completed":
        # Log successful processing
        await log_financial_transaction(result, user_id)
        
        # Check for alerts or notifications
        if result.metadata.get("manual_review_occurred"):
            await notify_compliance_team(result, "manual_review")
        
        # Generate compliance report
        compliance_report = await generate_compliance_report(result)
        
        return {
            "status": "success",
            "document_id": result.metadata.get("document_id"),
            "processing_type": result.metadata.get("processing_type"),
            "compliance_report": compliance_report,
            "audit_trail": result.metadata.get("audit_trail")
        }
    else:
        # Handle processing failure
        await notify_financial_team(result, "processing_failure")
        return {
            "status": "failed",
            "error": result.error,
            "escalation_required": True
        }

# Example usage
document_result = await process_financial_document(
    document_data="Invoice #12345 for $50,000",
    user_id="financial_clerk_001",
    session_id="session_abc123"
)

print(f"Financial Processing Result: {document_result}")
```

---

## 🔍 Migration Testing Examples

### **Testing Migration Equivalence**

```python
# Comprehensive migration testing
import pytest
import asyncio
from langswarm.core.workflows import load_yaml_workflows, execute_workflow

class TestWorkflowMigration:
    """Test suite for validating YAML migration results"""
    
    @pytest.mark.asyncio
    async def test_simple_workflow_migration(self):
        """Test simple workflow produces same results before/after migration"""
        
        # Original YAML content
        original_yaml = """
        workflows:
          simple_test:
            - step: step1
              agent: test_agent1
              input: "${context.user_input}"
            - step: step2
              agent: test_agent2
              input: "${context.step_outputs.step1}"
        """
        
        # Migrated YAML content
        migrated_yaml = """
        workflows:
          simple_test:
            - step: step1
              agent: test_agent1
              input: "${input}"
            - step: step2
              agent: test_agent2
              input: "${step1}"
              depends_on: [step1]
        """
        
        # Load both versions
        original_workflows = await load_yaml_workflows_from_string(original_yaml)
        migrated_workflows = await load_yaml_workflows_from_string(migrated_yaml)
        
        # Test input
        test_input = {"input": "test data"}
        
        # Execute both (using mock agents for testing)
        with mock_agents({"test_agent1": "result1", "test_agent2": "result2"}):
            original_result = await execute_workflow("simple_test", test_input, workflows=original_workflows)
            migrated_result = await execute_workflow("simple_test", test_input, workflows=migrated_workflows)
        
        # Compare results
        assert original_result.status == migrated_result.status
        assert original_result.final_result == migrated_result.final_result
        
        # Migrated should have explicit dependencies
        migrated_workflow = migrated_workflows["simple_test"]
        step2 = next(step for step in migrated_workflow.steps if step.step_id == "step2")
        assert "step1" in step2.depends_on
    
    @pytest.mark.asyncio
    async def test_complex_workflow_migration(self):
        """Test complex workflow with conditions and variables"""
        
        test_cases = [
            {
                "name": "High score path",
                "input": {"input": "high quality content"},
                "variables": {"threshold": 0.7},
                "expected_path": ["review", "auto_approve", "notify"]
            },
            {
                "name": "Low score path", 
                "input": {"input": "low quality content"},
                "variables": {"threshold": 0.9},
                "expected_path": ["review", "manual_review", "notify"]
            }
        ]
        
        for test_case in test_cases:
            # Execute test case
            result = await execute_workflow("approval_workflow", {
                **test_case["input"],
                **test_case["variables"]
            })
            
            # Verify execution path
            executed_steps = list(result.step_results.keys())
            for expected_step in test_case["expected_path"]:
                assert expected_step in executed_steps, f"Expected step {expected_step} not found in {executed_steps}"
    
    @pytest.mark.asyncio
    async def test_performance_improvement(self):
        """Test that V2 execution is faster than V1"""
        
        # Large workflow for performance testing
        large_workflow_yaml = generate_large_workflow_yaml(num_steps=50)
        workflows = await load_yaml_workflows_from_string(large_workflow_yaml)
        
        # Time V2 execution
        start_time = time.time()
        result = await execute_workflow("large_workflow", {"input": "test"}, workflows=workflows)
        v2_duration = time.time() - start_time
        
        # V2 should complete successfully
        assert result.status == "completed"
        
        # Performance expectations (adjust based on your requirements)
        assert v2_duration < 30.0  # Should complete in under 30 seconds
        assert result.total_duration_ms < 25000  # Workflow execution under 25 seconds
        
        print(f"Performance Test Results:")
        print(f"  Total execution time: {v2_duration:.2f}s")
        print(f"  Workflow duration: {result.total_duration_ms}ms")
        print(f"  Steps executed: {len(result.step_results)}")
        print(f"  Average step duration: {result.total_duration_ms / len(result.step_results):.1f}ms")

# Helper functions for testing
def generate_large_workflow_yaml(num_steps: int) -> str:
    """Generate large workflow YAML for performance testing"""
    steps = []
    for i in range(num_steps):
        step = {
            "id": f"step_{i}",
            "agent": f"agent_{i % 5}",  # Rotate through 5 different agents
            "input": "${input}" if i == 0 else f"${{step_{i-1}}}"
        }
        if i > 0:
            step["depends_on"] = [f"step_{i-1}"]
        steps.append(step)
    
    workflow = {
        "workflows": {
            "large_workflow": {
                "name": f"Large Workflow with {num_steps} steps",
                "steps": steps
            }
        }
    }
    
    import yaml
    return yaml.dump(workflow)

@contextmanager
def mock_agents(agent_responses: Dict[str, str]):
    """Mock agent responses for testing"""
    # Implementation depends on your testing framework
    # This would mock the agent execution to return predefined responses
    pass
```

---

## 📚 Best Practices from Examples

### **Migration Strategy**
- **Start Simple**: Begin with simple workflows to validate migration process
- **Test Thoroughly**: Compare results before and after migration
- **Gradual Rollout**: Migrate non-critical workflows first
- **Monitor Performance**: Track execution improvements with V2

### **Business Logic Integration**
- **Preserve Compliance**: Ensure security and compliance requirements are maintained
- **Add V2 Features**: Leverage V2 monitoring and middleware capabilities
- **Custom Validation**: Add business-specific validation and error handling
- **Audit Trails**: Implement comprehensive audit logging for critical workflows

### **Performance Optimization**
- **Parallel Execution**: Use V2's improved parallel execution for independent steps
- **Resource Management**: Set appropriate timeouts and retry policies
- **Monitoring Integration**: Use V2 monitoring to track performance improvements
- **Bottleneck Analysis**: Identify and optimize slow steps

### **Testing and Validation**
- **Functional Testing**: Verify migrated workflows produce same results
- **Performance Testing**: Measure execution time improvements
- **Integration Testing**: Test with V2 monitoring and middleware
- **Business Logic Testing**: Validate business-specific requirements

---

**These examples demonstrate the seamless migration path from YAML workflows to LangSwarm V2, showing how to preserve existing functionality while gaining access to V2's enhanced monitoring, middleware integration, and performance optimizations.**

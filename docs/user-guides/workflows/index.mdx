# LangSwarm V2 Workflow User Guide

**Learn how to create and execute workflows in the modernized LangSwarm V2 system**

## 🎯 Overview

LangSwarm V2 completely revolutionizes workflow creation with an intuitive, fluent builder API that replaces complex YAML configuration. Create powerful, multi-step workflows with automatic dependency resolution, parallel execution, and comprehensive error handling.

**Key Benefits:**
- **90% Simpler**: Fluent API vs complex YAML editing
- **Type Safe**: Compile-time validation vs runtime errors
- **Multiple Execution Modes**: Sync, async, streaming, parallel
- **Production Ready**: Error recovery, monitoring, validation

---

## 🚀 Quick Start

### **Create Your First Workflow**

```python
from langswarm.core.workflows import create_workflow, execute_workflow

# Create a simple data analysis workflow
workflow = (create_workflow("analysis", "Data Analysis Workflow")
    .add_agent_step("extract", "data_extractor", "Extract key information from: ${input}")
    .add_agent_step("analyze", "data_analyzer", "Analyze this data: ${extract}")
    .add_agent_step("summarize", "summarizer", "Summarize findings: ${analyze}")
    .build())

# Execute the workflow
result = await execute_workflow("analysis", {"input": "Sample data to analyze"})

# Check results
if result.status == "completed":
    print(f"Final result: {result.final_result}")
    print(f"Execution time: {result.total_duration_ms}ms")
else:
    print(f"Workflow failed: {result.error}")
```

### **Quick Workflow Patterns**

```python
from langswarm.core.workflows.builder import (
    create_simple_workflow, 
    create_analysis_workflow,
    create_approval_workflow
)

# Simple agent chain
simple = create_simple_workflow(
    workflow_id="simple_chain",
    name="Simple Processing Chain", 
    agents=["processor", "validator", "formatter"]
)

# Analysis workflow pattern
analysis = create_analysis_workflow(
    workflow_id="data_analysis",
    data_extractor="extractor",
    analyzer="analyzer", 
    validator="validator"
)

# Approval workflow pattern
approval = create_approval_workflow(
    workflow_id="document_approval",
    reviewer="document_reviewer",
    approver="manager",
    threshold=0.8
)
```

---

## 🎛️ Building Workflows

### **Basic Workflow Creation**

```python
from langswarm.core.workflows import WorkflowBuilder

# Start with builder
builder = WorkflowBuilder(workflow_id="my_workflow", name="My Custom Workflow")

# Add steps one by one
workflow = (builder
    .add_agent_step("step1", "agent1", "Process this: ${input}")
    .add_tool_step("step2", "web_search", "${step1}")
    .add_agent_step("step3", "agent2", "Combine: ${step1} and ${step2}")
    .build())
```

### **Step Types**

#### **Agent Steps**
```python
# Basic agent step
builder.add_agent_step(
    step_id="analyze",
    agent_id="data_analyzer", 
    prompt_template="Analyze this data: ${data}",
    depends_on=["extract"],  # Optional dependency
    timeout_seconds=60       # Optional timeout
)

# Agent step with advanced configuration
builder.add_agent_step(
    step_id="review",
    agent_id="reviewer",
    prompt_template="Review and score (1-10): ${content}",
    depends_on=["process"],
    timeout_seconds=30,
    retry_count=2,           # Retry on failure
    cache_result=True        # Cache for performance
)
```

#### **Tool Steps**
```python
# Basic tool step
builder.add_tool_step(
    step_id="search",
    tool_name="web_search",
    tool_input="${query}",
    depends_on=["prepare_query"]
)

# Tool step with configuration
builder.add_tool_step(
    step_id="file_read",
    tool_name="filesystem",
    tool_input="${filename}",
    tool_config={
        "operation": "read",
        "encoding": "utf-8"
    }
)
```

#### **Condition Steps**
```python
# Simple condition
builder.add_condition_step(
    step_id="quality_check",
    condition="${score} >= 8",
    true_step="approve",      # Go here if condition is true
    false_step="reject"       # Go here if condition is false
)

# Complex condition with variables
builder.add_condition_step(
    step_id="complex_check",
    condition="${score} >= ${threshold} and ${confidence} > 0.9",
    true_step="proceed",
    false_step="manual_review"
)
```

#### **Transform Steps**
```python
# Data transformation
def format_output(data):
    return {
        "summary": data.get("summary", ""),
        "score": float(data.get("score", 0)),
        "timestamp": datetime.now().isoformat()
    }

builder.add_transform_step(
    step_id="format",
    input_template="${analysis_result}",
    transform_function=format_output
)
```

### **Advanced Configuration**

```python
# Comprehensive workflow configuration
workflow = (WorkflowBuilder("advanced", "Advanced Workflow")
    .set_description("Complex multi-stage processing workflow")
    .set_timeout(300)                    # 5 minute total timeout
    .set_retry_policy(max_retries=3, exponential_backoff=True)
    .set_error_strategy("continue")      # Continue on step failures
    
    # Add variables
    .add_variable("threshold", 0.8)
    .add_variable("max_items", 100)
    
    # Require inputs
    .require_input("data")
    .require_input("config")
    
    # Add steps
    .add_agent_step("validate", "validator", "Validate: ${data}")
    .add_condition_step("check", "${validate.valid}", "process", "error")
    .add_agent_step("process", "processor", "${validate.data}")
    .add_transform_step("format", "${process}", format_function)
    
    .build())
```

---

## ⚡ Execution Modes

### **Synchronous Execution**
```python
# Immediate execution with results
result = await execute_workflow(
    workflow_id="analysis",
    inputs={"data": "sample data"},
    mode="sync"  # Default mode
)

print(f"Status: {result.status}")
print(f"Final result: {result.final_result}")
print(f"Duration: {result.total_duration_ms}ms")

# Check individual step results
for step_id, step_result in result.step_results.items():
    print(f"Step {step_id}: {step_result.status}")
    if step_result.result:
        print(f"  Result: {step_result.result}")
```

### **Asynchronous Execution**
```python
# Background execution
execution_id = await execute_workflow(
    workflow_id="long_analysis", 
    inputs={"large_dataset": data},
    mode="async"
)

print(f"Started execution: {execution_id}")

# Check status later
from langswarm.core.workflows import get_execution_status

status = await get_execution_status(execution_id)
print(f"Current status: {status.status}")

# Wait for completion
import asyncio
while status.status == "running":
    await asyncio.sleep(5)
    status = await get_execution_status(execution_id)
    print(f"Still running... Current step: {status.current_step}")

print(f"Final result: {status.final_result}")
```

### **Streaming Execution**
```python
# Real-time step-by-step results
from langswarm.core.workflows import execute_workflow_stream

print("Starting workflow execution...")
async for step_result in execute_workflow_stream("analysis", {"data": "input"}):
    print(f"✓ Step {step_result.step_id} completed")
    print(f"  Status: {step_result.status}")
    print(f"  Duration: {step_result.duration_ms}ms")
    
    if step_result.result:
        print(f"  Result: {step_result.result}")
    
    if step_result.status == "failed":
        print(f"  Error: {step_result.error}")
        break

print("Workflow execution complete!")
```

### **Parallel Execution**
```python
# Optimized parallel processing
result = await execute_workflow(
    workflow_id="parallel_analysis",
    inputs={"data": "large_dataset"},
    mode="parallel"  # Automatic dependency-based parallelization
)

print(f"Parallel execution completed in {result.total_duration_ms}ms")

# View execution plan
execution_plan = result.metadata.get("execution_plan", {})
print(f"Dependency levels: {execution_plan.get('levels', [])}")
print(f"Parallel groups: {execution_plan.get('parallel_groups', [])}")
```

---

## 🔄 Workflow Patterns

### **Linear Workflows**
```python
from langswarm.core.workflows.builder import LinearWorkflowBuilder

# Sequential processing
linear = (LinearWorkflowBuilder("document_processing")
    .then_agent("extract", "text_extractor", "${document}")
    .then_tool("validate", "text_validator", "${extract}")
    .then_agent("summarize", "summarizer", "${validate}")
    .then_transform("format", "${summarize}", format_summary)
    .build())
```

### **Parallel Workflows**
```python
from langswarm.core.workflows.builder import ParallelWorkflowBuilder

# Multiple parallel analyses
parallel = (ParallelWorkflowBuilder("multi_analysis")
    .add_parallel_group([
        ("sentiment", "sentiment_analyzer", "${text}"),
        ("topics", "topic_extractor", "${text}"),
        ("entities", "entity_recognizer", "${text}"),
        ("summary", "summarizer", "${text}")
    ])
    .then_agent("combine", "result_combiner", 
               "Combine results: sentiment=${sentiment}, topics=${topics}, entities=${entities}, summary=${summary}")
    .build())
```

### **Conditional Workflows**
```python
# Workflow with branching logic
conditional = (WorkflowBuilder("content_moderation")
    .add_agent_step("analyze", "content_analyzer", "Analyze: ${content}")
    .add_condition_step("safety_check", "${analyze.safety_score} >= 0.8", "approve", "review")
    
    # Approval path
    .add_agent_step("approve", "auto_approver", "Auto-approve: ${analyze}")
    
    # Review path  
    .add_agent_step("review", "human_reviewer", "Needs review: ${analyze}")
    .add_condition_step("final_decision", "${review.approved}", "publish", "reject")
    
    # Final steps
    .add_agent_step("publish", "publisher", "Publish: ${content}")
    .add_agent_step("reject", "notifier", "Notify rejection: ${content}")
    
    .build())
```

### **Analysis Workflows**
```python
# Data analysis pattern
analysis = (WorkflowBuilder("comprehensive_analysis")
    # Data preparation
    .add_tool_step("load", "data_loader", "${source}")
    .add_agent_step("clean", "data_cleaner", "Clean this data: ${load}")
    .add_transform_step("validate", "${clean}", validate_data)
    
    # Parallel analysis
    .add_parallel_group([
        ("stats", "statistician", "Calculate statistics: ${validate}"),
        ("insights", "insight_generator", "Generate insights: ${validate}"),
        ("anomalies", "anomaly_detector", "Detect anomalies: ${validate}")
    ])
    
    # Synthesis
    .add_agent_step("synthesize", "synthesizer", 
                   "Combine analysis: stats=${stats}, insights=${insights}, anomalies=${anomalies}")
    .add_transform_step("report", "${synthesize}", generate_report)
    
    .build())
```

---

## 🛠️ Working with Variables

### **Template Variables**
```python
# Define workflow variables
workflow = (WorkflowBuilder("templated_workflow")
    .add_variable("user_name", "John Doe")
    .add_variable("threshold", 0.8)
    .add_variable("output_format", "json")
    
    # Use variables in templates
    .add_agent_step("greet", "greeter", "Hello ${user_name}, how can I help?")
    .add_condition_step("check", "${score} >= ${threshold}", "proceed", "retry")
    .add_transform_step("format", "${result}", lambda r: format_output(r, "${output_format}"))
    
    .build())

# Override variables at execution
result = await execute_workflow("templated_workflow", {
    "input": "data",
    "user_name": "Jane Smith",  # Override default
    "threshold": 0.9            # Override default
})
```

### **Dynamic Variables**
```python
# Variables from previous steps
workflow = (WorkflowBuilder("dynamic_vars")
    .add_agent_step("analyze", "analyzer", "Analyze: ${input}")
    
    # Use result from previous step
    .add_agent_step("detailed", "detail_analyzer", 
                   "Detailed analysis of ${analyze.topic} with confidence ${analyze.confidence}")
    
    # Conditional based on previous results
    .add_condition_step("quality_gate", 
                       "${analyze.confidence} >= 0.8 and ${analyze.relevance} >= 0.7",
                       "proceed", "retry")
    
    .build())
```

### **Complex Variable Resolution**
```python
# Advanced template resolution
workflow = (WorkflowBuilder("complex_templates")
    .add_agent_step("multi_input", "processor", 
                   """Process the following:
                   Title: ${metadata.title}
                   Content: ${content}
                   Instructions: ${config.instructions}
                   Context: Previous analysis showed ${previous.summary}
                   """)
    .build())

# Execute with nested data
result = await execute_workflow("complex_templates", {
    "content": "Main content here",
    "metadata": {
        "title": "Document Analysis",
        "author": "AI System"
    },
    "config": {
        "instructions": "Be thorough and accurate"
    },
    "previous": {
        "summary": "Positive sentiment detected"
    }
})
```

---

## 🔍 Monitoring and Debugging

### **Real-time Monitoring**
```python
from langswarm.core.workflows import list_executions

# Monitor all running workflows
executions = list_executions(status="running")
for execution in executions:
    print(f"Workflow: {execution.workflow_id}")
    print(f"Execution ID: {execution.execution_id}")
    print(f"Started: {execution.start_time}")
    print(f"Current step: {execution.current_step}")
    print(f"Progress: {execution.completed_steps}/{execution.total_steps}")
    print("---")
```

### **Step-by-Step Debugging**
```python
# Get detailed execution information
result = await execute_workflow("debug_workflow", {"input": "test"})

print(f"Workflow Status: {result.status}")
print(f"Total Duration: {result.total_duration_ms}ms")
print()

# Analyze each step
for step_id, step_result in result.step_results.items():
    print(f"Step: {step_id}")
    print(f"  Type: {step_result.step_type}")
    print(f"  Status: {step_result.status}")
    print(f"  Duration: {step_result.duration_ms}ms")
    
    if step_result.result:
        print(f"  Result: {step_result.result}")
    
    if step_result.error:
        print(f"  Error: {step_result.error}")
    
    print()
```

### **Performance Analysis**
```python
from langswarm.core.workflows import get_workflow_metrics

# Get performance metrics
metrics = await get_workflow_metrics("analysis")

print(f"Workflow: {metrics.workflow_id}")
print(f"Total executions: {metrics.execution_count}")
print(f"Success rate: {metrics.success_rate:.2%}")
print(f"Average duration: {metrics.avg_duration_ms}ms")
print(f"Fastest execution: {metrics.min_duration_ms}ms")
print(f"Slowest execution: {metrics.max_duration_ms}ms")

# Step-level metrics
print("\nStep Performance:")
for step_id, step_metrics in metrics.step_metrics.items():
    print(f"  {step_id}:")
    print(f"    Success rate: {step_metrics.success_rate:.2%}")
    print(f"    Avg duration: {step_metrics.avg_duration_ms}ms")
    print(f"    Retry rate: {step_metrics.retry_rate:.2%}")
```

---

## 🚨 Error Handling

### **Error Recovery Strategies**
```python
# Configure error handling
workflow = (WorkflowBuilder("robust_workflow")
    .set_error_strategy("continue")     # Continue on step failures
    .set_retry_policy(
        max_retries=3,
        exponential_backoff=True,
        retry_delay=1.0
    )
    
    # Add error handling steps
    .add_agent_step("risky", "risky_agent", "${input}")
    .add_recovery_step("cleanup", cleanup_function)  # Run on failure
    
    .build())
```

### **Handling Failed Workflows**
```python
# Execute with error handling
result = await execute_workflow("robust_workflow", {"input": "test"})

if result.status == "failed":
    print(f"Workflow failed: {result.error}")
    
    # Analyze failures
    failed_steps = [
        step for step in result.step_results.values() 
        if step.status == "failed"
    ]
    
    for step in failed_steps:
        print(f"Failed step: {step.step_id}")
        print(f"Error: {step.error}")
        print(f"Retry count: {step.retry_count}")
        
        # Decide whether to retry
        if step.retry_count < 3:
            print(f"Retrying step {step.step_id}...")
            # Implement retry logic
```

### **Custom Error Handling**
```python
def custom_error_handler(step_result, context):
    """Custom error handling function"""
    if step_result.step_type == "agent" and "rate_limit" in step_result.error:
        # Wait and retry for rate limits
        return {"action": "retry", "delay": 60}
    elif step_result.step_type == "tool" and "network" in step_result.error:
        # Skip network errors and continue
        return {"action": "skip", "default_value": "network_unavailable"}
    else:
        # Fail for other errors
        return {"action": "fail"}

# Apply custom error handler
workflow = (WorkflowBuilder("custom_errors")
    .set_error_handler(custom_error_handler)
    .add_agent_step("step1", "agent1", "${input}")
    .add_tool_step("step2", "tool1", "${step1}")
    .build())
```

---

## 🧪 Testing Workflows

### **Mock Execution**
```python
from langswarm.core.workflows.testing import MockWorkflowEngine

# Create mock engine
mock_engine = MockWorkflowEngine()

# Configure mock responses
mock_engine.add_step_result("analyze", {
    "status": "completed",
    "result": "Analysis complete: positive sentiment",
    "duration_ms": 500
})

mock_engine.add_step_result("summarize", {
    "status": "completed", 
    "result": "Summary: Document shows positive sentiment and high quality",
    "duration_ms": 300
})

# Test workflow with mocks
result = await mock_engine.execute_workflow("test_workflow", {"input": "test"})
assert result.status == "completed"
assert "positive sentiment" in result.final_result
```

### **Validation Testing**
```python
from langswarm.core.workflows.validator import WorkflowValidator

# Validate workflow before execution
validator = WorkflowValidator()
validation_result = await validator.validate_workflow(workflow)

if validation_result.is_valid:
    print("✓ Workflow is valid")
else:
    print("✗ Validation errors:")
    for error in validation_result.errors:
        print(f"  - {error.message}")
        if error.step_id:
            print(f"    Step: {error.step_id}")
        if error.suggestion:
            print(f"    Suggestion: {error.suggestion}")
```

### **Integration Testing**
```python
import pytest

class TestWorkflowIntegration:
    async def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        workflow = create_analysis_workflow(
            workflow_id="test_analysis",
            data_extractor="extractor",
            analyzer="analyzer",
            validator="validator"
        )
        
        result = await execute_workflow("test_analysis", {
            "data": "Sample data for analysis"
        })
        
        assert result.status == "completed"
        assert result.final_result is not None
        assert result.total_duration_ms > 0
        
        # Check all steps completed
        for step_result in result.step_results.values():
            assert step_result.status == "completed"
    
    async def test_error_recovery(self):
        """Test workflow error recovery"""
        # Create workflow that will fail initially
        workflow = (WorkflowBuilder("error_test")
            .set_retry_policy(max_retries=2)
            .add_agent_step("failing", "nonexistent_agent", "${input}")
            .add_agent_step("backup", "working_agent", "${input}")
            .build())
        
        result = await execute_workflow("error_test", {"input": "test"})
        
        # Should recover with backup step
        assert result.status in ["completed", "partial"]
```

---

## 🔧 Best Practices

### **Workflow Design**
- **Keep steps focused**: Each step should have a single responsibility
- **Use clear naming**: Step IDs should be descriptive and meaningful
- **Design for failure**: Include error handling and recovery strategies
- **Optimize dependencies**: Minimize unnecessary step dependencies for better parallelization

### **Performance Optimization**
- **Use parallel execution**: When steps don't depend on each other
- **Set appropriate timeouts**: Prevent workflows from running indefinitely
- **Cache expensive operations**: Use result caching for costly computations
- **Monitor execution**: Track performance metrics to identify bottlenecks

### **Error Handling**
- **Plan for failures**: Consider what could go wrong at each step
- **Provide meaningful errors**: Include context and suggestions in error messages
- **Implement retries**: Use exponential backoff for transient failures
- **Design recovery paths**: Have backup strategies for critical failures

### **Testing Strategy**
- **Validate early**: Check workflow configuration before execution
- **Use mocks**: Test workflow logic without external dependencies
- **Test error scenarios**: Verify error handling and recovery work correctly
- **Monitor in production**: Track workflow performance and reliability

### **Security Considerations**
- **Validate inputs**: Ensure all workflow inputs are properly validated
- **Sanitize templates**: Be careful with variable substitution to prevent injection
- **Limit permissions**: Use least-privilege access for agents and tools
- **Log securely**: Avoid logging sensitive data in workflow traces

---

**LangSwarm V2 workflows provide a powerful, intuitive way to orchestrate complex multi-step processes with type safety, error recovery, and production-ready performance monitoring.**

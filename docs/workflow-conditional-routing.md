# Workflow Conditional Routing in LangSwarm

## Overview

LangSwarm provides powerful conditional routing capabilities within workflows, allowing dynamic step execution based on runtime conditions. This enables intelligent workflow paths that adapt to different scenarios and data conditions.

## Core Conditional Features

LangSwarm supports multiple conditional patterns:

1. **Output Conditional Routing** - Route to different steps based on conditions
2. **Step-Level Conditions** - Execute steps only when conditions are met
3. **Switch/Case Logic** - Multiple condition branches
4. **Exists Checks** - Route based on field presence

## 1. Output Conditional Routing

### Basic If/Then/Else Syntax

The most common pattern uses `if/then/else` logic in the `output` section:

```yaml
steps:
  - id: analyze_request
    agent: analyzer
    input: "${user_input}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.analyze_request.priority} == 'high'"
            then: escalate_immediately
            else: normal_processing
```

### Real-World Example: Security Routing

```yaml
steps:
  - id: initialize_request
    agent: security_scanner
    input: "${user_input}"
    output:
      to: process_request

  - id: process_request
    agent: request_processor
    input: "${context.step_outputs.initialize_request}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.initialize_request.suspicious_warning} != None"
            then: send_security_warning
            else: check_validation

  - id: send_security_warning
    agent: security_handler
    input: |
      Security Warning: ${context.step_outputs.initialize_request.suspicious_warning}
      Original Request: ${user_input}
    output:
      to: user

  - id: check_validation
    agent: validator
    input: "${context.step_outputs.initialize_request}"
    output:
      to: user
```

## 2. Multiple Condition Checks

### Complex Conditional Logic

```yaml
steps:
  - id: classify_customer
    agent: customer_classifier
    input: "${user_input}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.classify_customer.tier} == 'premium' && ${context.step_outputs.classify_customer.issue_type} == 'technical'"
            then: premium_technical_support
            else: standard_routing

  - id: standard_routing
    agent: router
    input: "${context.step_outputs.classify_customer}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.classify_customer.tier} == 'premium'"
            then: premium_support
            else: general_support
```

### String Contains Checks

```yaml
steps:
  - id: analyze_intent
    agent: intent_analyzer
    input: "${user_input}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.analyze_intent.category} contains 'billing'"
            then: billing_workflow
            else: technical_workflow
```

## 3. Switch/Case Logic

For multiple discrete options, use switch/case patterns:

```yaml
steps:
  - id: categorize_request
    agent: categorizer
    input: "${user_input}"
    output:
      to:
        - condition:
            switch: "${context.step_outputs.categorize_request.category}"
            cases:
              technical: technical_support
              billing: billing_support
              sales: sales_team
              general: general_inquiry
            default: fallback_handler
```

## 4. Exists Checks

Route based on field presence:

```yaml
steps:
  - id: extract_user_data
    agent: data_extractor
    input: "${user_input}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.extract_user_data.user_id} exists"
            then: authenticated_flow
            else: guest_flow
```

## 5. Step-Level Conditions

Execute steps only when conditions are met:

```yaml
steps:
  - id: basic_processing
    agent: processor
    input: "${user_input}"
    output:
      to: check_premium

  - id: premium_enhancement
    condition: "${context.step_outputs.basic_processing.user_tier} == 'premium'"
    agent: premium_processor
    input: "${context.step_outputs.basic_processing}"
    output:
      to: finalize

  - id: check_premium
    agent: tier_checker
    input: "${context.step_outputs.basic_processing}"
    output:
      to: finalize

  - id: finalize
    agent: finalizer
    input: |
      Basic: ${context.step_outputs.basic_processing}
      Premium: ${context.step_outputs.premium_enhancement}
    output:
      to: user
```

## 6. Advanced Conditional Operators

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equals | `"${value} == 'expected'"` |
| `!=` | Not equals | `"${value} != None"` |
| `>` | Greater than | `"${score} > 0.8"` |
| `<` | Less than | `"${priority} < 5"` |
| `>=` | Greater than or equal | `"${count} >= 10"` |
| `<=` | Less than or equal | `"${risk} <= 0.3"` |
| `contains` | String contains | `"${text} contains 'error'"` |
| `not contains` | String doesn't contain | `"${status} not contains 'failed'"` |
| `in` | Value in list | `"${category} in ['urgent', 'high']"` |
| `exists` | Field exists | `"${field} exists"` |
| `not exists` | Field doesn't exist | `"${optional_field} not exists"` |

### Logical Operators

```yaml
# AND condition
condition:
  if: "${priority} == 'high' && ${user_tier} == 'premium'"
  then: vip_escalation
  else: standard_flow

# OR condition  
condition:
  if: "${status} == 'failed' || ${errors} > 0"
  then: error_handling
  else: success_flow

# Complex logic
condition:
  if: "(${priority} == 'critical' || ${user_tier} == 'enterprise') && ${business_hours} == true"
  then: immediate_response
  else: queue_for_later
```

## 7. Context Variable References

### Accessing Step Outputs

```yaml
# Previous step output
"${context.step_outputs.step_id.field_name}"

# Nested field access
"${context.step_outputs.analyzer.result.confidence_score}"

# Array access (if supported)
"${context.step_outputs.classifier.categories[0]}"
```

### Accessing Input Variables

```yaml
# User input
"${user_input}"

# User query (alternative input)
"${user_query}"

# Context data
"${context.user_id}"
"${context.session_data.preferences}"
```

## 8. Error Handling with Conditions

### Graceful Error Routing

```yaml
steps:
  - id: risky_operation
    agent: risky_processor
    input: "${user_input}"
    output:
      to:
        - condition:
            if: "${context.step_outputs.risky_operation.error} exists"
            then: handle_error
            else: process_success

  - id: handle_error
    agent: error_handler
    input: |
      Error: ${context.step_outputs.risky_operation.error}
      Original Input: ${user_input}
    output:
      to: user

  - id: process_success
    agent: success_processor
    input: "${context.step_outputs.risky_operation.result}"
    output:
      to: user
```

## 9. Best Practices

### 1. Keep Conditions Simple and Readable

✅ **Good:**
```yaml
condition:
  if: "${priority} == 'high'"
  then: escalate
  else: normal_flow
```

❌ **Avoid:**
```yaml
condition:
  if: "${(priority == 'high' || (priority == 'medium' && user_tier == 'premium' && business_hours == true)) && !maintenance_mode}"
  then: complex_logic
```

### 2. Use Descriptive Step Names

✅ **Good:**
```yaml
then: escalate_to_senior_support
else: route_to_standard_queue
```

❌ **Avoid:**
```yaml
then: step_a
else: step_b
```

### 3. Handle Edge Cases

```yaml
condition:
  if: "${context.step_outputs.classifier.confidence} exists && ${context.step_outputs.classifier.confidence} > 0.8"
  then: high_confidence_flow
  else: manual_review_flow
```

### 4. Use Default Cases in Switch Logic

```yaml
condition:
  switch: "${category}"
  cases:
    technical: tech_support
    billing: billing_team
    sales: sales_team
  default: general_inquiry  # Always provide a default
```

## 10. Common Patterns

### Pattern 1: Priority-Based Routing

```yaml
- id: analyze_priority
  agent: priority_analyzer
  input: "${user_input}"
  output:
    to:
      - condition:
          switch: "${context.step_outputs.analyze_priority.level}"
          cases:
            critical: immediate_escalation
            high: senior_agent
            medium: standard_agent
            low: self_service
          default: standard_agent
```

### Pattern 2: User Tier Routing

```yaml
- id: check_user_tier
  agent: user_service
  input: "${user_input}"
  output:
    to:
      - condition:
          if: "${context.step_outputs.check_user_tier.tier} in ['enterprise', 'premium']"
          then: premium_service
          else: standard_service
```

### Pattern 3: Validation Flow

```yaml
- id: validate_input
  agent: validator
  input: "${user_input}"
  output:
    to:
      - condition:
          if: "${context.step_outputs.validate_input.valid} == true"
          then: process_request
          else: request_clarification
```

### Pattern 4: Retry Logic

```yaml
- id: attempt_operation
  agent: processor
  input: "${user_input}"
  output:
    to:
      - condition:
          if: "${context.step_outputs.attempt_operation.success} == true"
          then: success_handler
          else: retry_or_fail

- id: retry_or_fail
  agent: retry_manager
  input: "${context.step_outputs.attempt_operation}"
  output:
    to:
      - condition:
          if: "${context.step_outputs.attempt_operation.retry_count} < 3"
          then: attempt_operation
          else: failure_handler
```

## 11. Debugging Conditional Logic

### Add Logging Steps

```yaml
- id: debug_condition
  agent: debug_logger
  input: |
    Condition Check:
    - Priority: ${context.step_outputs.analyzer.priority}
    - User Tier: ${context.step_outputs.analyzer.user_tier}
    - Decision: Will route to ${condition_result}
  output:
    to: actual_routing_step
```

### Test with Known Values

```yaml
# Test step to verify condition logic
- id: test_conditions
  agent: test_agent
  input: |
    Testing conditions with:
    - priority = "high"
    - user_tier = "premium"
    
    Expected route: vip_escalation
  output:
    to:
      - condition:
          if: "${priority} == 'high' && ${user_tier} == 'premium'"
          then: vip_escalation
          else: standard_flow
```

## 12. Performance Considerations

1. **Simple Conditions First**: Place simple conditions before complex ones
2. **Avoid Deep Nesting**: Use multiple steps instead of deeply nested conditions
3. **Cache Expensive Checks**: Store results of expensive condition checks in step outputs
4. **Use Appropriate Data Types**: Ensure consistent data types in comparisons

## Summary

LangSwarm's conditional routing provides powerful flow control within workflows:

- **`if/then/else`** for basic branching
- **`switch/case`** for multiple discrete options  
- **Step-level conditions** for conditional execution
- **Rich operators** for complex logic
- **Context access** to previous step outputs
- **Error handling** patterns for robust workflows

This enables building sophisticated, adaptive workflows that respond intelligently to runtime conditions and data.

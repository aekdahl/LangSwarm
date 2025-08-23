# Navigation Configuration Schema

## Overview

The LangSwarm intelligent navigation system uses a comprehensive configuration schema to define navigation-enabled workflows. This schema provides validation, type safety, and documentation for navigation configurations.

## Schema Structure

### Core Configuration Fields

```yaml
mode: manual | conditional | hybrid | weighted
available_steps: []
rules: []              # Optional
fallback_step: string  # Optional
timeout_seconds: 30
max_attempts: 3
tracking_enabled: true
analytics_enabled: true
prompt_template: string  # Optional
metadata: {}           # Optional
```

### Navigation Modes

#### Manual Mode
Agent chooses from available steps based on context and reasoning.

```yaml
mode: manual
available_steps:
  - id: process_request
    name: Process Request
    description: Handle the user request normally
  - id: escalate_to_human
    name: Escalate to Human
    description: Route complex issues to human support
```

#### Conditional Mode
Routing based purely on rules and conditions.

```yaml
mode: conditional
rules:
  - conditions:
      - field: output.priority
        operator: eq
        value: critical
    target_step: escalate_immediately
    priority: 10
```

#### Hybrid Mode
Combines conditional rules with agent choice.

```yaml
mode: hybrid
available_steps: [...]
rules:
  - conditions: [...]
    target_step: auto_escalate
    priority: 10
```

#### Weighted Mode
Probabilistic selection based on step weights.

```yaml
mode: weighted
available_steps:
  - id: automated_resolution
    name: Automated Resolution
    description: Try automated resolution first
    weight: 3.0  # Higher probability
  - id: human_support
    name: Human Support
    description: Route to human agent
    weight: 1.0  # Lower probability
```

## Available Steps Configuration

### Basic Step Definition

```yaml
available_steps:
  - id: step_identifier          # Required: unique step ID
    name: Human Readable Name     # Required: display name
    description: Detailed description for agent context  # Required
    conditions: []               # Optional: availability conditions
    weight: 1.0                  # Optional: selection weight
    metadata: {}                 # Optional: additional data
```

### Step Conditions

Steps can have conditions that determine when they're available:

```yaml
conditions:
  - field: output.category        # Field path to evaluate
    operator: eq                  # Comparison operator
    value: technical             # Value to compare against
    description: Issue is technical  # Optional: human description
```

### Supported Operators

- **`eq`**: Equals
- **`ne`**: Not equals
- **`gt`**: Greater than
- **`lt`**: Less than
- **`gte`**: Greater than or equal
- **`lte`**: Less than or equal
- **`contains`**: String contains value
- **`not_contains`**: String does not contain value
- **`in`**: Value is in list
- **`not_in`**: Value is not in list
- **`exists`**: Field exists
- **`not_exists`**: Field does not exist
- **`regex`**: Regular expression match
- **`starts_with`**: String starts with value
- **`ends_with`**: String ends with value

### Field Path Examples

```yaml
# Simple field access
field: category

# Nested object access
field: output.category

# Deep nesting
field: analysis.sentiment.score

# Array access (if supported by implementation)
field: tags[0]
```

## Conditional Rules

Rules enable automatic routing based on conditions:

```yaml
rules:
  - conditions:
      - field: output.priority
        operator: eq
        value: critical
      - field: output.customer_tier
        operator: eq
        value: premium
    target_step: vip_escalation
    priority: 10
    description: VIP customers with critical issues get immediate escalation
```

### Rule Priority

Rules are evaluated in priority order (highest first):

```yaml
rules:
  - priority: 10    # Evaluated first
    conditions: [...]
    target_step: critical_escalation
    
  - priority: 5     # Evaluated second
    conditions: [...]
    target_step: normal_routing
    
  - priority: 1     # Evaluated last
    conditions: [...]
    target_step: default_handling
```

## Configuration Examples

### Basic Customer Support

```yaml
mode: manual
available_steps:
  - id: technical_support
    name: Technical Support
    description: Route to technical support team
    
  - id: billing_support
    name: Billing Support
    description: Route to billing department
    
  - id: general_inquiry
    name: General Inquiry
    description: Handle general questions

fallback_step: general_inquiry
timeout_seconds: 30
tracking_enabled: true
```

### Advanced Support with Conditions

```yaml
mode: hybrid
available_steps:
  - id: technical_support
    name: Technical Support
    description: Route technical issues to specialized team
    conditions:
      - field: output.category
        operator: eq
        value: technical
    weight: 1.5
    
  - id: billing_support
    name: Billing Support
    description: Handle billing and payment issues
    conditions:
      - field: output.category
        operator: eq
        value: billing
      - field: output.complexity
        operator: lte
        value: 0.7
        
  - id: escalation
    name: Escalate to Manager
    description: Route complex issues to management
    conditions:
      - field: output.complexity
        operator: gt
        value: 0.8

rules:
  - conditions:
      - field: output.priority
        operator: eq
        value: critical
    target_step: escalation
    priority: 10
    description: Auto-escalate critical issues

fallback_step: technical_support
timeout_seconds: 45
prompt_template: |
  Select the best support channel based on:
  {context}
  
  Available channels: {available_steps}
```

### E-commerce Routing

```yaml
mode: weighted
available_steps:
  - id: order_status
    name: Order Status
    description: Check order status and shipping
    conditions:
      - field: output.intent
        operator: contains
        value: order
    weight: 2.0
    metadata:
      department: fulfillment
      
  - id: product_support
    name: Product Support
    description: Product questions and returns
    conditions:
      - field: output.intent
        operator: contains
        value: product
    weight: 1.5
    metadata:
      department: support
      
  - id: sales_inquiry
    name: Sales Inquiry
    description: Pre-purchase questions
    weight: 1.0
    metadata:
      department: sales

rules:
  - conditions:
      - field: output.customer_tier
        operator: eq
        value: vip
    target_step: order_status
    priority: 8
    description: VIP customers get priority order support

fallback_step: sales_inquiry
metadata:
  use_case: ecommerce
  departments: [fulfillment, support, sales]
```

## Programmatic Configuration

### Using the Builder API

```python
from langswarm.features.intelligent_navigation.schema import create_navigation_config

config = (create_navigation_config()
          .set_mode("hybrid")
          .add_condition_step(
              "technical_support",
              "Technical Support", 
              "Handle technical issues",
              "output.category", "eq", "technical"
          )
          .add_step(
              "general_support",
              "General Support",
              "Handle general inquiries"
          )
          .set_fallback("general_support")
          .set_timeout(30)
          .build())

# Export as YAML or JSON
yaml_config = config.to_yaml()
json_config = config.to_json()
```

### Loading and Validating

```python
from langswarm.features.intelligent_navigation.schema import load_navigation_config, validate_navigation_config

# Load from file
config = load_navigation_config("navigation_config.yaml")

# Validate dictionary
config_dict = {...}
validate_navigation_config(config_dict)  # Raises error if invalid
```

### Configuration Utilities

```python
from langswarm.features.intelligent_navigation.config_utils import *

# Generate templates
basic_template = generate_config_template("basic")
ecommerce_template = generate_config_template("ecommerce")

# Validate files
result = validate_config_file("my_config.yaml")
print(f"Valid: {result['valid']}")

# Convert formats
convert_config_format("config.yaml", "config.json")

# Get configuration summary
summary = get_config_summary("config.yaml")
print(f"Complexity: {summary['complexity']}")
```

## Validation

### Schema Validation

All configurations are validated against a JSON schema:

```python
from langswarm.features.intelligent_navigation.schema import NavigationSchemaValidator

validator = NavigationSchemaValidator()
validator.validate(config_dict)  # Raises ValidationError if invalid
```

### Common Validation Errors

#### Missing Required Fields
```
Navigation configuration validation failed: 'available_steps' is a required property
```

#### Invalid Step ID Format
```
Step ID must match pattern: ^[a-zA-Z][a-zA-Z0-9_-]*$
```

#### Invalid Operator
```
'invalid_op' is not one of ['eq', 'ne', 'gt', 'lt', ...]
```

#### Circular References
```
Fallback step 'step_a' creates circular reference
```

## Best Practices

### Step Design

1. **Clear IDs**: Use descriptive, consistent step identifiers
2. **Detailed Descriptions**: Provide context for agent decision-making
3. **Logical Conditions**: Use conditions that clearly define when steps apply
4. **Appropriate Weights**: Balance weights for optimal routing distribution

### Rule Design

1. **Priority Ordering**: Higher priority for more specific/important rules
2. **Condition Clarity**: Make conditions explicit and easy to understand
3. **Rule Documentation**: Include descriptions explaining rule purpose
4. **Avoid Conflicts**: Ensure rules don't create contradictory routing

### Performance Optimization

1. **Reasonable Timeouts**: Balance decision quality with response time
2. **Condition Efficiency**: Use efficient field paths and operators
3. **Step Count**: Limit available steps to manageable numbers (3-8 typical)
4. **Rule Complexity**: Keep rule conditions simple and fast to evaluate

### Configuration Management

1. **Version Control**: Track configuration changes in version control
2. **Environment Separation**: Use different configs for dev/staging/prod
3. **Validation Pipeline**: Validate configurations in CI/CD
4. **Documentation**: Document configuration decisions and changes

## Schema Reference

### Complete JSON Schema

The full JSON schema is available programmatically:

```python
from langswarm.features.intelligent_navigation.schema import get_navigation_schema

schema = get_navigation_schema()
```

### Configuration Templates

Built-in templates are available in the `templates/` directory:

- **`basic_navigation.yaml`**: Simple manual routing
- **`conditional_navigation.yaml`**: Advanced rule-based routing  
- **`weighted_navigation.yaml`**: Probabilistic routing

### Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mode` | string | No | `"manual"` | Navigation decision mode |
| `available_steps` | array | Yes | - | List of navigation target steps |
| `rules` | array | No | `[]` | Conditional routing rules |
| `fallback_step` | string | No | `null` | Default step when no options available |
| `timeout_seconds` | integer | No | `30` | Maximum decision time (1-300) |
| `max_attempts` | integer | No | `3` | Maximum retry attempts (1-10) |
| `tracking_enabled` | boolean | No | `true` | Enable decision tracking |
| `analytics_enabled` | boolean | No | `true` | Enable analytics collection |
| `prompt_template` | string | No | `null` | Custom agent prompt template |
| `metadata` | object | No | `{}` | Additional configuration metadata |

This schema system provides the foundation for robust, validated navigation configurations that can evolve with changing requirements while maintaining compatibility and type safety. 
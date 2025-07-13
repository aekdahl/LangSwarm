# Navigation Tool Response Format Standards

## Overview

The intelligent navigation system follows LangSwarm's standard response format to ensure consistency across all tools and integrations.

## Agent Output Format

When an agent needs to navigate to the next workflow step, it outputs the standard LangSwarm tool format:

```json
{
  "response": "I'll route this to technical support since this is an API authentication issue that requires specialized expertise",
  "tool": "navigate_workflow",
  "args": {
    "step_id": "technical_support",
    "reasoning": "API authentication issue requires technical expertise",
    "confidence": 0.9
  }
}
```

### Fields Explanation

- **`response`** (required): Human-readable explanation of the navigation decision
- **`tool`** (required): Must be `"navigate_workflow"` for navigation
- **`args`** (required): Navigation parameters
  - **`step_id`** (required): ID of the step to navigate to
  - **`reasoning`** (required): Explanation for the choice
  - **`confidence`** (optional): Confidence level (0.0-1.0, defaults to 1.0)

## Navigation Tool Response Format

The navigation tool returns responses in the standard LangSwarm format:

```json
{
  "response": "Successfully navigating to step 'technical_support'. API authentication issue requires technical expertise",
  "tool": {
    "status": "success",
    "chosen_step": "technical_support",
    "reasoning": "API authentication issue requires technical expertise",
    "confidence": 0.9,
    "navigation_choice": {
      "step_id": "technical_support",
      "reasoning": "API authentication issue requires technical expertise",
      "confidence": 0.9,
      "metadata": {},
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

### Standard Fields

- **`response`**: User-facing message about the navigation result
- **`tool`**: Tool-specific data containing navigation results

## Error Response Format

When navigation fails, the tool returns:

```json
{
  "response": "Navigation failed - 'invalid_step' is not available. Available steps: technical_support, billing_support, general_inquiry",
  "tool": {
    "status": "error",
    "error": "Invalid step 'invalid_step'. Available steps: technical_support, billing_support, general_inquiry"
  }
}
```

## Fallback Mechanisms

The navigation system provides multiple fallback layers:

### 1. Step Validation
- Validates `step_id` against available steps
- Returns error with available options if invalid

### 2. Configuration Fallback
- Uses `fallback_step` from navigation configuration
- Triggered when no valid steps are available

### 3. Timeout Handling
- Uses `fallback_step` if agent doesn't respond within `timeout_seconds`
- Configurable via `timeout_seconds` parameter

### 4. Conditional Override
- High-priority rules can override agent decisions
- Example: Critical issues auto-route to escalation

## Usage Examples

### Basic Navigation
```yaml
navigation:
  available_steps:
    - id: "technical_support"
      name: "Technical Support"
      description: "Route to technical support"
  fallback_step: "general_inquiry"
```

### Conditional Navigation
```yaml
navigation:
  rules:
    - conditions:
        - field: "output.priority"
          operator: "eq"
          value: "critical"
      target_step: "escalate_to_human"
      priority: 10
```

## Integration Notes

- The navigation tool is a **regular LangSwarm tool**, not an MCP tool
- Agents automatically get the `navigate_workflow` tool when used in navigation-enabled steps
- All responses follow the standard `{response, tool}` structure

## Best Practices

1. **Always provide clear reasoning** in agent responses
2. **Use descriptive step IDs** for better debugging
3. **Set appropriate confidence levels** based on decision certainty
4. **Configure fallback steps** for robust error handling
5. **Use conditional rules** for automatic routing when appropriate 
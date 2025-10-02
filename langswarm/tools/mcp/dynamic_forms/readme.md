# Dynamic Forms MCP Tool

A powerful tool for generating dynamic configuration forms based on user-defined YAML schemas. This tool allows users to define their own forms in their main `tools.yaml` configuration file, making them fully customizable and editable.

## Key Features

- **User-Configurable**: Forms are defined in your main `tools.yaml` file, not hardcoded
- **Multiple Field Types**: Support for text, email, number, select, multiselect, toggle, slider, and textarea
- **Flexible Filtering**: Include/exclude specific fields dynamically
- **Pre-population**: Load current settings to pre-fill form values
- **JSON Schema Output**: Pure JSON schemas for frontend rendering

## Configuration

### 1. Add Tool to Your tools.yaml

```yaml
tools:
  - id: dynamic-forms
    type: mcpforms
    description: "Dynamic forms tool"
    local_mode: true
    pattern: "direct"
    methods:
      - generate_form_schema: "Generate form schema from configuration"
      - get_available_forms: "List all available form types"
      - get_form_definition: "Get raw form definition"
    
    # Define your custom forms here
    forms:
      settings:
        title: "User Settings"
        description: "Basic user preferences"
        fields:
          - id: display_name
            label: "Display Name"
            type: text
            required: true
            placeholder: "Enter your name"
          
          - id: theme
            label: "Theme"
            type: select
            default_value: "auto"
            options:
              - value: "light"
                label: "Light"
              - value: "dark"
                label: "Dark"
              - value: "auto"
                label: "Auto"
```

### 2. Supported Field Types

- **text**: Text input with optional min/max length, pattern validation
- **email**: Email input with validation
- **password**: Password input with optional min/max length
- **number**: Numeric input with min/max values, step, and unit
- **select**: Dropdown selection with options
- **multiselect**: Multiple selection with options
- **toggle**: Boolean toggle switch
- **slider**: Range slider with min/max/step values
- **textarea**: Multi-line text input

### 3. Field Properties

Common properties for all field types:
- `id`: Unique field identifier (required)
- `label`: Display label (required)
- `type`: Field type (required)
- `required`: Whether field is mandatory
- `default_value`: Default/initial value
- `help_text`: Help text displayed below field
- `placeholder`: Placeholder text for input fields

Type-specific properties:
- Text fields: `min_length`, `max_length`, `pattern`
- Number fields: `min_value`, `max_value`, `step`, `unit`
- Select fields: `options` (array of value/label pairs)
- Slider fields: `min_value`, `max_value`, `step`, `unit`
- Textarea fields: `rows`

## Usage

### Generate a Form Schema

```python
from langswarm.mcp.tools.dynamic_forms.main import generate_form_schema

# Generate form schema for "settings" form
result = generate_form_schema(
    form_type="settings",
    user_context={"config_path": "/path/to/your/tools.yaml"},
    included_fields=["display_name", "theme"],  # Optional filtering
    current_settings={"display_name": "John Doe"}  # Pre-populate values
)

print(result["form_schema"])
```

### Available Methods

1. **generate_form_schema**: Generate complete form schema
2. **get_available_forms**: List all configured form types  
3. **get_form_definition**: Get raw form definition

## Environment Variables

- `LANGSWARM_CONFIG_PATH`: Path to your main tools.yaml file

## Example Complete Configuration

See `example_mcp_config/tools.yaml` for a complete example with multiple form types including:
- User settings form
- AI configuration form  
- System administration form

## Migration from Previous Version

If you were using the previous version with hardcoded forms:

1. Copy your form definitions from the old internal `tools.yaml`
2. Add them to your main `tools.yaml` under the `forms` section
3. Update any references to use the new form names
4. The tool will automatically load from your configuration

## Benefits of User Configuration

- **Fully Editable**: Modify forms without touching source code
- **Project-Specific**: Different forms for different projects
- **Version Controlled**: Forms are part of your project configuration
- **No Library Rebuilds**: Changes take effect immediately
- **Complete Control**: Define exactly the forms you need 
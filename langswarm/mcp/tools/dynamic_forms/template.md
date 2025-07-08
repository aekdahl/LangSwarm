# Dynamic Forms MCP Tool Template

## Description

Generate dynamic configuration forms based on user-defined YAML schemas. This tool loads form definitions from the user's main tools.yaml configuration file and creates JSON schemas for frontend rendering. Supports multiple field types, filtering, and pre-population of values.

## Instructions

**Tool Type**: Direct method calls, workflow orchestration, AND intent-based calls
**Tool ID**: dynamic-forms

### Methods Available:
- **generate_form_schema**: Generate complete form schema from configuration
- **get_available_forms**: List all configured form types  
- **get_form_definition**: Get raw form definition for specific type

### Workflow Support:
This tool supports workflow orchestration through defined workflows in workflows.yaml:
- **generate_form_schema** workflow: Full form generation with validation, filtering, and population steps
- **get_available_forms** workflow: Extract available form types from user configuration
- **get_form_definition** workflow: Load specific form definition

### How to Use:
**For Direct Calls**: Call generate_form_schema method with specific parameters directly.
**For Workflows**: Trigger workflows with structured input parameters - workflows orchestrate validation, configuration loading, filtering, and schema generation through multiple agents.
**For Intent-Based**: Describe what you want to accomplish in natural language (e.g., "create a user settings form with only name and email fields", "generate a configuration form for the admin panel"). The system will parse your intent and route to appropriate workflows with extracted parameters.

Forms must be defined in the user's main tools.yaml file under the 'forms' section of the dynamic-forms tool configuration.

### Parameters (for direct calls and workflows):
- **form_type** (required): Must match a form defined in user's configuration
- **user_context** (optional): Can include config_path for custom configuration location
- **included_fields** (optional): Array of field IDs to include (filters to show only these fields)
- **excluded_fields** (optional): Array of field IDs to exclude (hides these fields)
- **current_settings** (optional): Object with field values for pre-population

### Intent-Based Examples:
- "Create a settings form with just the basic fields"
- "Generate a form schema for user preferences excluding the advanced options"
- "I need a configuration form for the admin panel with all fields pre-populated"
- "Show me a form for editing user profiles but hide the password fields"

### Usage Context:
- Use when you need to create configuration forms or UI forms
- Use when generating form schemas for frontend applications
- Use when user has defined forms in their tools.yaml configuration
- Use when you need to filter specific fields or pre-populate form values
- Use workflows for complex orchestration with validation and error handling
- Use direct calls for simple, immediate form schema generation
- Use intent-based calls for natural language form generation requests

### Supported Field Types:
- text, email, password, number, select, multiselect, toggle, slider, textarea

### Output:
Returns JSON schema with form structure, fields, validation rules, and metadata suitable for frontend form rendering.

### Limitations:
- Forms must be predefined in user's tools.yaml configuration
- Cannot create new form types dynamically
- Field types are limited to the supported set
- Workflow orchestration requires proper agent configuration
- Intent-based calls require natural language processing and intent recognition

## Brief

Dynamic forms from user config 
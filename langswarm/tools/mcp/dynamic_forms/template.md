# Dynamic Forms Tool

## Description

Intelligent form generation with natural language specification for creating user input interfaces, surveys, and data collection forms.

## Instructions

This tool provides form creation with two calling approaches:

### Intent-Based Calling (Smart Form Generation)

Use **`dynamic_forms`** with natural language intent to generate forms from descriptions:

**Parameters:**
- `intent`: What kind of form you need
- `context`: Relevant details (use case, required fields, validation rules)

**When to use:**
- Creating forms from description: "Build a customer feedback form"
- Complex forms: "Multi-step registration with validation"
- Survey generation: "Employee satisfaction survey"
- Rapid prototyping: "Simple contact form"

**Examples:**
- "Create customer feedback form" → intent="create a customer feedback form for our mobile app with rating and comments", context="user experience, app improvement"
- "Build signup form" → intent="create enterprise customer sign-up form with company details", context="B2B registration, validation required"

### Direct Method Calling (Specific Form Operations)

**`dynamic_forms.create_form`** - Generate form structure
- **Parameters:** fields (array of field definitions), validation_rules
- **Use when:** You have exact field specifications

**`dynamic_forms.validate_form`** - Validate form data
- **Parameters:** form_id, data (submitted values)
- **Use when:** Processing form submissions

**`dynamic_forms.process_submission`** - Handle form submission
- **Parameters:** form_id, submission_data, actions (what to do with data)
- **Use when:** Processing completed forms

**`dynamic_forms.generate_fields`** - Create field definitions
- **Parameters:** field_types (list), requirements
- **Use when:** Building forms programmatically

### Decision Guide

**Use intent-based** when:
- User describes form requirements
- Quick form generation needed
- Complex validation logic
- Form type familiar (signup, feedback, contact)

**Use direct methods** when:
- Exact field specifications available
- Processing existing forms
- Validating submissions
- Programmatic form building

### Supported Field Types

- Text inputs (short/long)
- Number inputs (integers/decimals)
- Email and URL validation
- Date and time pickers
- Dropdowns and checkboxes
- File uploads
- Multi-select options
- Rating scales

### Common Use Cases

1. **User feedback**: Intent-based → generates rating, comments, satisfaction
2. **Registration forms**: Intent-based → creates appropriate fields
3. **Data validation**: validate_form with submission data
4. **Custom forms**: create_form with exact field specs

## Brief

Dynamic form generation with intelligent intent processing for user input and data collection.

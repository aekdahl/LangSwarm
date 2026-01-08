
# Intent-Based Tool Execution
You have access to tools that support high-level "intents". Instead of micromanaging every parameter, you can provide a natural language `intent` to the tool.

## Usage
When invoking such tools, you can pass an `intent` field describing what you want to achieve.
Example: `{"tool": "filesystem", "intent": "Read the configuration for the staging environment"}`.
The tool will analyze your intent and execute the necessary steps.

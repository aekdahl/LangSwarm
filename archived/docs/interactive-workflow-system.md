# Interactive Workflow System

🚀 **A comprehensive make command system that allows users to interactively select workflows, enter queries, and execute them with ease.**

## 📋 Overview

The Interactive Workflow System provides a user-friendly command-line interface for discovering, selecting, and running LangSwarm workflows. It automatically discovers all available workflows in your project and presents them in an organized, searchable format.

## 🎯 Key Features

### ✨ Interactive Workflow Selection
- **Automatic Discovery**: Finds all workflow configurations across your project
- **Categorized Browsing**: Groups workflows by type (Agent-based, BigQuery, Filesystem, etc.)
- **Search & Filter**: Easy navigation through available workflows
- **Detailed Previews**: View workflow structure and requirements before execution

### 🔧 Make Commands
- **Simple Interface**: Easy-to-remember make commands
- **Query Input**: Interactive prompts for user input and queries
- **Debug Mode**: Built-in debugging and tracing capabilities
- **Preset Workflows**: Quick access to common workflow types

### 🎨 User Experience
- **Colorized Output**: Clear, color-coded terminal interface
- **Progress Feedback**: Real-time execution status
- **Error Handling**: Graceful error messages and recovery
- **Help System**: Comprehensive help and usage examples

## 🚀 Quick Start

### 1. Setup Environment
```bash
make setup
```
This will:
- Install LangSwarm dependencies
- Configure API keys
- Verify installation

### 2. Run Interactive Workflow
```bash
make run-workflow
```
This launches the interactive workflow selection interface where you can:
1. Browse available workflows by category
2. Select a workflow
3. Enter your query/input
4. Execute and see results

### 3. List Available Workflows
```bash
make list-workflows
```
Shows all discovered workflows organized by category.

## 📚 Available Commands

### Core Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make run-workflow` | Interactive workflow selection and execution | Primary interface |
| `make list-workflows` | Show all available workflows | Discovery |
| `make debug-workflow` | Run workflows with debug tracing | Development |
| `make create-workflow` | AI-powered workflow generation | Creation |

### Quick Presets

| Command | Description |
|---------|-------------|
| `make workflow-bigquery` | Run BigQuery analysis workflows |
| `make workflow-filesystem` | Run filesystem operation workflows |
| `make workflow-memory` | Run memory demonstration workflows |

### Management Commands

| Command | Description |
|---------|-------------|
| `make validate-workflow` | Validate workflow configurations |
| `make setup` | Setup environment and dependencies |
| `make clean` | Clean debug traces and temporary files |

### Advanced Commands

| Command | Description |
|---------|-------------|
| `make debug-cases` | Run debug test cases |
| `make nav-analytics` | Show navigation analytics |
| `make memory-stats` | Show memory system statistics |
| `make test` | Run test suite |

## 🔍 Workflow Discovery

The system automatically discovers workflows from:

### 📁 Search Locations
- `langswarm/core/debug/test_configs/*.yaml` - Debug test configurations

### 🏷️ Workflow Categories
- **Debug Test Workflows** - Specialized workflows for testing and debugging LangSwarm components
- **BigQuery Debug** - BigQuery vector search testing workflows
- **Agent Debug** - Agent behavior testing workflows
- **Tool Debug** - MCP tool testing workflows

## 🎮 Interactive Interface

### Main Menu Options
```
🚀 LangSwarm Interactive Workflow Runner
==================================================

Main Menu:
  1 - 🎯 Select and run a workflow
  2 - ✨ Create a new workflow (AI-powered)
  3 - 📋 List all available workflows
  4 - ⚡ Run a preset workflow
  5 - 🔍 View workflow details
  q - 🚪 Quit
```

### Workflow Selection Example
```
🎯 Select a Workflow to Run
========================================

BigQuery Workflows:
  1. bigquery_debug_workflow (bigquery_debug.yaml)
     BigQuery Debug Workflow

Select workflow number (1): 
```

### Query Input
```
🚀 Running Workflow: bigquery_debug_workflow
==================================================
Description: BigQuery Debug Workflow
File: langswarm/core/debug/test_configs/bigquery_debug.yaml

Enter your query or input for this workflow:
(This will be passed as the user_input to the workflow)
Your query: Execute list_datasets using the bigquery_search tool
```

## 🐛 Debug Mode

Enable debug mode for detailed execution tracing:

```bash
make debug-workflow
```

Debug features:
- **Trace Files**: Execution traces saved to `debug_traces/`
- **Error Details**: Complete stack traces for troubleshooting
- **Step-by-Step Logs**: Detailed workflow execution logs
- **Performance Metrics**: Timing and resource usage information

## ✨ AI-Powered Workflow Creation

Create new workflows using natural language descriptions:

```bash
make create-workflow
```

Example interaction:
```
✨ AI-Powered Workflow Creator
========================================

Describe the workflow you want to create.
Example: 'Analyze a text file and generate a summary report'

Workflow description: Analyze customer feedback and generate insights
Workflow name (optional): feedback_analyzer

🔄 Generating workflow...
✅ Workflow generated successfully!
Generated workflow: feedback_analyzer

Save and run this workflow? (y/n): y
💾 Workflow saved to: generated_workflows/feedback_analyzer.yaml
Enter input for workflow execution: Customer complained about slow response times
🚀 Executing generated workflow...
```

## 📊 Workflow Structure

### Supported Workflow Types

#### Agent-Based Workflows
```yaml
workflows:
  my_workflow:
    steps:
      - id: step1
        agent: my_agent
        input: "${user_input}"
        output:
          to: user
```

#### Function-Based Workflows
```yaml
workflows:
  my_workflow:
    steps:
      - id: step1
        function: my.module.function
        args:
          input: "${user_input}"
        output:
          to: user
```

#### Tool-Based Workflows
```yaml
workflows:
  my_workflow:
    steps:
      - id: step1
        tool: my_tool
        input: "${user_input}"
        output:
          to: user
```

## ⚙️ Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for AI-powered features
- `LANGSWARM_DEBUG` - Enable debug logging
- `LANGSWARM_CONFIG_PATH` - Custom configuration path

### File Structure
```
/
├── Makefile                          # Make commands
├── scripts/
│   └── interactive_workflow_runner.py # Main interactive script
├── examples/                         # Example workflows
├── debug_traces/                     # Debug trace files
├── generated_workflows/              # AI-generated workflows
└── docs/
    └── interactive-workflow-system.md # This documentation
```

## 🔧 Customization

### Adding Custom Workflow Categories
Edit the `get_workflows_by_category()` method in `scripts/interactive_workflow_runner.py`:

```python
def get_workflows_by_category(self) -> Dict[str, List[Dict]]:
    categories = {
        'My Custom Category': [],
        # ... existing categories
    }
    
    for key, workflow in self.workflows.items():
        if 'my_custom' in workflow['file_path'].lower():
            categories['My Custom Category'].append((key, workflow))
```

### Adding Custom Presets
Add new preset options in the `run_preset_workflow()` method:

```python
presets = {
    '1': ('BigQuery Analysis', 'bigquery'),
    '2': ('Filesystem Operations', 'filesystem'), 
    '3': ('Memory Demo', 'memory'),
    '4': ('My Custom Preset', 'my_custom'),  # New preset
}
```

## 🚨 Troubleshooting

### Common Issues

#### No Workflows Found
```bash
# Check if workflow files exist
find . -name "*.yaml" -o -name "*.yml"

# Verify workflow format
make validate-workflow
```

#### Import Errors
```bash
# Reinstall LangSwarm
make setup

# Check Python path
python -c "import langswarm; print(langswarm.__file__)"
```

#### API Key Issues
```bash
# Setup API keys
python setup_api_key.py

# Verify environment
echo $OPENAI_API_KEY
```

### Debug Mode
For detailed troubleshooting, always use debug mode:
```bash
make debug-workflow
```

This creates detailed trace files in `debug_traces/` that can help identify issues.

## 📖 Examples

### Example 1: Running a BigQuery Workflow
```bash
make run-workflow
# Select: BigQuery Workflows → data_analysis_workflow
# Query: "Show me sales trends for the last quarter"
```

### Example 2: Creating a Custom Workflow
```bash
make create-workflow
# Description: "Process CSV files and generate Excel reports"
# Name: "csv_to_excel_processor"
# Input: "process sales_data.csv"
```

### Example 3: Debug Mode Execution
```bash
make debug-workflow
# Select any workflow
# Check debug_traces/ for detailed execution logs
```

## 🎯 Best Practices

### Workflow Design
1. **Clear Descriptions**: Always include meaningful descriptions in your workflows
2. **Modular Structure**: Break complex workflows into smaller, reusable steps
3. **Error Handling**: Include proper error handling and validation
4. **Documentation**: Document expected inputs and outputs

### Usage Patterns
1. **Start Simple**: Begin with basic workflows before creating complex ones
2. **Use Presets**: Leverage preset workflows for common tasks
3. **Debug Early**: Use debug mode during development
4. **Iterate**: Refine workflows based on execution results

### Performance
1. **Async Execution**: Use async workflows for better performance
2. **Resource Management**: Monitor memory and API usage
3. **Caching**: Leverage LangSwarm's memory system for efficiency
4. **Optimization**: Profile workflows using debug traces

## 🤝 Contributing

To add new features to the Interactive Workflow System:

1. **Fork and Clone**: Get the latest code
2. **Create Features**: Add new commands or improve existing ones
3. **Test Thoroughly**: Ensure compatibility with existing workflows
4. **Document Changes**: Update this documentation
5. **Submit PR**: Follow the project's contribution guidelines

## 📞 Support

For help with the Interactive Workflow System:

1. **Documentation**: Check this guide and other docs in `/docs`
2. **Examples**: Review example workflows in `/examples`
3. **Debug Logs**: Use debug mode for detailed troubleshooting
4. **Community**: Reach out via project channels

---

**Happy workflow orchestration! 🚀**

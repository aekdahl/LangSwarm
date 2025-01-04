---
title: Logging in LangSwarm
---

# **Logging in LangSwarm**

## **Overview**

LangSwarm provides a flexible and user-friendly logging mechanism to track the behavior of workflows and agents. It integrates seamlessly with Python's built-in `logging` module and supports both centralized logging and custom loggers. This ensures that developers can debug, monitor, and evaluate LangSwarm workflows efficiently.

---

## **Key Features**

1. **Centralized Logging**:  
   A global logger is automatically available across all LangSwarm workflows.
   
2. **Customizable Loggers**:  
   Users can override the default logger with their own custom logger for advanced use cases.

3. **Consistent Logging**:  
   All LangSwarm classes, such as `LLMConsensus`, `LLMAggregation`, and `LLMBranching`, integrate with the centralized logging mechanism.

4. **Minimal Boilerplate**:  
   No need to explicitly pass a logger unless customization is required.

---

## **How Logging Works in LangSwarm**

1. **Default Logger**:  
   LangSwarm initializes a global logger (`LangSwarmLogger`) that is used by default in all workflows.

2. **Custom Logger Support**:  
   Users can pass their own logger to any workflow or class if custom behavior is desired.

3. **Fallback Mechanism**:  
   If no logger is provided, the default logger is used automatically.

---

## **API Reference**

### **Default Logger Initialization**

LangSwarm automatically initializes a global logger during setup:
```python
import logging

# Initialize the default logger
def initialize_logger():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger("LangSwarmLogger")

global_logger = initialize_logger()
```

This logger is available globally within LangSwarm workflows.

---

### **Custom Logger Support**

All LangSwarm workflows accept an optional `logger` parameter for custom logging.

```python
class LLMConsensus:
    def __init__(self, query, clients, logger=None):
        self.query = query
        self.clients = clients
        self.logger = logger or global_logger  # Fallback to the global logger
```

---

## **Examples**

### **Using the Default Logger**

LangSwarm workflows automatically log to the default logger without requiring user intervention.

```python
from langswarm.swarm import LLMConsensus

# Create and run a consensus workflow
consensus = LLMConsensus(query="What are the benefits of AI?", clients=[agent1, agent2])
response = consensus.run()

# Logs will automatically appear in the console
# Example Log Output:
# 2024-12-20 14:35:12 - INFO - Running consensus for query: What are the benefits of AI?
# 2024-12-20 14:35:13 - INFO - Consensus response: Increased efficiency and productivity.
```

---

### **Using a Custom Logger**

You can create and pass a custom logger for advanced use cases, such as debugging or logging to a file.

```python
import logging
from langswarm.swarm import LLMConsensus

# Initialize a custom logger
custom_logger = logging.getLogger("CustomLogger")
custom_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("custom_logs.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
custom_logger.addHandler(handler)

# Use the custom logger in a workflow
consensus = LLMConsensus(query="What are the challenges of AI?", clients=[agent1, agent2], logger=custom_logger)
response = consensus.run()

# Logs will be written to the file "custom_logs.log"
```

---

### **Customizing Logging Levels**

You can customize the logging level (e.g., DEBUG, INFO, WARNING) globally or for individual loggers.

```python
# Set the global logger to debug level
global_logger.setLevel(logging.DEBUG)

# Adjust the logging level of the custom logger
custom_logger.setLevel(logging.WARNING)
```

---

## **Best Practices**

1. **Leverage the Default Logger**:  
   Use the default logger for simplicity and consistent logging across LangSwarm.

2. **Use Custom Loggers for Advanced Use Cases**:  
   Create custom loggers for scenarios requiring specific logging levels, destinations, or formats.

3. **Enable Verbose Mode for Development**:  
   Use verbose workflows and detailed logging during testing to identify issues.

4. **Centralized Configuration**:  
   Configure logging centrally to maintain consistency across the application.

---

## **Key Advantages**

1. **Minimal Setup**:  
   Automatic fallback to a global logger reduces boilerplate code.

2. **Customizable**:  
   Easily override the default logger for specific workflows or use cases.

3. **Debug-Friendly**:  
   Supports detailed logging to facilitate debugging and monitoring.

---

## **Future Enhancements**

1. **Integration with LangSmith**:  
   Expand logging to include structured evaluations and analytics via LangSmith.

2. **Visualization**:  
   Add support for visualizing logs in dashboards or external tools like ELK Stack.

3. **Custom Handlers**:  
   Allow users to specify custom log handlers for more advanced logging destinations (e.g., cloud services, databases).

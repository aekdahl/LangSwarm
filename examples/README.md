# LangSwarm Examples

This directory contains comprehensive examples demonstrating LangSwarm's capabilities across different domains and use cases.

## 📁 Directory Structure

### `/comprehensive/`
**Full integration examples showcasing multiple LangSwarm systems working together**

- `demo_comprehensive_langswarm_integration.py` - End-to-end demo featuring:
  - Multi-provider agent orchestration
  - Session management across conversations  
  - MCP tool integration (local & remote)
  - Workflow orchestration
  - Multi-platform UI gateways
  - Intelligent navigation system
  - Memory backends
  - Multi-agent consensus

### `/memory/`
**MemoryPro feature demonstrations**

- `demo_memorypro.py` - Complete MemoryPro showcase including:
  - Dual-mode memory management (internal vs external)
  - AI-powered memory analysis and insights
  - Action discovery from memory content
  - Real-time webhook notifications
  - Memory lifecycle management
  - Pattern analysis and evolution tracking

### `/integration/`
**Integration examples for specific platforms and tools**

*Directory ready for platform-specific integration examples*

## 🚀 Running Examples

### Prerequisites
```bash
# Install LangSwarm with all dependencies
pip install langswarm[all]

# Set up environment variables (see individual example files for specifics)
export OPENAI_API_KEY="your_key_here"
export MEMORYPRO_API_KEY="your_key_here"  # For MemoryPro examples
```

### Quick Start
```bash
# Run comprehensive integration demo
cd examples/comprehensive
python demo_comprehensive_langswarm_integration.py

# Run MemoryPro feature demo  
cd examples/memory
python demo_memorypro.py
```

## 📋 Example Categories

### 🔄 **Real-World Scenarios** (Comprehensive)
1. **E-commerce Customer Support** - Multi-agent consensus for complex queries
2. **Software Development Workflow** - Repository integration with automated workflows  
3. **Document Analysis Pipeline** - Memory persistence across processing stages
4. **Multi-Platform Notifications** - Intelligent routing across communication channels
5. **Collaborative Content Creation** - Navigation-driven workflow orchestration

### 🧠 **Memory & Intelligence** (MemoryPro)
- External memory provider integration
- AI-powered memory insights and analysis
- Automated action discovery from content
- Real-time webhook event handling
- Memory pattern evolution tracking

## 🔗 Related Examples

- **MCP Tools**: See `example_mcp_config/` for tool configuration examples
- **Navigation**: See `langswarm/features/intelligent_navigation/examples/` for routing demos
- **Documentation**: See `docs/simplification/examples/` for configuration examples

## 📖 Documentation

For detailed documentation on the features demonstrated in these examples:

- [LangSwarm Documentation](../docs/)
- [MCP Integration Guide](../docs/LOCAL_MCP_GUIDE.md)
- [MemoryPro API Documentation](../docs/MEMORYPRO_API.md)
- [Zero Config Guide](../docs/ZERO_CONFIG_CUSTOMIZATION_GUIDE.md)

## 🤝 Contributing Examples

When adding new examples:

1. Choose the appropriate directory based on the primary focus
2. Include comprehensive docstrings explaining the use case
3. Add environment variable documentation
4. Update this README with the new example
5. Ensure examples are self-contained and runnable

---

**Note**: These examples are designed to showcase LangSwarm's capabilities. For production use, please refer to the main documentation for best practices and security considerations. 
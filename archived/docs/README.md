# LangSwarm Documentation

## 🔍 Debug and Tracing System

### **Quick Start**
- **[Debug Quick Reference](debug-quick-reference.md)** - TL;DR for emergency debugging
- **[Full Debug Guide](debug-tracing-system.md)** - Comprehensive documentation

### **Detailed Guides** 
- **[Debug Configuration](debug-configuration.md)** - Setup and config management
- **[Debug Cases](debug-cases.md)** - Ready-made debug scenarios  
- **[Separate Trace Files](debug-separate-traces.md)** - Per-scenario tracing

### **Key Points**

✅ **Debug is DISABLED by default** - production safe  
⚡ **0.000023ms overhead** when disabled  
🚨 **34% performance hit** when enabled (emergency use only)  
🔧 **CLI tools** for easy debugging  
📊 **Structured JSON logs** with hierarchical tracing  

### **Emergency Debugging**

```bash
# Quick debug case
python -m langswarm.core.debug.cli run-case-1

# Enable tracing in code
python -c "from langswarm.core.debug import enable_debug_tracing; enable_debug_tracing('debug.jsonl')"
```

## 📁 Documentation Structure

```
docs/
├── README.md                     # This file
├── debug-quick-reference.md      # TL;DR guide
├── debug-tracing-system.md       # Complete debug guide
├── debug-configuration.md        # Config setup
├── debug-cases.md               # Debug scenarios
└── debug-separate-traces.md     # Per-scenario tracing
```

---

*For more LangSwarm documentation, see the main project README.*
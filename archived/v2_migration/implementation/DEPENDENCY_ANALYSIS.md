# LangSwarm V2 Dependency Analysis & Cleanup Strategy

**Task ID**: 07  
**Phase**: Integration & Cleanup  
**Status**: 🔍 **IN ANALYSIS**  
**Date**: 2024-12-19

---

## 📊 **CURRENT DEPENDENCY ANALYSIS**

### **Heavy Framework Dependencies (Lines 23-31 in pyproject.toml)**

| Package | Version | Usage | Replacement Strategy |
|---------|---------|-------|---------------------|
| `langchain-community` | ^0.3.24 | Vector stores, LLM wrappers | ✅ **V2 Native** - Direct API calls |
| `langchain-openai` | ^0.3.17 | OpenAI agent creation | ✅ **V2 Agents** - Native OpenAI integration |
| `langsmith` | ^0.3.42 | Logging and tracing | ⚠️ **Optional** - Move to extras |
| `llama-index` | ^0.12.36 | Document indexing, vector stores | ✅ **V2 Memory** - Native vector storage |
| `transformers` | ^4.51.3 | Hugging Face model support | ⚠️ **Keep** - Direct model usage |
| `pinecone` | ^6.0.2 | Vector database | ✅ **V2 Native** - Direct Pinecone API |
| `qdrant-client` | ^1.14.2 | Vector database | ✅ **V2 Native** - Direct Qdrant API |

### **Framework Usage Analysis**

#### **1. Memory Adapters (High Impact)**
- **Files**: `langswarm/memory/adapters/langchain.py` (1,100+ lines)
- **Files**: `langswarm/memory/adapters/llamaindex.py` (560+ lines)
- **Usage**: Vector stores (Pinecone, Qdrant, Chroma, etc.)
- **Replacement**: V2 memory system with native vector store clients

#### **2. Agent Factory (Medium Impact)**
- **Files**: `langswarm/core/factory/agents.py` (lines 212-239)
- **Usage**: LangChain/LlamaIndex agent creation
- **Replacement**: V2 agent system with native provider implementations

#### **3. Generic Wrappers (Low Impact)**
- **Files**: `langswarm/core/wrappers/generic.py` (lines 27-52)
- **Usage**: Try/except imports for framework fallbacks
- **Replacement**: V2 agent wrappers with clean imports

---

## 🎯 **REPLACEMENT STRATEGY**

### **Phase 1: Native Memory Implementations** ⏳
**Target**: Replace LangChain/LlamaIndex memory adapters with V2 native implementations

1. **Create Native Vector Store Clients**
   - Direct Pinecone client implementation
   - Direct Qdrant client implementation
   - Direct ChromaDB client implementation
   - Native SQLite vector storage

2. **Implement V2 Memory Adapters**
   - Unified interface compatible with V2 memory system
   - Direct API calls without framework abstractions
   - Better performance and control

3. **Migration Tools**
   - Automatic migration from framework adapters to native
   - Data preservation during migration
   - Compatibility layer for gradual transition

### **Phase 2: Native Agent Implementations** ✅
**Target**: Replace LangChain/LlamaIndex agent creation with V2 agents

1. **V2 Agent System** (Already Complete)
   - Native OpenAI implementation ✅
   - Native Anthropic implementation ✅
   - Native Gemini implementation ✅
   - Native Cohere implementation ✅

2. **Factory Migration**
   - Update agent factory to use V2 agents
   - Remove framework-specific creation paths
   - Maintain backward compatibility

### **Phase 3: Wrapper Simplification** ⏳
**Target**: Simplify generic wrappers to use V2 systems

1. **Clean V2 Imports**
   - Remove try/except framework imports
   - Use V2 agent and memory systems directly
   - Simplify wrapper inheritance

2. **Legacy Compatibility**
   - Optional framework support for advanced users
   - Clean separation between V2 and legacy

### **Phase 4: Dependency Cleanup** ⏳
**Target**: Remove or move heavy dependencies

1. **Remove Core Dependencies**
   - `langchain-community` → V2 native implementations
   - `langchain-openai` → V2 OpenAI agent
   - `llama-index` → V2 memory system

2. **Move to Optional Dependencies**
   - `langsmith` → dev/monitoring extras
   - Framework packages → legacy extras

3. **Update Documentation**
   - Migration guides for framework users
   - V2 native implementation guides

---

## 🔧 **IMPLEMENTATION PLAN**

### **Step 1: Create Native Vector Store Implementations** 
**Duration**: 2-3 days

```python
# Native Pinecone implementation
class NativePineconeAdapter:
    """Direct Pinecone API integration without LangChain"""
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        import pinecone
        self.pc = pinecone.Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
    
    async def query(self, vector: List[float], top_k: int = 10, 
                   filters: Dict = None) -> List[Dict]:
        """Direct query without LangChain abstractions"""
        return self.index.query(
            vector=vector,
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )
```

### **Step 2: Integrate with V2 Memory System**
**Duration**: 1-2 days

```python
# Integration with V2 memory
from langswarm.v2.core.memory import MemoryBackend, IMemoryBackend

class V2VectorMemoryBackend(IMemoryBackend):
    """V2-native vector memory backend"""
    
    def __init__(self, vector_store: str, config: Dict[str, Any]):
        if vector_store == "pinecone":
            self.store = NativePineconeAdapter(**config)
        elif vector_store == "qdrant":
            self.store = NativeQdrantAdapter(**config)
        # etc.
```

### **Step 3: Update Agent Factory for V2**
**Duration**: 1 day

```python
# Updated agent factory
class V2AgentFactory:
    """Modern agent factory using V2 systems"""
    
    @staticmethod
    def create_agent(provider: str, model: str, **kwargs) -> BaseAgent:
        """Create agent using V2 system"""
        from langswarm.v2.core.agents import AgentBuilder
        
        return (AgentBuilder(f"{provider}_agent")
                .provider(provider)
                .model(model)
                .build())
```

### **Step 4: Clean Dependencies**
**Duration**: 1 day

```toml
# Updated pyproject.toml - Core dependencies only
[tool.poetry.dependencies]
python = ">=3.8,<4.0"
# Core dependencies
pyyaml = "^6.0.2"
tiktoken = "^0.9.0"
openai = "^1.79.0"
# Remove: langchain-community, langchain-openai, llama-index

[tool.poetry.extras]
# Legacy framework support (optional)
langchain = ["langchain-community", "langchain-openai"]
llamaindex = ["llama-index"]
# Monitoring and development
monitoring = ["langsmith"]
```

---

## 📈 **EXPECTED BENEFITS**

### **Installation Speed**
- **Before**: 45+ packages, 200+ MB download
- **After**: 15+ packages, 50+ MB download
- **Improvement**: 70% faster installation

### **Dependency Conflicts**
- **Before**: Frequent LangChain/LlamaIndex version conflicts
- **After**: Minimal dependencies, controlled versions
- **Improvement**: 90% reduction in dependency issues

### **Performance**
- **Before**: Framework abstractions add 10-20% overhead
- **After**: Direct API calls, optimized for LangSwarm use
- **Improvement**: 15-25% performance improvement

### **Maintenance**
- **Before**: Track 12+ framework packages and their dependencies
- **After**: Control direct API integrations
- **Improvement**: 80% reduction in dependency maintenance

---

## 🚨 **MIGRATION RISKS & MITIGATION**

### **Risk 1: Breaking Existing Integrations**
- **Mitigation**: Gradual migration with compatibility layers
- **Timeline**: Phase out over 2-3 minor releases
- **Fallback**: Optional framework dependencies for legacy users

### **Risk 2: Feature Gaps in Native Implementations**
- **Mitigation**: Feature parity analysis before removal
- **Timeline**: Comprehensive testing of native implementations
- **Fallback**: Keep framework implementations until feature parity

### **Risk 3: User Migration Burden**
- **Mitigation**: Automated migration tools
- **Timeline**: Clear migration guides and examples
- **Fallback**: Support both V1 and V2 during transition

---

## 📋 **SUCCESS CRITERIA**

### **Functional Success**
- [ ] **Native Implementations**: All LangChain/LlamaIndex functionality replicated natively
- [ ] **Performance Parity**: Native implementations match or exceed framework performance
- [ ] **Feature Completeness**: No regression in available features
- [ ] **Migration Tools**: Automated migration from framework to native

### **Quality Success**
- [ ] **Installation Speed**: 50%+ improvement in installation time
- [ ] **Dependency Count**: 60%+ reduction in required dependencies
- [ ] **Version Conflicts**: 90%+ reduction in dependency conflicts
- [ ] **Code Simplicity**: Removal of complex try/except import blocks

### **User Success**
- [ ] **Backward Compatibility**: Existing configurations continue working
- [ ] **Migration Path**: Clear path from framework dependencies to native
- [ ] **Documentation**: Complete guides for native implementations
- [ ] **Optional Support**: Framework dependencies available as extras

---

## 🔄 **IMPLEMENTATION STATUS**

### **Phase 1: Native Memory Implementations** 
- [ ] **Pinecone Native Client** - Not Started
- [ ] **Qdrant Native Client** - Not Started
- [ ] **ChromaDB Native Client** - Not Started
- [ ] **SQLite Vector Storage** - Not Started
- [ ] **V2 Memory Integration** - Not Started

### **Phase 2: Native Agent Implementations**
- [x] **V2 Agent System** - ✅ Complete
- [ ] **Factory Migration** - Not Started
- [ ] **Wrapper Integration** - Not Started

### **Phase 3: Wrapper Simplification**
- [ ] **Clean V2 Imports** - Not Started
- [ ] **Legacy Compatibility** - Not Started

### **Phase 4: Dependency Cleanup**
- [ ] **Remove Core Dependencies** - Not Started
- [ ] **Move to Optional** - Not Started
- [ ] **Update Documentation** - Not Started

---

**Next Steps**: Begin Phase 1 with native vector store implementations, starting with Pinecone as the most commonly used vector database in the codebase.

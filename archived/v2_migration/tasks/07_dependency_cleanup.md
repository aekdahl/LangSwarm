# TASK: Dependency Cleanup - Remove LangChain/LlamaIndex and Simplify Dependencies

**Task ID**: 07  
**Phase**: 3 (Integration)  
**Priority**: LOW  
**Dependencies**: All previous tasks (01-06)  
**Estimated Time**: 1-2 weeks

---

## 🔍 **ANALYZE**

### **Current State Assessment**
**Description**: LangSwarm currently has heavy dependencies on LangChain and LlamaIndex, adding 12+ packages, version conflicts, and unnecessary complexity. These can be replaced with native implementations now that V2 architecture is in place.

**Files Involved**:
- [ ] `pyproject.toml` - 89 lines with heavy AI/ML dependencies (lines 23-31)
- [ ] `langswarm/core/factory/agents.py` - LangChain/LlamaIndex integrations (lines 212-239)
- [ ] `langswarm/core/wrappers/generic.py` - LangChain/LlamaIndex imports (lines 27-52)
- [ ] `langswarm/memory/adapters/llamaindex.py` - LlamaIndex memory adapters (494+ lines)
- [ ] `langswarm/memory/adapters/langchain.py` - LangChain memory adapters
- [ ] Multiple import statements across the codebase using these dependencies

**Pain Points Identified**:
1. **Heavy Dependencies**: 12+ additional packages (langchain-community, langchain-openai, llama-index, etc.)
2. **Version Conflicts**: LangChain/LlamaIndex updates often break compatibility
3. **Complex Abstractions**: LangSwarm abstractions on top of framework abstractions
4. **Maintenance Overhead**: Need to track and update multiple framework versions
5. **Import Bloat**: Try/except import blocks throughout codebase
6. **Performance Overhead**: Framework abstractions add unnecessary layers
7. **Limited Control**: Framework opinions limit LangSwarm flexibility

**Dependencies and Constraints**:
- **Technical Dependencies**: Must complete all V2 systems first (agents, tools, sessions)
- **Backward Compatibility**: Existing functionality must be preserved
- **Performance Constraints**: Native implementations must match or exceed current performance
- **Security Considerations**: Direct API integrations must maintain security practices

**Impact Assessment**:
- **Scope**: Agent creation, memory adapters, tool integrations, installation dependencies
- **Risk Level**: LOW - Can be done incrementally after V2 systems are stable
- **Breaking Changes**: No - Native implementations provide same interfaces
- **User Impact**: Faster installation, more reliable dependencies, better performance

### **Complexity Analysis**
- **Code Complexity**: Multiple framework integrations with complex adapter patterns
- **Integration Complexity**: Framework dependencies affect agent creation and memory systems
- **Testing Complexity**: Must ensure native implementations match framework behavior
- **Migration Complexity**: Replace framework code while maintaining all functionality

---

## 💬 **DISCUSS**

### **Key Decisions Required**
1. **Removal Strategy**: How to remove framework dependencies
   - **Option A**: Remove all at once after V2 is complete
   - **Option B**: Remove incrementally as V2 components are implemented
   - **Option C**: Keep frameworks as optional dependencies
   - **Recommendation**: Remove incrementally after V2 stability - reduces risk

2. **Native Implementation Scope**: What to implement natively vs what to remove
   - **Option A**: Implement everything that frameworks provided
   - **Option B**: Implement only what LangSwarm actually uses
   - **Option C**: Remove unused functionality and implement core features
   - **Recommendation**: Implement only what's actually used - reduces complexity

3. **Performance Requirements**: How native implementations should perform
   - **Option A**: Match framework performance exactly
   - **Option B**: Exceed framework performance
   - **Option C**: Accept some performance trade-offs for simplicity
   - **Recommendation**: Exceed framework performance where possible

### **Trade-offs Analysis**
| Aspect | Benefit | Cost | Decision |
|--------|---------|------|----------|
| Dependency Reduction | Faster install, fewer conflicts | Native implementation effort | Accepted |
| Native Implementations | Full control, better performance | Initial development cost | Accepted |
| Incremental Removal | Lower risk, gradual validation | Longer timeline | Accepted |
| Optional Dependencies | User choice, gradual migration | Complexity in codebase | Rejected |

### **Constraints and Limitations**:
- **Technical Constraints**: Must wait for V2 systems to be stable and tested
- **Resource Constraints**: Native implementations require development effort
- **Compatibility Constraints**: Must maintain all current functionality
- **Business Constraints**: Cannot break existing user workflows

### **Stakeholder Considerations**:
- **Developers**: Want simpler, more reliable dependencies
- **Users**: Want faster installation and fewer version conflicts
- **Operations**: Want reduced surface area for security and deployment
- **Community**: Want cleaner codebase for contributions

---

## 📝 **PLAN**

### **Implementation Strategy**
**Approach**: Incremental removal of framework dependencies after V2 systems are stable, with native implementations

**Phases**:
1. **Phase 1**: Assessment - Analyze actual framework usage and create native implementation plan (2-3 days)
2. **Phase 2**: Native Implementation - Create native implementations for used features (5-7 days)
3. **Phase 3**: Migration - Replace framework usage with native implementations (3-5 days)

### **Detailed Implementation Steps**
1. **Analyze Framework Usage**: Determine what framework features are actually used
   - **Input**: Complete codebase analysis of LangChain/LlamaIndex usage
   - **Output**: Usage report and native implementation requirements
   - **Duration**: 2 days
   - **Dependencies**: All V2 tasks completed

2. **Create Native Agent Implementations**: Replace LangChain/LlamaIndex agent creation
   - **Input**: Framework usage analysis and V2 agent system
   - **Output**: Native provider implementations to replace framework agents
   - **Duration**: 3 days
   - **Dependencies**: Task 04 (Agent System) stable

3. **Create Native Memory Implementations**: Replace framework memory adapters
   - **Input**: Memory adapter analysis and requirements
   - **Output**: Native memory implementations without framework dependencies
   - **Duration**: 2 days
   - **Dependencies**: Framework usage analysis

4. **Replace Framework Imports**: Remove framework imports throughout codebase
   - **Input**: Native implementations
   - **Output**: Codebase free of framework dependencies
   - **Duration**: 2 days
   - **Dependencies**: Native implementations complete

5. **Update Dependencies**: Remove framework packages from dependencies
   - **Input**: Framework-free codebase
   - **Output**: Updated pyproject.toml with reduced dependencies
   - **Duration**: 1 day
   - **Dependencies**: Framework imports removed

6. **Validate Performance**: Ensure native implementations meet performance requirements
   - **Input**: Native implementations
   - **Output**: Performance validation and optimization
   - **Duration**: 1 day
   - **Dependencies**: All native implementations

### **Testing Strategy**
#### **Unit Testing**
- **Scope**: All native implementations, performance comparisons
- **Framework**: pytest with framework behavior mocking for comparison
- **Coverage Target**: 95%
- **Test Files**: 
  - [ ] `tests/unit/v2/native/test_native_openai.py`
  - [ ] `tests/unit/v2/native/test_native_anthropic.py`
  - [ ] `tests/unit/v2/native/test_native_memory.py`

#### **Integration Testing**
- **Scope**: Native implementations with V2 systems, end-to-end functionality
- **Test Scenarios**: Agent creation, conversation flow, memory operations
- **Test Files**:
  - [ ] `tests/integration/v2/test_native_agent_integration.py`
  - [ ] `tests/integration/v2/test_native_memory_integration.py`

#### **Regression Testing**
- **V1 Compatibility**: All functionality preserved without frameworks
- **Performance Testing**: Native implementations vs framework implementations
- **Test Files**:
  - [ ] `tests/regression/test_framework_removal_compatibility.py`
  - [ ] `tests/performance/benchmark_native_vs_framework.py`

#### **Dependency Testing**
- **Installation Testing**: Verify clean installation without framework dependencies
- **Conflict Testing**: Verify no dependency conflicts after removal
- **Test Files**:
  - [ ] `tests/installation/test_clean_install.py`

### **Tracing Implementation**
#### **Component Tracing**
- **Entry Points**: Native implementation initialization, API calls
- **Exit Points**: Response processing, error handling
- **Data Flow**: Request/response flow through native implementations

#### **Error Tracing**
- **Error Points**: API failures, authentication issues, response parsing errors
- **Error Context**: API call context, request/response data, error recovery
- **Error Recovery**: Trace retry mechanisms and fallback strategies

#### **Performance Tracing**
- **Timing Points**: API call timing, response processing, memory operations
- **Resource Usage**: Memory for native implementations vs frameworks
- **Bottleneck Detection**: Identify performance improvements from native implementations

### **Debug Mode Implementation**
#### **Verbose Logging**
- **Debug Levels**: TRACE, DEBUG, INFO, WARNING, ERROR
- **Log Categories**: Native implementations, API calls, performance, dependency tracking
- **Output Formats**: Console with performance comparisons, structured JSON

#### **Debug Utilities**
- **Inspection Tools**: Native implementation inspector, performance comparator
- **State Dumping**: Native implementation states, performance metrics
- **Interactive Debugging**: Native implementation testing, API call simulation

### **Rollback Plan**
- **Rollback Triggers**: Performance degradation, functionality loss, stability issues
- **Rollback Steps**: Re-enable framework dependencies, revert to framework implementations
- **Data Recovery**: No data recovery needed (implementations are functionally equivalent)
- **Timeline**: Quick rollback by reverting dependency changes

### **Success Criteria**
- [ ] **Functional**: All framework functionality preserved with native implementations
- [ ] **Performance**: Native implementations equal or better performance than frameworks
- [ ] **Compatibility**: 100% backward compatibility maintained
- [ ] **Quality**: Reduced dependencies, cleaner codebase, fewer version conflicts
- [ ] **Testing**: 95% test coverage, all native implementations tested
- [ ] **Documentation**: Updated installation and dependency documentation

---

## ⚡ **DO**

### **Implementation Log**
**Start Date**: [YYYY-MM-DD]  
**End Date**: [YYYY-MM-DD]  
**Total Duration**: [X days]

#### **Phase 1 Implementation** (Framework Usage Analysis)
- **Start**: [Date/Time]
- **Status**: [⏳ Pending]
- **Step 1**: [⏳] Analyze LangChain usage across codebase - [Result/Issues]
- **Step 2**: [⏳] Analyze LlamaIndex usage across codebase - [Result/Issues]
- **Step 3**: [⏳] Create native implementation requirements - [Result/Issues]
- **End**: [Date/Time]
- **Notes**: [Implementation notes, issues, decisions made]

#### **Phase 2 Implementation** (Native Implementations)
- **Start**: [Date/Time]
- **Status**: [⏳ Pending]
- **Step 1**: [⏳] Create native agent implementations - [Result/Issues]
- **Step 2**: [⏳] Create native memory implementations - [Result/Issues]
- **Step 3**: [⏳] Create native utility implementations - [Result/Issues]
- **End**: [Date/Time]
- **Notes**: [Implementation notes, issues, decisions made]

#### **Phase 3 Implementation** (Migration & Cleanup)
- **Start**: [Date/Time]
- **Status**: [⏳ Pending]
- **Step 1**: [⏳] Replace framework imports with native implementations - [Result/Issues]
- **Step 2**: [⏳] Update dependencies in pyproject.toml - [Result/Issues]
- **Step 3**: [⏳] Validate performance and functionality - [Result/Issues]
- **End**: [Date/Time]
- **Notes**: [Implementation notes, issues, decisions made]

### **Framework Usage Analysis**
#### **LangChain Usage**
- [ ] **Agent Creation** - [Usage Level] - [Native Implementation Status]
  - [ ] `ChatOpenAI` usage in agent factory
  - [ ] `AzureChatOpenAI` usage patterns
  - [ ] LangChain tool integrations
  - [ ] LangChain memory integrations

- [ ] **Memory Systems** - [Usage Level] - [Native Implementation Status]
  - [ ] `PineconeAdapter` implementation
  - [ ] LangChain vector store integrations
  - [ ] Memory retrieval patterns

- [ ] **Tool Integrations** - [Usage Level] - [Native Implementation Status]
  - [ ] LangChain tool wrappers
  - [ ] LangChain function calling
  - [ ] LangChain agent executors

#### **LlamaIndex Usage**
- [ ] **Index Systems** - [Usage Level] - [Native Implementation Status]
  - [ ] `GPTSimpleVectorIndex` usage
  - [ ] `PineconeIndex` implementations
  - [ ] `WeaviateIndex` implementations
  - [ ] `FAISSIndex` implementations
  - [ ] `SQLIndex` implementations

- [ ] **Document Processing** - [Usage Level] - [Native Implementation Status]
  - [ ] Document loaders and parsers
  - [ ] Text splitting and chunking
  - [ ] Embedding generation

- [ ] **Query Systems** - [Usage Level] - [Native Implementation Status]
  - [ ] Query engines and retrievers
  - [ ] Response synthesis
  - [ ] Query optimization

### **Native Implementation Progress**
#### **Agent Implementations**
- [ ] **OpenAI Native** - [Status] - [Notes]
  - [ ] Direct OpenAI API integration
  - [ ] Function calling support
  - [ ] Streaming responses
  - [ ] Error handling and retries

- [ ] **Anthropic Native** - [Status] - [Notes]
  - [ ] Direct Anthropic API integration
  - [ ] Tool use support
  - [ ] Message formatting
  - [ ] Content safety handling

- [ ] **Google Native** - [Status] - [Notes]
  - [ ] Direct Gemini API integration
  - [ ] Function calling support
  - [ ] Safety settings
  - [ ] Content generation

#### **Memory Implementations**
- [ ] **Vector Storage Native** - [Status] - [Notes]
  - [ ] Direct Pinecone integration
  - [ ] Direct ChromaDB integration
  - [ ] Direct Qdrant integration
  - [ ] Vector operations and similarity search

- [ ] **Database Storage Native** - [Status] - [Notes]
  - [ ] Direct SQLite integration
  - [ ] Direct PostgreSQL integration
  - [ ] Direct BigQuery integration
  - [ ] Query optimization

### **Dependency Reduction Progress**
#### **Dependencies Removed**
- [ ] `langchain-community` - [Status] - [Replacement]
- [ ] `langchain-openai` - [Status] - [Replacement]
- [ ] `langsmith` - [Status] - [Replacement]
- [ ] `llama-index` - [Status] - [Replacement]

#### **Dependencies Retained**
- [ ] `openai` - [Reason: Direct provider integration]
- [ ] `anthropic` - [Reason: Direct provider integration]
- [ ] `google-generativeai` - [Reason: Direct provider integration]
- [ ] Essential utility packages

### **Testing Results**
#### **Unit Tests**
- **Framework Used**: [pytest]
- **Tests Created**: [Number of test files/functions]
- **Coverage Achieved**: [Percentage]
- **Results**: [✅ All Pass / ❌ X Failed]
- **Failed Tests**: 
  - [ ] `test_[function]` - [Reason for failure] - [Resolution]

#### **Integration Tests**
- **Tests Created**: [Number of integration test scenarios]
- **Results**: [✅ All Pass / ❌ X Failed]
- **Failed Tests**:
  - [ ] `test_[integration]` - [Reason for failure] - [Resolution]

#### **Performance Tests**
- **Native vs Framework**: [Performance Comparison Results]
- **Installation Time**: [Before/After Comparison]
- **Memory Usage**: [Before/After Comparison]
- **Startup Time**: [Before/After Comparison]

### **Tracing Implementation Results**
#### **Component Tracing**
- **Trace Points Added**: [Number of trace points]
- **Trace Files Created**: 
  - [ ] `langswarm/v2/native/tracing.py`
- **Integration**: [✅ Complete / 🔄 Partial] - [Details]

#### **Performance Tracing**
- **Timing Measurements**: [Number of timing points added]
- **Resource Monitoring**: [✅ CPU / ✅ Memory / ✅ I/O] - [Details]
- **Bottleneck Detection**: [✅ Implemented / ❌ Not Implemented] - [Details]

### **Debug Mode Implementation Results**
#### **Verbose Logging**
- **Debug Levels**: [Number of verbosity levels implemented]
- **Log Categories**: [Types of debug information available]
- **Output Support**: [✅ Console / ✅ File / ✅ Structured] - [Details]

### **Issues Encountered**
1. **[Issue 1]**: [Description]
   - **Impact**: [How it affected implementation]
   - **Resolution**: [How it was resolved]
   - **Lessons**: [What was learned]

### **Code Quality Metrics**
- **Lines of Code Added**: [Number]
- **Lines of Code Removed**: [Number] (target: significant reduction)
- **Dependencies Removed**: [Number of packages removed]
- **Installation Time Improvement**: [Percentage improvement]
- **Linting Results**: [✅ Pass / ❌ X Issues] - [Details]

---

## 🚀 **IMPROVE**

### **Optimization Opportunities**
1. **Performance Optimizations**:
   - **Connection Pooling**: Shared HTTP connections for API calls
   - **Response Caching**: Cache API responses for development
   - **Batch Operations**: Batch API calls where possible

2. **Code Quality Improvements**:
   - **API Clients**: Unified API client implementations
   - **Error Handling**: Consistent error handling across providers
   - **Configuration**: Unified provider configuration patterns

3. **Architecture Enhancements**:
   - **Provider Abstraction**: Common interface for all providers
   - **Plugin System**: Easy addition of new providers
   - **Rate Limiting**: Built-in rate limiting and retry logic

### **Documentation Updates Required**
- [ ] **Installation Guide**: Updated installation without framework dependencies
- [ ] **Migration Guide**: How to migrate from framework-dependent code
- [ ] **Performance Guide**: Performance improvements from native implementations
- [ ] **Developer Guide**: How to add new provider integrations
- [ ] **Troubleshooting Guide**: Common issues with native implementations

### **Lessons Learned**
1. **Technical Lessons**:
   - **[To be filled during implementation]**

2. **Process Lessons**:
   - **[To be filled during implementation]**

3. **Team Lessons**:
   - **[To be filled during implementation]**

### **Recommendations for Future Tasks**
1. **Native first approach**: Always consider native implementations before adding frameworks
2. **Dependency minimalism**: Keep dependencies to essential packages only
3. **Performance focus**: Native implementations should prioritize performance

### **Follow-up Tasks**
- [ ] **Additional providers**: Add more native provider implementations - [Medium] - [Next quarter]
- [ ] **Performance optimization**: Further optimize native implementations - [Medium] - [Ongoing]
- [ ] **Provider ecosystem**: Create ecosystem for community provider implementations - [Low] - [Future]

### **Success Metrics Achieved**
- [ ] **Functional Success**: [All planned functionality implemented]
- [ ] **Performance Success**: [Performance targets met or exceeded]
- [ ] **Quality Success**: [Code quality standards achieved]
- [ ] **Process Success**: [ADPDI process followed successfully]
- [ ] **Team Success**: [Team collaboration was effective]

### **Next Steps**
1. **Immediate**: Begin Phase 1 implementation (after all V2 tasks complete)
2. **Short-term**: Complete dependency cleanup and validation
3. **Long-term**: Maintain native implementations and add new providers

---

## 📋 **Task Completion Checklist**

- [ ] **ANALYZE phase complete**: Framework usage analyzed and native implementation plan created
- [ ] **DISCUSS phase complete**: Incremental removal strategy and native implementation decisions
- [ ] **PLAN phase complete**: Implementation plan with performance validation strategy
- [ ] **DO phase complete**: All framework dependencies removed with native implementations
- [ ] **IMPROVE phase complete**: Optimizations identified and lessons documented
- [ ] **Tests created**: Unit, integration, regression, performance tests for native implementations
- [ ] **Tracing implemented**: Native implementation and performance tracing
- [ ] **Debug mode added**: Verbose logging and debug utilities for native implementations
- [ ] **Documentation updated**: Installation, migration, and performance documentation
- [ ] **Code reviewed**: Native implementation code reviewed and approved
- [ ] **Backward compatibility**: All functionality preserved without framework dependencies
- [ ] **Migration path**: Clear upgrade path from framework-dependent to native implementations
- [ ] **Success criteria met**: Reduced dependencies with maintained/improved functionality achieved

---

**Task Status**: [⏳ Not Started]  
**Overall Success**: [⏳ Pending]  
**Lessons Learned**: [To be filled during implementation]

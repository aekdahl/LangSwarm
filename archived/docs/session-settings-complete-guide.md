# LangSwarm Session Settings Complete Guide

Complete explanation of all session configuration options in LangSwarm.

## 🔧 UNIFIED_MEMORY
**Type:** boolean  
**Default:** false  
**Description:** Enable shared conversation context across all agents in the session  
**Example:** `unified_memory: true`  
**⚠️ Caution:** Can lead to context expansion and increased token costs

**Impact:** When true, all agents see complete session history instead of just previous output  
**Use Cases:**
- Multi-agent collaboration workflows
- Customer support with context preservation
- Document processing pipelines
- Research and analysis workflows

## 🔧 SESSION_STRATEGY
**Type:** string  
**Default:** hybrid  
**Options:** native, client, hybrid  
**Description:** How to manage sessions with LLM providers  
**Example:** `session_strategy: 'hybrid'`  
**Recommendation:** Use 'hybrid' for best performance and compatibility

**Details:**
- **native:** Use provider's built-in session management (OpenAI threads, Mistral conversations)
- **client:** LangSwarm manages sessions client-side (works with all providers)
- **hybrid:** Intelligently choose native or client based on provider capabilities

## 🔧 SESSION_CONTROL
**Type:** string  
**Default:** hybrid  
**Options:** native, langswarm, hybrid  
**Description:** Level of session control and management  
**Example:** `session_control: 'hybrid'`  
**Note:** Different from session_strategy - this controls WHO manages, strategy controls HOW

**Details:**
- **native:** Rely entirely on provider's session management
- **langswarm:** Full LangSwarm control over sessions
- **hybrid:** Mix of native and LangSwarm control for optimal results

## 🔧 SCOPE
**Type:** string  
**Default:** workflow  
**Options:** workflow, user, global  
**Description:** Define the boundary of memory sharing  
**Example:** `scope: 'workflow'`

**Details:**
- **workflow:** Memory shared only within a single workflow execution
- **user:** Memory shared across all workflows for a specific user
- **global:** Memory shared across all users and workflows (organizational knowledge)

**Privacy Implications:**
- **workflow:** High privacy - isolated sessions
- **user:** Medium privacy - user-specific memory
- **global:** Low privacy - shared knowledge base

## 🔧 SHARING_STRATEGY
**Type:** string  
**Default:** all  
**Options:** all, sequential, selective  
**Description:** How much context to share between agents  
**Example:** `sharing_strategy: 'all'`

**Details:**
- **all:** Each agent sees complete session history
- **sequential:** Each agent sees only immediately previous agent's work
- **selective:** Agents see only relevant context based on criteria

**Context Impact:**
- **all:** Maximum context, maximum tokens
- **sequential:** Limited context, controlled tokens
- **selective:** Smart context, optimized tokens

## 🔧 PERSIST_SESSION
**Type:** boolean  
**Default:** true  
**Description:** Whether to save session data to persistent storage (BigQuery)  
**Impact:** When true, sessions survive restarts and enable analytics  
**Example:** `persist_session: true`  
**Storage Location:** Configured memory backend (BigQuery in your case)

**Benefits:**
- Session recovery
- Analytics
- Audit trails
- Long-term memory

## 🔧 SESSION_TIMEOUT
**Type:** integer  
**Default:** 3600  
**Unit:** seconds  
**Description:** How long sessions remain active without new activity  
**Example:** `session_timeout: 7200  # 2 hours`  
**Cleanup Behavior:** Expired sessions are marked inactive but may be preserved for analytics

**Recommendations:**
- **Interactive workflows:** 1800-3600 seconds (30min-1hour)
- **Batch processing:** 7200-14400 seconds (2-4 hours)
- **Long research:** 28800+ seconds (8+ hours)

## 🔧 AUTO_CLEANUP
**Type:** boolean  
**Default:** false  
**Description:** Automatically remove expired sessions from storage  
**Example:** `auto_cleanup: true`  
**⚠️ Caution:** May delete valuable conversation data - consider retention policies  
**Alternatives:** Use retention policies in BigQuery instead for better control

## 🔧 ENABLE_ANALYTICS
**Type:** boolean  
**Default:** false  
**Description:** Enable session performance analytics and metrics  
**Example:** `enable_analytics: true`  
**Storage:** Analytics stored in BigQuery for querying

**Metrics Collected:**
- Session duration
- Agent collaboration patterns
- Context growth rates
- Token usage per agent
- Workflow success rates

## 🔧 ENABLE_SEARCH
**Type:** boolean  
**Default:** false  
**Description:** Enable semantic search across session history  
**Example:** `enable_search: true`  
**Requirements:** Vector embeddings backend (ChromaDB, Qdrant, etc.)

**Capabilities:**
- Search conversation history
- Find similar sessions
- Context-aware retrieval
- Semantic similarity matching

## 🔧 CONTEXT_WINDOW_MANAGEMENT
**Type:** string  
**Default:** auto  
**Options:** auto, manual, smart_truncate, summarize  
**Description:** How to handle growing context windows  
**Example:** `context_window_management: 'auto'`  
**Critical For:** Long sessions with many agents to prevent token overflow

**Details:**
- **auto:** Automatically manage context based on model limits
- **manual:** No automatic management - rely on explicit control
- **smart_truncate:** Remove least relevant context when approaching limits
- **summarize:** Summarize older context to compress token usage

## 🔧 Context Window Management Strategies

### 📋 AUTO STRATEGY
**Description:** LangSwarm automatically manages context

**Behavior:**
- Monitor token usage per model
- Truncate oldest messages when approaching limits
- Preserve critical context (user input, recent responses)
- Adjust based on model context window (4K, 8K, 32K, 128K)

**Pros:** Zero configuration, Model-aware, Safe defaults  
**Cons:** May lose important context, Generic truncation

### 📋 MANUAL STRATEGY
**Description:** Full manual control over context

**Behavior:**
- No automatic truncation
- Session can grow until model limits
- Requires explicit context management in workflow
- Risk of context overflow errors

**Pros:** Complete control, No unexpected context loss  
**Cons:** Risk of errors, Requires expertise, Manual management

### 📋 SMART_TRUNCATE STRATEGY
**Description:** Intelligent context pruning

**Behavior:**
- Analyze context relevance
- Remove least important messages
- Preserve agent reasoning chains
- Keep user intent and recent context

**Pros:** Preserves important context, Intelligent decisions  
**Cons:** More complex, May still lose context

### 📋 SUMMARIZE STRATEGY
**Description:** Compress context through summarization

**Behavior:**
- Summarize older conversation segments
- Replace detailed history with summaries
- Preserve recent full context
- Use AI to create summaries

**Pros:** Preserves information, Compact representation  
**Cons:** Loss of detail, Summarization costs, Potential information loss

## 🎯 Session Scope Examples

### 📂 WORKFLOW SCOPE
**Config:** `scope: 'workflow'`  
**Description:** Memory isolated to single workflow execution  
**Example:** Customer support ticket processing

**Memory Boundaries:**
- Workflow A Session 1: Isolated memory
- Workflow A Session 2: Different memory (new execution)
- Workflow B Session 1: Completely separate memory

**Best For:** One-time tasks, Stateless processing, High privacy needs

### 📂 USER SCOPE
**Config:** `scope: 'user'`  
**Description:** Memory shared across all workflows for a user  
**Example:** Personal AI assistant

**Memory Boundaries:**
- User Alice Workflow A: Alice's memory
- User Alice Workflow B: Same Alice's memory (accumulated)
- User Bob Workflow A: Bob's separate memory

**Best For:** Personal assistants, Customer relationships, Learning systems

### 📂 GLOBAL SCOPE
**Config:** `scope: 'global'`  
**Description:** Memory shared across all users and workflows  
**Example:** Company knowledge base

**Memory Boundaries:**
- Any user, any workflow: Shared organizational memory
- All conversations contribute to collective knowledge
- Cross-user learning and information sharing

**Best For:** Knowledge bases, Organizational learning, Collective intelligence

## 💡 Configuration Recommendations

### 🎯 CUSTOMER SUPPORT WORKFLOWS
**Recommended Configuration:**
```yaml
unified_memory: true
scope: user
sharing_strategy: all
context_window_management: smart_truncate
session_timeout: 3600
enable_analytics: true
```
**Reasoning:** Preserve customer context across interactions, smart context management

### 🎯 DOCUMENT PROCESSING PIPELINES
**Recommended Configuration:**
```yaml
unified_memory: true
scope: workflow
sharing_strategy: sequential
context_window_management: summarize
session_timeout: 7200
enable_analytics: false
```
**Reasoning:** Sequential processing with summarization to handle large documents

### 🎯 RESEARCH AND ANALYSIS
**Recommended Configuration:**
```yaml
unified_memory: true
scope: workflow
sharing_strategy: all
context_window_management: auto
session_timeout: 14400
enable_search: true
```
**Reasoning:** Complete context sharing for thorough analysis, extended timeouts

### 🎯 HIGH PRIVACY REQUIREMENTS
**Recommended Configuration:**
```yaml
unified_memory: false
scope: workflow
persist_session: false
auto_cleanup: true
session_timeout: 1800
```
**Reasoning:** Minimal context sharing, no persistence, quick cleanup

## 🎯 Key Takeaways

- **unified_memory: true** = agents share conversation context
- **scope:** Controls the boundary of memory sharing
- **sharing_strategy:** Controls how much context each agent sees
- **context_window_management:** Critical for preventing token overflow
- **session_timeout:** Balance between persistence and resource usage
- **enable_analytics:** Essential for monitoring session performance

## ⚠️ Critical Considerations

- **Context expansion can lead to exponential token costs**
- **Choose sharing_strategy carefully based on your use case**
- **Monitor context growth with enable_analytics: true**
- **Use context_window_management to prevent model limit errors**
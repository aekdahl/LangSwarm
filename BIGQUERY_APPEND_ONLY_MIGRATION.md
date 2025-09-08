# BigQuery Append-Only Migration Guide

## 🚨 IMPORTANT: Two Different BigQuery Configurations

**There are TWO separate BigQuery features in LangSwarm that store DIFFERENT data:**

| Feature | What It Stores | When To Use | Table Structure |
|---------|---------------|-------------|-----------------|
| **Memory Backend** (EXISTING) | Agent conversation history, messages, context | For AI memory across conversations | `agent_conversations` table with message content |
| **Session Storage** (NEW) | Session metadata, user info, session lifecycle | For session management, analytics, user tracking | `session_events` table with session metadata |

### 🤔 Which One Do You Need?

- **Memory Backend**: "I want my AI agent to remember past conversations and context"
- **Session Storage**: "I want to track user sessions, manage session lifecycle, and avoid BigQuery update conflicts"

**Most users only need Memory Backend** - Session Storage is for advanced session management scenarios.

### 📝 Existing BigQuery Memory Configuration (Still Works)

This is the **original** way BigQuery was used in LangSwarm for conversation memory:

```yaml
# This is EXISTING and works as before - NO CHANGES NEEDED
# Stores: agent conversations, message history, AI context
agents:
  - id: "your_agent"
    model: "gpt-4o"
    memory:
      backend: "bigquery"  # ← This is the ORIGINAL BigQuery feature
      settings:
        project_id: "your-project"
        dataset_id: "langswarm_memory"      # Different from session storage!
        table_id: "agent_conversations"     # Stores MESSAGE CONTENT
```

**This creates a table like:**
```sql
agent_conversations:
- agent_id (string)
- session_id (string) 
- user_message (string)
- agent_response (string)
- timestamp (timestamp)
- metadata (json)
```

### ⭐ NEW: BigQuery Session Storage (For Session Management)

This is a **NEW feature** I added for append-only session management:

```python
# NEW FEATURE - Use only if you want BigQuery for session management
# Stores: session metadata, user info, session lifecycle events
from langswarm.core.session.storage import SessionStorageFactory
from langswarm.core.session.manager import LangSwarmSessionManager

# Create append-only BigQuery session storage
storage = SessionStorageFactory.create_storage(
    storage_type="bigquery",
    project_id="your-project-id",
    dataset_id="langswarm_sessions",  # Different from memory dataset!
    table_id="session_events"         # Stores SESSION METADATA
)

# Use with session manager
session_manager = LangSwarmSessionManager(storage=storage)
```

**This creates a table like:**
```sql
session_events:
- event_id (string)
- session_id (string)
- user_id (string)
- event_type (string)  # 'session_created', 'session_updated', etc.
- event_timestamp (timestamp)
- session_data (json)  # Session metadata, NOT message content
- metadata (json)
```

# Now all operations are append-only:
session = session_manager.create_session(
    user_id="user123",
    provider="openai", 
    model="gpt-4o"
)

session_manager.add_message(session.session_id, role="user", content="Hello")
session_manager.add_message(session.session_id, role="assistant", content="Hi there!")
```

### Option 2: Replace Your Custom BigQuery Code

If you have custom BigQuery session management code, replace UPDATE operations with INSERT operations:

```python
# ❌ OLD WAY (causes streaming buffer warnings):
def update_session(session_id, new_data):
    query = f"""
    UPDATE `{project}.{dataset}.{table}` 
    SET data = @new_data, updated_at = CURRENT_TIMESTAMP()
    WHERE session_id = @session_id
    """
    # This causes "Cannot update session in streaming buffer" warnings

# ✅ NEW WAY (append-only):
def update_session(session_id, new_data):
    # Insert a new event instead of updating
    event = {
        "event_id": str(uuid4()),
        "session_id": session_id,
        "event_type": "session_updated",
        "event_timestamp": datetime.utcnow().isoformat(),
        "event_data": new_data
    }
    
    # Always INSERT, never UPDATE
    client.insert_rows_json(table_ref, [event])

# To get latest state, query the most recent event:
def get_latest_session_state(session_id):
    query = f"""
    SELECT event_data
    FROM `{project}.{dataset}.{table}`
    WHERE session_id = @session_id
    ORDER BY event_timestamp DESC
    LIMIT 1
    """
    # Returns the latest state without any streaming buffer conflicts
```

### Option 3: Check Your Application Code

Search your codebase for BigQuery UPDATE statements:

```bash
# Find all BigQuery UPDATE operations that need to be converted
grep -r "UPDATE.*session" your_app_directory/
grep -r "client.query.*UPDATE" your_app_directory/
```

Replace any UPDATE operations on session tables with INSERT operations.

## 🎯 Is This On By Default?

**❌ NO - This is a completely NEW feature:**

- **Existing BigQuery Memory**: Still works exactly as before (no changes needed)
- **NEW BigQuery Session Storage**: Only activates if you explicitly configure it
- **Default Session Storage**: Remains SQLite (not BigQuery)

**The warnings you're seeing are likely from custom application code, not from LangSwarm core.**

## 🔧 LangSwarm BigQuery Memory Adapter Status

**✅ GOOD NEWS: LangSwarm's built-in BigQuery memory adapter already uses append-only patterns!**

The `BigQueryAdapter` in `langswarm/memory/adapters/_langswarm/bigquery/main.py` correctly uses:
- `client.insert_rows_json()` for adding documents (append-only) ✅
- No UPDATE operations on memory data ✅
- Proper BigQuery best practices ✅

**If you're seeing BigQuery warnings, they're coming from:**
1. **Custom application code** that uses UPDATE statements
2. **Third-party libraries** that aren't BigQuery-optimized
3. **Legacy session management code** that needs updating

## ✅ Verification

After switching, you should no longer see:
```
WARNING:app.core.bigquery_session_manager:Cannot update session ... in streaming buffer
```

Instead, all operations will be fast INSERT operations that don't conflict with BigQuery's streaming buffer.

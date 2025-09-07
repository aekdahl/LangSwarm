# SQL Database Tool Template

Quick reference for using the SQL Database MCP tool with secure querying and intent-based natural language support.

## 🎯 **Tool Purpose**
Securely query SQL databases (SQLite, PostgreSQL, MySQL) with configurable restrictions and natural language intent parsing.

## ⚡ **Quick Usage**

### **Intent-Based Querying (Recommended)**
```python
# Natural language queries
{
  "tool": "sql_database",
  "intent": "show me all active users from the last month",
  "context": "user management dashboard"
}

{
  "tool": "sql_database", 
  "intent": "find customers with high order values",
  "constraints": {"total_orders": "> 1000"}
}
```

### **Direct SQL Queries**
```python
# Basic query
{
  "tool": "sql_database",
  "method": "execute_query",
  "params": {
    "query": "SELECT name, email FROM users WHERE active = 1 LIMIT 10"
  }
}

# Parameterized query (safer)
{
  "tool": "sql_database",
  "method": "execute_query", 
  "params": {
    "query": "SELECT * FROM orders WHERE user_id = %(user_id)s",
    "parameters": {"user_id": 123}
  }
}
```

### **Database Information**
```python
# Get schema info
{
  "tool": "sql_database",
  "method": "get_database_info",
  "params": {"include_schema": true}
}
```

## 🛡️ **Security Features**

- **Operation Whitelisting**: Only allowed SQL operations execute
- **Keyword Blocking**: Dangerous operations (DROP, DELETE) blocked
- **Row Limits**: Prevents large data exports
- **Query Validation**: SQL injection protection
- **Table Restrictions**: Limit access to specific tables

## 📋 **Parameters**

### **execute_query**
- `query` (required): SQL query string
- `parameters` (optional): Parameters for prepared statements
- `limit` (optional): Max rows to return
- `explain_only` (optional): Only show query plan

### **intent_query**
- `intent` (required): Natural language description
- `context` (optional): Additional context for query generation
- `constraints` (optional): Additional filters/conditions

### **get_database_info**
- `include_schema` (optional): Include table column details
- `table_pattern` (optional): Filter tables by name pattern

## ⚙️ **Configuration Example**

```yaml
tools:
  demo_database:
    type: mcpsql_database
    config:
      db_type: "sqlite"
      db_path: "/uploads/demo_123/database.sqlite"
      allowed_operations: ["SELECT", "INSERT", "UPDATE"]
      max_rows: 1000
      enable_intent_parsing: true
      blocked_keywords: ["DROP", "DELETE", "TRUNCATE"]
```

## 🔧 **Tool Call Patterns**

### **When to Use Intent-Based**
- ✅ Exploratory data analysis
- ✅ Business user queries  
- ✅ Complex multi-table queries
- ✅ When you want query optimization

### **When to Use Direct SQL**
- ✅ Specific known queries
- ✅ Performance-critical operations
- ✅ Complex joins and subqueries
- ✅ When you need exact control

### **Database Info Usage**
- ✅ Schema exploration
- ✅ Table discovery
- ✅ Column information
- ✅ Database health checks

## 🎨 **Response Examples**

### **Successful Query**
```json
{
  "success": true,
  "query": "SELECT name, email FROM users LIMIT 5",
  "results": [
    {"name": "John Doe", "email": "john@example.com"}
  ],
  "row_count": 1,
  "columns": ["name", "email"],
  "execution_time_ms": 15.3
}
```

### **Intent Response**
```json
{
  "success": true,
  "intent": "show active users",
  "generated_query": "SELECT * FROM users WHERE status = 'active'",
  "results": [...],
  "explanation": "Selecting active users from users table"
}
```

### **Security Error**
```json
{
  "success": false,
  "error": "Query validation failed: Blocked keyword 'DROP' found in query",
  "error_type": "parameter_validation"
}
```

## 🚨 **Common Issues**

### **Wrong Parameter Names**
```python
# ❌ Wrong
{"sql": "SELECT * FROM users"}

# ✅ Correct  
{"query": "SELECT * FROM users"}
```

### **Blocked Operations**
```python
# ❌ Blocked (if not in allowed_operations)
{"query": "DROP TABLE users"}

# ✅ Safe
{"query": "SELECT * FROM users"}
```

### **Large Result Sets**
```python
# ❌ Might hit row limits
{"query": "SELECT * FROM large_table"}

# ✅ Limited
{"query": "SELECT * FROM large_table LIMIT 100"}
```

## 🔗 **Integration Tips**

1. **Use with workflows** for complex data analysis
2. **Combine with memory** to learn query patterns
3. **Enable logging** for audit and debugging
4. **Start with intent-based** for exploration
5. **Use explain_only** for query optimization

## 📚 **See Also**

- [Full Documentation](readme.md) - Comprehensive guide
- [Security Guide](#security-features) - Security best practices
- [Configuration Reference](#configuration-example) - All config options

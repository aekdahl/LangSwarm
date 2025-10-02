# SQL Database MCP Tool

A secure, intent-based SQL database querying tool with configurable restrictions and multi-database support.

## 🔥 **Key Features**

### **🛡️ Security First**
- **Query Validation**: Automatic blocking of dangerous operations (DROP, DELETE, TRUNCATE)
- **Operation Whitelisting**: Configure exactly which SQL operations are allowed
- **Parameter Sanitization**: Protection against SQL injection attacks
- **Row Limits**: Prevent accidental large data exports
- **Table Restrictions**: Limit access to specific tables

### **🧠 Intent-Based Querying**
- **Natural Language**: Write queries in plain English
- **Automatic SQL Generation**: AI-powered query construction
- **Context Awareness**: Understands database schema and relationships
- **Safety Validation**: Generated queries go through same security checks

### **🔗 Multi-Database Support**
- **SQLite**: ✅ Built-in support
- **PostgreSQL**: ✅ With psycopg2-binary
- **MySQL**: ✅ With mysql-connector-python
- **Oracle**: 🔜 With cx_Oracle
- **SQL Server**: 🔜 With pyodbc

## 📦 **Installation**

### **Basic (SQLite only)**
```bash
# SQLite support is built-in, no additional dependencies needed
```

### **PostgreSQL Support**
```bash
pip install psycopg2-binary
```

### **MySQL Support** 
```bash
pip install mysql-connector-python
```

## ⚙️ **Configuration**

### **Basic SQLite Configuration**
```yaml
tools:
  demo_database:
    type: mcpsql_database
    config:
      db_type: "sqlite"
      db_path: "/uploads/demo_123/database.sqlite"
      allowed_operations: ["SELECT", "INSERT", "UPDATE"]
      max_rows: 500
      enable_intent_parsing: true
```

### **PostgreSQL Configuration**
```yaml
tools:
  production_db:
    type: mcpsql_database
    config:
      db_type: "postgresql"
      host: "localhost"
      port: 5432
      database: "myapp_production"
      user: "readonly_user"
      password: "${DB_PASSWORD}"  # Use environment variables
      allowed_operations: ["SELECT"]
      max_rows: 1000
      allowed_tables: ["users", "orders", "products"]
```

### **MySQL Configuration**
```yaml
tools:
  analytics_db:
    type: mcpsql_database
    config:
      db_type: "mysql"
      host: "analytics.company.com"
      port: 3306
      database: "analytics"
      user: "analyst"
      password: "${MYSQL_PASSWORD}"
      allowed_operations: ["SELECT"]
      max_rows: 10000
      enable_query_logging: true
```

## 🚀 **Usage Examples**

### **1. Intent-Based Querying (Recommended)**

**Natural Language Query:**
```python
# Simple intent
result = tool.run({
    "intent": "show me all active users from the last month"
})

# With context and constraints  
result = tool.run({
    "intent": "find high-value customers",
    "context": "sales analysis for Q4 report",
    "constraints": {
        "status": "active",
        "total_orders": ">= 5"
    }
})
```

**YAML Workflow:**
```yaml
agents:
  data_analyst:
    model: gpt-4
    tools: [demo_database]

workflows:
  - name: sales_analysis
    steps:
      - tool: demo_database
        intent: "get total sales by month for this year"
        context: "quarterly business review"
```

### **2. Direct SQL Queries**

**Basic Query:**
```python
result = tool.run({
    "query": "SELECT name, email FROM users WHERE created_at > '2024-01-01' LIMIT 10"
})
```

**Parameterized Query:**
```python
result = tool.run({
    "query": "SELECT * FROM orders WHERE user_id = %(user_id)s AND status = %(status)s",
    "parameters": {
        "user_id": 123,
        "status": "completed"
    }
})
```

### **3. Database Information**

**Get Schema Information:**
```python
result = tool.run({
    "method": "get_database_info",
    "params": {
        "include_schema": True,
        "table_pattern": "user"  # Filter tables containing "user"
    }
})
```

### **4. Query Planning (Explain Only)**

**Analyze Query Performance:**
```python
result = tool.run({
    "query": "SELECT * FROM large_table WHERE complex_condition = 'value'",
    "explain_only": True
})
```

## 🛡️ **Security Configuration**

### **Operation Restrictions**
```yaml
config:
  allowed_operations: 
    - "SELECT"      # Safe read operations
    - "INSERT"      # Allow data insertion
    - "UPDATE"      # Allow data updates
    # Blocked: DROP, DELETE, TRUNCATE, ALTER, CREATE
```

### **Table Access Control**
```yaml
config:
  allowed_tables: 
    - "users"
    - "orders" 
    - "products"
  # Only these tables can be queried
```

### **Additional Security**
```yaml
config:
  blocked_keywords:
    - "DROP"
    - "TRUNCATE"
    - "DELETE"
    - "xp_cmdshell"    # SQL Server specific
    - "LOAD_FILE"      # MySQL specific
  
  max_rows: 1000           # Prevent large exports
  timeout_seconds: 30      # Query timeout
  enable_explain_only: false  # Set true for query analysis only
```

## 📊 **Response Formats**

### **Query Results**
```json
{
  "success": true,
  "query": "SELECT name, email FROM users LIMIT 5",
  "results": [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
  ],
  "row_count": 2,
  "columns": ["name", "email"],
  "execution_time_ms": 15.3,
  "warnings": ["Results limited to 1000 rows"]
}
```

### **Intent-Based Results**
```json
{
  "success": true,
  "intent": "show me all active users",
  "generated_query": "SELECT * FROM users WHERE status = 'active' LIMIT 1000",
  "results": [...],
  "row_count": 45,
  "explanation": "Selecting all columns from users table with active status condition",
  "execution_time_ms": 23.7
}
```

### **Database Information**
```json
{
  "success": true,
  "database_type": "sqlite",
  "database_name": "/uploads/demo_123/database.sqlite",
  "tables": [
    {
      "name": "users",
      "row_count": 1500,
      "columns": [
        {"name": "id", "type": "INTEGER", "nullable": false, "primary_key": true},
        {"name": "name", "type": "TEXT", "nullable": false},
        {"name": "email", "type": "TEXT", "nullable": false}
      ]
    }
  ],
  "total_tables": 1
}
```

## 🔧 **Advanced Features**

### **Query Logging**
```yaml
config:
  enable_query_logging: true
  # Logs all executed queries for audit purposes
```

### **Intent Context Enhancement**
```python
# Enhanced intent with business context
result = tool.run({
    "intent": "customers who haven't ordered recently",
    "context": "retention marketing campaign",
    "constraints": {
        "last_order_days": "> 30",
        "total_lifetime_value": "> 100"
    }
})
```

### **Multiple Database Types in Same Config**
```yaml
tools:
  main_db:
    type: mcpsql_database
    config:
      db_type: "postgresql"
      # ... postgres config
  
  analytics_db:
    type: mcpsql_database  
    config:
      db_type: "mysql"
      # ... mysql config
      
  local_cache:
    type: mcpsql_database
    config:
      db_type: "sqlite"
      # ... sqlite config
```

## ⚠️ **Error Handling**

### **Security Violations**
```json
{
  "success": false,
  "error": "Query validation failed: Blocked keyword 'DROP' found in query",
  "error_type": "parameter_validation",
  "tool_name": "sql_database",
  "suggestion": "Remove dangerous operations and use only allowed operations: SELECT, INSERT, UPDATE"
}
```

### **Parameter Validation**
```json
{
  "success": false,
  "error": "Invalid parameter 'sql': Expected query (SQL string), got str: 'SELECT * FROM users'",
  "error_type": "parameter_validation", 
  "suggestion": "Please provide 'sql' as query (SQL string)"
}
```

### **Connection Issues**
```json
{
  "success": false,
  "error": "Failed to connect to database",
  "error_type": "connection",
  "suggestion": "Check database credentials and network connectivity"
}
```

## 🧪 **Testing**

### **Test Database Connection**
```python
# Test basic connectivity
result = tool.run({
    "method": "get_database_info",
    "params": {"include_schema": False}
})

if result["success"]:
    print(f"Connected to {result['database_type']} database")
    print(f"Found {result['total_tables']} tables")
```

### **Validate Security**
```python
# This should be blocked
result = tool.run({
    "query": "DROP TABLE users"  
})
assert not result["success"]
assert "Blocked keyword" in result["error"]
```

### **Test Intent Parsing**
```python
# Test natural language understanding
result = tool.run({
    "intent": "count total users"
})
assert "COUNT" in result["generated_query"].upper()
assert result["success"]
```

## 🔗 **Integration Patterns**

### **With LangSwarm Workflows**
```yaml
workflows:
  customer_analysis:
    description: "Analyze customer behavior and generate insights"
    steps:
      - id: get_customer_data
        tool: demo_database
        intent: "get customer purchase patterns for the last 6 months"
        output_to: customer_data
        
      - id: analyze_trends
        agent: data_analyst
        input: |
          Based on this customer data: ${context.step_outputs.get_customer_data}
          Identify the top 3 trends and recommend actions.
```

### **With Memory Integration**
```yaml
agents:
  sql_analyst:
    model: gpt-4
    tools: [demo_database]
    memory:
      adapter: langchain
      config:
        # Remember successful query patterns
        store_successful_queries: true
        learn_from_intent_mappings: true
```

## 🎯 **Best Practices**

### **Security**
1. **Always use read-only users** for production databases
2. **Limit allowed operations** to minimum required
3. **Use environment variables** for credentials
4. **Enable query logging** for audit trails
5. **Set appropriate row limits** to prevent data dumps

### **Performance**
1. **Use intent-based queries** for better optimization
2. **Add query timeouts** to prevent long-running queries
3. **Monitor execution times** and optimize slow queries
4. **Use EXPLAIN** to analyze query plans

### **Intent Design**
1. **Be specific** in intent descriptions
2. **Provide context** for better query generation
3. **Use constraints** to add conditions
4. **Test generated queries** before production use

## 🆕 **What's New**

This SQL Database tool includes all the latest LangSwarm improvements:

- ✅ **Standardized Error Handling**: Consistent error responses across all tools
- ✅ **Intent-Based Architecture**: Natural language query generation
- ✅ **Security First Design**: Multiple layers of query validation
- ✅ **Multi-Database Support**: SQLite, PostgreSQL, MySQL with same interface
- ✅ **Configuration Flexibility**: Granular control over permissions and behavior

## 📄 **License**

This tool is part of the LangSwarm ecosystem and follows the same MIT license.

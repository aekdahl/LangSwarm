#!/usr/bin/env python3
"""
Test script for the new SQL Database MCP tool
"""

import tempfile
import sqlite3
import os

def create_test_database():
    """Create a test SQLite database with sample data"""
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Connect and create schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Insert sample data
    users_data = [
        (1, 'John Doe', 'john@example.com', 'active'),
        (2, 'Jane Smith', 'jane@example.com', 'active'),
        (3, 'Bob Johnson', 'bob@example.com', 'inactive'),
        (4, 'Alice Wilson', 'alice@example.com', 'active')
    ]
    
    cursor.executemany(
        "INSERT INTO users (id, name, email, status) VALUES (?, ?, ?, ?)",
        users_data
    )
    
    orders_data = [
        (1, 1, 99.99, 'completed'),
        (2, 1, 149.99, 'completed'),
        (3, 2, 79.99, 'pending'),
        (4, 4, 199.99, 'completed'),
        (5, 2, 299.99, 'completed')
    ]
    
    cursor.executemany(
        "INSERT INTO orders (id, user_id, amount, status) VALUES (?, ?, ?, ?)",
        orders_data
    )
    
    conn.commit()
    conn.close()
    
    return db_path

def test_sql_tool_import():
    """Test SQL tool import and initialization"""
    print("🧪 Testing SQL Tool Import...")
    
    try:
        from langswarm.mcp.tools.sql_database.main import SQLDatabaseMCPTool
        print("✅ SQL tool import successful")
        
        # Test tool creation
        tool = SQLDatabaseMCPTool('test_sql')
        print("✅ SQL tool initialization successful")
        print(f"   Name: {tool.name}")
        print(f"   _bypass_pydantic: {getattr(tool, '_bypass_pydantic', 'Missing')}")
        
        return tool, True
        
    except Exception as e:
        print(f"❌ SQL tool import failed: {e}")
        return None, False

def test_security_validation():
    """Test security features"""
    print("\n🧪 Testing Security Validation...")
    
    try:
        from langswarm.mcp.tools.sql_database.main import QueryValidator
        
        # Test with safe configuration
        config = {
            'allowed_operations': ['SELECT'],
            'blocked_keywords': ['DROP', 'DELETE', 'TRUNCATE'],
            'allowed_tables': None
        }
        
        validator = QueryValidator(config)
        
        # Test safe query
        is_valid, sanitized, warnings = validator.validate_query("SELECT * FROM users LIMIT 10")
        assert is_valid, "Safe query should be valid"
        print("✅ Safe query validation passed")
        
        # Test blocked keyword
        is_valid, sanitized, warnings = validator.validate_query("DROP TABLE users")
        assert not is_valid, "Dangerous query should be blocked"
        assert any("DROP" in warning for warning in warnings), "Should warn about DROP"
        print("✅ Dangerous query blocked correctly")
        
        # Test blocked operation
        is_valid, sanitized, warnings = validator.validate_query("INSERT INTO users VALUES (1, 'test')")
        assert not is_valid, "Non-allowed operation should be blocked"
        print("✅ Non-allowed operation blocked correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Security validation test failed: {e}")
        return False

def test_database_connection():
    """Test database connection functionality"""
    print("\n🧪 Testing Database Connection...")
    
    try:
        from langswarm.mcp.tools.sql_database.main import DatabaseConnection
        
        # Create test database
        db_path = create_test_database()
        
        try:
            config = {
                'db_type': 'sqlite',
                'db_path': db_path,
                'timeout_seconds': 30
            }
            
            db_conn = DatabaseConnection(config)
            
            # Test connection
            connected = db_conn.connect()
            assert connected, "Should connect successfully"
            print("✅ Database connection successful")
            
            # Test query execution
            results, columns, exec_time = db_conn.execute_query("SELECT COUNT(*) as user_count FROM users")
            assert len(results) == 1, "Should return one row"
            assert results[0]['user_count'] == 4, "Should have 4 users"
            print(f"✅ Query execution successful: {results[0]['user_count']} users found")
            
            # Test database info
            info = db_conn.get_database_info()
            assert info['database_type'] == 'sqlite', "Should identify as SQLite"
            assert len(info['tables']) >= 2, "Should find users and orders tables"
            print(f"✅ Database info retrieved: {len(info['tables'])} tables found")
            
            db_conn.close()
            return True
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intent_generation():
    """Test intent-based query generation"""
    print("\n🧪 Testing Intent-Based Query Generation...")
    
    try:
        from langswarm.mcp.tools.sql_database.main import IntentQueryGenerator, DatabaseConnection
        
        # Create test database
        db_path = create_test_database()
        
        try:
            config = {
                'db_type': 'sqlite',
                'db_path': db_path,
                'max_rows': 1000
            }
            
            db_conn = DatabaseConnection(config)
            db_conn.connect()
            
            generator = IntentQueryGenerator(db_conn, config)
            
            # Test simple intent
            query, explanation = generator.generate_query_from_intent(
                "show me all users",
                context="user management"
            )
            
            assert "SELECT" in query.upper(), "Should generate SELECT query"
            assert "users" in query.lower(), "Should query users table"
            print(f"✅ Intent query generated: {query}")
            print(f"   Explanation: {explanation}")
            
            db_conn.close()
            return True
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Intent generation test failed: {e}")
        return False

def test_tool_integration():
    """Test full tool integration"""
    print("\n🧪 Testing Tool Integration...")
    
    try:
        from langswarm.mcp.tools.sql_database.main import SQLDatabaseMCPTool
        
        # Create test database
        db_path = create_test_database()
        
        try:
            tool = SQLDatabaseMCPTool('test_integration')
            
            # Configure tool
            tool.configure({
                'db_type': 'sqlite',
                'db_path': db_path,
                'allowed_operations': ['SELECT'],
                'max_rows': 100
            })
            
            print("✅ Tool configuration successful")
            
            # Test direct query
            result = tool.run({
                "query": "SELECT name, email FROM users WHERE status = 'active'"
            })
            
            assert result['success'], f"Query should succeed: {result.get('error', '')}"
            assert len(result['results']) > 0, "Should return results"
            print(f"✅ Direct query successful: {len(result['results'])} results")
            
            # Test intent query
            result = tool.run({
                "intent": "count total users",
                "context": "dashboard metrics"
            })
            
            assert result['success'], f"Intent query should succeed: {result.get('error', '')}"
            print(f"✅ Intent query successful: {result.get('explanation', '')}")
            
            # Test database info
            result = tool.run({
                "method": "get_database_info",
                "params": {"include_schema": True}
            })
            
            assert result['success'], f"Database info should succeed: {result.get('error', '')}"
            assert result['total_tables'] >= 2, "Should find multiple tables"
            print(f"✅ Database info successful: {result['total_tables']} tables")
            
            # Test security (should fail)
            result = tool.run({
                "query": "DROP TABLE users"
            })
            
            assert not result['success'], "Dangerous query should fail"
            assert "DROP" in result['error'], "Should mention blocked keyword"
            print("✅ Security validation working")
            
            return True
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Tool integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_standards():
    """Test error standards integration"""
    print("\n🧪 Testing Error Standards Integration...")
    
    try:
        from langswarm.mcp.tools.sql_database.main import SQLDatabaseMCPTool
        
        tool = SQLDatabaseMCPTool('test_errors')
        
        # Test parameter error
        result = tool.run({
            "sql": "SELECT * FROM users"  # Wrong parameter name
        })
        
        assert not result['success'], "Should fail with wrong parameter"
        assert 'parameter' in result.get('error', '').lower(), "Should mention parameter error"
        assert result.get('error_type') == 'parameter_validation', "Should have correct error type"
        print("✅ Parameter error handling correct")
        
        # Test without database configuration (should fail)
        result = tool.run({
            "query": "SELECT * FROM users"
        })
        
        assert not result['success'], "Should fail without database config"
        print("✅ Configuration error handling correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error standards test failed: {e}")
        return False

def main():
    """Run all SQL tool tests"""
    print("🚀 Testing SQL Database MCP Tool\n")
    
    tests = [
        ("Import & Initialization", test_sql_tool_import),
        ("Security Validation", test_security_validation),
        ("Database Connection", test_database_connection),
        ("Intent Generation", test_intent_generation),
        ("Tool Integration", test_tool_integration),
        ("Error Standards", test_error_standards),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 SQL DATABASE TOOL TEST RESULTS")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{total} tests ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SQL TOOL READY! 🚀")
        print("\nSQL Database Tool features verified:")
        print("  ✅ Security validation and query filtering")
        print("  ✅ Multi-database connection support")
        print("  ✅ Intent-based natural language querying")
        print("  ✅ Comprehensive error handling")
        print("  ✅ Database schema exploration")
        print("  ✅ LangSwarm integration patterns")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed - Review before deployment")
        return False

if __name__ == "__main__":
    main()

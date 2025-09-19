#!/usr/bin/env python3
"""
Setup Test Database for SQL Database MCP Tool Debug
===================================================

This script creates a SQLite database with sample data for testing the SQL Database MCP tool.
"""

import sqlite3
import os
from pathlib import Path

def setup_test_database():
    """Create and populate the test SQLite database"""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    db_path = script_dir / "test_database.db"
    sql_path = script_dir / "create_test_database.sql"
    
    print(f"Setting up test database at: {db_path}")
    
    # Remove existing database if it exists
    if db_path.exists():
        os.remove(db_path)
        print("Removed existing database")
    
    # Create new database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Read and execute the SQL file
        with open(sql_path, 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ Database created successfully!")
        
        # Verify the setup by checking table counts
        tables = ['users', 'orders', 'products']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} records")
        
        # Show available views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        if views:
            print(f"   - Views: {', '.join(views)}")
        
        print(f"\nDatabase ready at: {db_path}")
        print("You can now run the SQL Database debug workflow!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    setup_test_database()

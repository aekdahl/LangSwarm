# SQL Database Tool

## Description

Intelligent SQL interface with natural language query understanding for data analysis, reporting, and business intelligence.

## Instructions

This tool provides SQL database operations with two calling approaches:

### Intent-Based Calling (Natural Language Queries)

Use **`sql_database`** with natural language intent to translate business questions into SQL:

**Parameters:**
- `intent`: The business question or data need
- `context`: Relevant details (tables, metrics, time periods)

**When to use:**
- Business questions: "Show top customers by revenue"
- Analytics queries: "Compare sales month over month"
- Exploratory analysis: "Find inactive users"
- Complex aggregations: "Revenue breakdown by product category and region"

**Examples:**
- "Show customers from Stockholm in last quarter" → intent="get customers from Stockholm who signed up in last 90 days", context="customer analysis, geographic segmentation"
- "Find top products this month" → intent="show best selling products this month", context="sales analysis, product performance"

### Direct Method Calling (SQL Queries)

**`sql_database.execute_query`** - Execute SQL query
- **Parameters:** query (SQL string), params (optional bind parameters)
- **Use when:** You have the exact SQL query to run

**`sql_database.list_tables`** - Show available tables
- **Parameters:** schema (optional)
- **Use when:** Discovering database structure

**`sql_database.describe_table`** - Get table schema
- **Parameters:** table_name
- **Use when:** Understanding table columns and types

**`sql_database.analyze_data`** - Run data analysis
- **Parameters:** table_name, analysis_type (summary/trends/distribution)
- **Use when:** Getting statistical summaries

### Decision Guide

**Use intent-based** when:
- User asks in business terms
- Query requires interpretation
- Complex joins or aggregations needed
- Time-based or comparative analysis

**Use direct methods** when:
- You have the exact SQL
- Simple table operations
- Schema exploration
- Known query patterns

### Safety Features

- Automatic SQL injection prevention
- Read-only mode by default
- Query timeout limits
- Result size caps

### Common Patterns

1. **Customer analysis**: "customers who..." → Intent-based
2. **Simple lookups**: "SELECT * FROM users WHERE id=123" → Direct execute_query
3. **Schema exploration**: "what tables exist?" → list_tables
4. **Revenue reporting**: "revenue by region" → Intent-based

## Brief

SQL database interface with intelligent natural language query processing for business intelligence.
